"""Independent finite symbolic execution for source cost coverage and raw value equivalence.

Uses shared WAT syntax reader, not transform.sequence/envelope. Z3 and the reader
remain in the trusted base; this is not a formal verification of either engine.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import time

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'.tools/encoding-synthesis-python'));import z3 as z
spec=importlib.util.spec_from_file_location('reader',ROOT/'research/connectivity-elimination/prototype.py');w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
S,X=z.BitVecs('secret input_x',32)


def val(x,local):
    op=x[0]
    if op=='i32.const':return z.BitVecVal(int(x[1]),32),1
    if op=='local.get':return local[int(x[1])],1
    if op=='i32.eqz':
        a,c=val(x[1],local);return z.If(a==0,z.BitVecVal(1,32),z.BitVecVal(0,32)),c+1
    a,ca=val(x[1],local);b,cb=val(x[2],local)
    ops={'i32.add':lambda:a+b,'i32.sub':lambda:a-b,'i32.mul':lambda:a*b,'i32.and':lambda:a&b,'i32.or':lambda:a|b,'i32.xor':lambda:a^b,'i32.shl':lambda:a<<(b&31),'i32.shr_u':lambda:z.LShR(a,b&31)}
    cmps={'i32.eq':lambda:a==b,'i32.ne':lambda:a!=b,'i32.lt_u':lambda:z.ULT(a,b),'i32.le_u':lambda:z.ULE(a,b),'i32.gt_u':lambda:z.UGT(a,b),'i32.ge_u':lambda:z.UGE(a,b)}
    if op in ops:return ops[op](),ca+cb+1
    if op in cmps:return z.If(cmps[op](),z.BitVecVal(1,32),z.BitVecVal(0,32)),ca+cb+1
    raise ValueError('unsupported expression '+op)


def paths(binary,skip_start=False):
    w.tool('wasm-validate',[binary]);m=w.parse(w.tool('wasm2wat',[binary,'--fold-exprs','--no-debug-names']))
    if any(n[0] not in ('type','import','func','export') for n in m[1:]):raise ValueError('checker module subset')
    imports=[n for n in m[1:] if n[0]=='import'];fs=[n for n in m[1:] if n[0]=='func'];exports=[n for n in m[1:] if n[0]=='export'];types=[n for n in m[1:] if n[0]=='type']
    if len(imports)!=1 or imports[0][1:3]!=['"env"','"mark"'] or imports[0][3][0]!='func' or len(fs)!=1 or exports!=[['export','"run"',['func','1']]]:raise ValueError('checker function boundary')
    if types[int(imports[0][3][1][1])][1]!=['func',['param','i32','i32']]:raise ValueError('checker marker signature')
    f=next(n for n in m[1:] if n[0]=='func');nlocal=sum(len(n)-1 for n in f[1:] if n[0]=='local');body=[n for n in f[1:] if n[0] not in ('param','result','local','type')]
    if [n for n in f[1:] if n[0]=='param']!=[['param','i32','i32']] or [n for n in f[1:] if n[0]=='result']!=[['result','i32']] or any(v!='i32' for n in f[1:] if n[0]=='local' for v in n[1:]):raise ValueError('checker run signature')
    start=['call','0',['i32.const','-2147483648'],['i32.const','0']]
    if skip_start:
        if not body or body[0]!=start:raise ValueError('checker missing entry marker')
        body=body[1:]
    def execute(body,states):
        for x in body:
            output=[]
            for p in states:
                if x[0]=='if':
                    a,c=val(x[1],p['local'])
                    for side,condition in ((2,a!=0),(3,a==0)):
                        q=copy.deepcopy(p);q['cost']+=c+1;q['pc']=z.And(q['pc'],condition)
                        output.extend(execute(x[side][1:] if len(x)>side else [],[q]))
                    continue
                q=copy.deepcopy(p)
                if x[0]=='call':
                    assert x[1]=='0' and all(k[0]=='i32.const' for k in x[2:]);label=[int(k[1]) for k in x[2:]]
                    if label[0]<0:raise ValueError('checker reserved label')
                    q['cost']+=3;q['events'].append({'label':label,'cost':q['cost']})
                elif x[0]=='local.set':
                    v,c=val(x[2],q['local']);q['local'][int(x[1])]=v;q['cost']+=c+1
                elif x[0]=='nop':q['cost']+=1
                elif x[0]=='drop':v,c=val(x[1],q['local']);q['cost']+=c+1
                else:q['value'],c=val(x,q['local']);q['cost']+=c
                output.append(q)
            states=output
            if len(states)>4096:raise ValueError('checker path limit')
        return states
    return execute(body,[{'local':[S,X]+[z.BitVecVal(0,32)]*nlocal,'pc':z.BoolVal(True),'cost':0,'events':[],'value':None}])


def query(condition):
    solver=z.Solver();solver.set(timeout=5000);solver.add(condition);r=solver.check()
    answer={'status':str(r)}
    if r==z.sat:answer['witness']={str(k):solver.model().eval(k,model_completion=True).as_long() for k in (S,X)}
    if r==z.unknown:answer['reason']=solver.reason_unknown()
    return answer


def check_contract(executions,env):
    checks=[]
    for p in executions:
        index=0;violations=[]
        for e in p['events']:
            node=env['nodes'][index]
            if node['bound']<e['cost']:violations.append('next event undercovered')
            key=','.join(map(str,e['label']))
            if key not in node['next']:violations.append('missing label');break
            index=node['next'][key]
            if env['nodes'][index]['bound']<e['cost']:violations.append('refund below past cost')
        else:
            node=env['nodes'][index]
            if node['bound']<p['cost']:violations.append('return undercovered')
            if node['terminalBound'] is None or node['terminalBound']<p['cost']:violations.append('terminal undercovered')
        if violations:checks.append({'reasons':violations,**query(p['pc'])})
    return checks


def main(source,out):
    out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir();(out/'inputs').mkdir();rows=[];begin=time.perf_counter()
    shutil.copy2(HERE/'symbolic-audit.py',out/'sources/symbolic-audit.py');shutil.copy2(ROOT/'research/connectivity-elimination/prototype.py',out/'sources/wat-helper.py')
    try:
        for rec in json.loads((source/'manifest.json').read_text())['records']:
            folder=out/'inputs'/rec['kind'];folder.mkdir()
            for name in ('original.wasm','target.wasm','target.json'):shutil.copy2(source/rec['kind']/name,folder/name)
            original=paths(folder/'original.wasm');target=paths(folder/'target.wasm',True);env=json.loads((folder/'target.json').read_text());feasibility=[query(p['pc']) for p in original]
            checks=check_contract(original,env);assert all(x['status']=='unsat' for x in checks),checks
            equivalence=[]
            for p in original:
                same=[z.And(q['pc'],p['value']==q['value']) for q in target if [e['label'] for e in p['events']]==[e['label'] for e in q['events']]]
                equivalence.append(query(z.And(p['pc'],z.Not(z.Or(same)))))
            assert all(x['status']=='unsat' for x in equivalence),equivalence
            mutants=[]
            for i,node in enumerate(env['nodes']):
                for field in ('bound','terminalBound'):
                    if node[field] is None:continue
                    mutant=copy.deepcopy(env);mutant['nodes'][i][field]-=1;answer=check_contract(original,mutant)
                    mutants.append({'node':i,'field':field,'detected':any(x['status']=='sat' for x in answer),'checks':answer})
            rows.append({'kind':rec['kind'],'structuralPaths':len(original),'feasibility':feasibility,'coverageViolations':checks,'equivalenceCounterexamples':equivalence,'mutants':mutants})
        result={'z3':z.get_version_string(),'seconds':time.perf_counter()-begin,'rows':rows,'scope':'All 32-bit parameter pairs within modeled finite pure subset. Cost checking, raw target equivalence, no optimized-code symbolic semantics, no engine proof.'}
        (out/'results.json').write_text(json.dumps(result,indent=2),encoding='utf8')
        print(json.dumps({'models':len(rows),'paths':sum(r['structuralPaths'] for r in rows),'mutants':sum(len(r['mutants']) for r in rows),'detected':sum(m['detected'] for r in rows for m in r['mutants']),'seconds':result['seconds']}))
    finally:
        (out/'sha256.json').write_text(json.dumps({str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file() and p.name!='sha256.json'},indent=2),encoding='utf8')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args();main(a.source.resolve(),a.output.resolve())
