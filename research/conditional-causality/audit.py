# -*- coding: utf-8 -*-
"""Independent symbolic composition, BV helper checks, byte replay and WABT."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import sys
import time

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'.tools/encoding-synthesis-python'))
import z3
spec=importlib.util.spec_from_file_location('causal_audit',HERE/'prototype.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
MASK=(1<<32)-1


def write(path,data):Path(path).write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf8')


def symbolic(f,x):
    loc=[x]+[z3.BitVecVal(0,32) for t in f if t[0]=='local' for _ in t[1:]]
    def ev(t):
        op=t[0]
        if op=='local.get':return loc[int(t[1])]
        if op=='i32.const':return z3.BitVecVal(int(t[1])&MASK,32)
        if op in ('local.tee','local.set'):
            loc[int(t[1])]=ev(t[2]);return loc[int(t[1])]
        a,b=ev(t[1]),ev(t[2]);k=b&31
        if op=='i32.add':return a+b
        if op=='i32.sub':return a-b
        if op=='i32.mul':return a*b
        if op=='i32.xor':return a^b
        if op=='i32.or':return a|b
        if op=='i32.and':return a&b
        if op=='i32.shl':return a<<k
        if op=='i32.shr_u':return z3.LShR(a,k)
        if op=='i32.shr_s':return a>>k
        if op=='i32.rotl':return (a<<k)|z3.LShR(a,(-k)&31)
        if op=='i32.rotr':return z3.LShR(a,k)|(a<<((-k)&31))
        raise ValueError(op)
    result=None
    for t in f:
        if t[0] not in ('param','result','local','type'):result=ev(t)
    return result


def composition_certificate(r,orders):
    n=r['n'];facts=[]
    for flag in (0,1):
        cells=[('initial',j) for j in range(n)]
        schedule=r['schedule'] if r['mode']=='cyclic' else r['schedule'][flag*n:(flag+1)*n]
        for j in schedule:
            pred=r['preds'][flag][j];argument=('x',) if pred==n else cells[pred]
            cells[j]=('call',j,argument)
        want=('x',)
        for j in orders[flag]:want=('call',j,want)
        if cells[r['roots'][flag]]!=want:raise AssertionError('Symbolic schedule failed')
        facts.append({'selector':flag,'arbitrary_initial_states_eliminated':True,'composition_equal':True})
    return facts


def concrete(f,x,s):
    def rot(v,k):return ((v<<k)|(v>>(32-k)))&MASK
    x&=MASK
    for j in f['orders'][s&1]:
        a=f['ops'][j]
        if a['kind']==0:x=rot((x+a['a'])&MASK,a['k'])^a['b']
        elif a['kind']==1:x=(((x^a['a'])*a['b'])+rot(x,a['k']))&MASK
        else:x=rot(x^a['a'],a['k'])^(x>>a['h'])^a['b']
    return x&MASK


def main(main_dir,perf_dir,out):
    main_dir=Path(main_dir);perf_dir=Path(perf_dir);out=Path(out);out.mkdir(parents=True,exist_ok=False)
    (out/'sources').mkdir()
    for name in ('audit.py','prototype.py'):shutil.copyfile(HERE/name,out/'sources'/name)
    m=json.loads((main_dir/'manifest.json').read_text(encoding='utf8'))
    checks={'hashes':0,'helper_equivalence':[],'composition':[],'replays':[],'interpreter':[],'negative':[]}
    for root in (main_dir,perf_dir):
        pins=json.loads((root/'sha256.json').read_text(encoding='utf8'))
        for file,h in pins.items():
            if hashlib.sha256((root/file).read_bytes()).hexdigest()!=h:raise AssertionError('Hash mismatch '+file)
            checks['hashes']+=1
    orig={name:p.source(main_dir/name/'plain.wasm') for name in m['fixtures']}
    generated={}
    for name,(helpers,orders) in orig.items():
        d=out/name;d.mkdir();direct=d/'plain.wasm';p.save(p.direct(helpers,orders),direct)
        opt=direct.with_stem('plain-O3');p.optimize(direct,opt)
        generated[(name,'plain','raw')]=direct;generated[(name,'plain','O3')]=opt
        for mode in ('ordered','cyclic'):
            r=p.make_record(helpers,orders,mode);raw=d/(mode+'.wasm');p.save(p.render(helpers,r),raw)
            optimized=raw.with_stem(mode+'-O3');p.optimize(raw,optimized)
            for form,binary in (('raw',raw),('O3',optimized)):
                generated[(name,mode,form)]=binary
                actual=main_dir/name/(mode+('' if form=='raw' else '-O3')+'.wasm')
                hs,record=p.read_family(actual,d/(mode+'-'+form+'-read'))
                for j,(f,g) in enumerate(zip(helpers,hs)):
                    x=z3.BitVec('x',32);solver=z3.Solver();solver.set(timeout=15000);solver.add(symbolic(f,x)!=symbolic(g,x))
                    begin=time.perf_counter();status=str(solver.check());ms=(time.perf_counter()-begin)*1000
                    checks['helper_equivalence'].append({'fixture':name,'mode':mode,'form':form,'helper':j,'result':status,'ms':ms})
                    if status!='unsat':raise AssertionError('Unproved helper '+status)
                checks['composition'].append({'fixture':name,'mode':mode,'form':form,'facts':composition_certificate(record,orders)})
                rec=d/(mode+'-'+form+'-recovered.wasm');p.save(p.direct(hs,p.recover_orders(record)),rec)
                generated[(name,mode+'-recovered',form)]=rec
        # A public table is not enough: changing evaluator code must fail the guard.
        r=p.make_record(helpers,orders,'cyclic')
        text=p.render(helpers,r).replace('(local.set $s (i32.and (local.get $s) (i32.const 1)))','(local.set $s (i32.and (local.get $s) (i32.const 0)))')
        tampered=d/'bad-evaluator.wasm';p.save(text,tampered)
        try:p.recover(tampered,d/'bad-evaluator-recovered.wasm')
        except ValueError as e:checks['negative'].append({'fixture':name,'case':'changed-code','reason':str(e)})
        else:raise AssertionError('Changed evaluator accepted')
    samples=[(0,0),(-1,1),(123456789,2),(-2147483648,3)]
    for i,t in enumerate(m['targets']):
        original=main_dir/t['file'];rebuilt=generated[(t['fixture'],t['mode'],t['form'])]
        same=original.read_bytes()==rebuilt.read_bytes()
        if not same:raise AssertionError('Byte replay '+t['file'])
        checks['replays'].append({'file':t['file'],'byte_equal':same})
        mod=p.w.parse(p.w.tool('wasm2wat',[original,'--fold-exprs']))
        idx=next(x[2][1] for x in mod[1:] if x[:2]==['export','"run"'])
        extra=' '.join(f'(func (export "probe{k}") (result i32) (call {idx} (i32.const {x}) (i32.const {s})))' for k,(x,s) in enumerate(samples))
        wrapper=out/f'interpreter-{i:02d}.wasm';p.save(p.w.emit(mod)[:-1]+extra+')',wrapper)
        log=p.w.tool('wasm-interp',[wrapper,'--run-all-exports']);(out/f'interpreter-{i:02d}.txt').write_text(log,encoding='utf8')
        values=[int(v)&MASK for _,v in re.findall(r'probe(\d+)\(\) => i32:(-?\d+)',log)]
        expected=[concrete(m['fixtures'][t['fixture']],x,s) for x,s in samples]
        if values!=expected:raise AssertionError('WABT mismatch '+t['file'])
        checks['interpreter'].append({'file':t['file'],'calls':len(values),'values':values})
    checks['z3']=z3.get_version_string()
    write(out/'facts.json',checks)
    write(out/'sha256.json',{str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(out.rglob('*')) if f.is_file()})
    print(json.dumps({'hashes_checked':checks['hashes'],'helper_smt':len(checks['helper_equivalence']),'composition_cases':sum(len(t['facts']) for t in checks['composition']),'byte_replay':len(checks['replays']),'wabt_calls':sum(t['calls'] for t in checks['interpreter']),'negative':len(checks['negative'])}))


if __name__=='__main__':main(*sys.argv[1:])
