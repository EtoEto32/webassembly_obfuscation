# -*- coding: utf-8 -*-
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import sys
import time
import relaxed as r
import audit as old

def pincheck(root):
    pins=json.loads((root/'pins.json').read_text())
    for f,h in pins.items():assert hashlib.sha256((root/f).read_bytes()).hexdigest()==h,f
    return len(pins)

def boolean_rule(rule,state):
    terms=[]
    for a in range(1<<len(rule['args'])):
        if rule['truth']>>a&1:
            terms.append(r.z3.And(*[state[k] if a>>q&1 else r.z3.Not(state[k]) for q,k in enumerate(rule['args'])]))
    return r.z3.Or(*terms)

def check_rules(record,model,gates):
    z=r.z3.Bools(' '.join('b%d'%i for i in range(record['inputs']+record['n'])))
    def poly(P):return r.z3.Sum([c*r.z3.If(r.z3.And(*[z[k] for k in range(len(z)) if mask>>k&1]),1,0) for mask,c in P.items()])
    E=dict(record['terms']);cert=[]
    for rule in reversed(model['rules']):
        j=rule['coordinate'];D={mask^(1<<j):c for mask,c in E.items() if mask>>j&1};d=poly(D)
        chosen=r.z3.If(boolean_rule(rule,z),d,0)
        s=r.z3.Solver();s.set(timeout=15000);s.add(r.z3.Or(chosen>0,chosen>d));st=s.check();assert st==r.z3.unsat,(rule,str(st))
        cert.append({'coordinate':j,'minimizer_miter':str(st)})
        candidate=r.local_rule(E,j,len(z));assert candidate and candidate['args']==rule['args'] and candidate['truth']==rule['truth']
        E=candidate['reduced']
    assert not E
    state={i:z[i] for i in range(record['inputs'])}
    for rule in model['rules']:state[rule['coordinate']]=boolean_rule(rule,state)
    actual=state[model['output']]
    if model['flip']:actual=r.z3.Not(actual)
    values=[];ops={'and':r.z3.And,'or':r.z3.Or,'xor':r.z3.Xor}
    def get(a):return z[a[1]] if a[0]=='input' else values[a[1]]
    for op,a,b in gates:values.append(ops[op](get(a),get(b)))
    s=r.z3.Solver();s.set(timeout=15000);s.add(actual!=values[-1]);st=s.check();assert st==r.z3.unsat,'output mismatch'
    return {'steps':cert,'output_miter':str(st)}

def main(dst,sources):
    root=Path(dst);root.mkdir(parents=True,exist_ok=False);replay=[];wabt=[];certs=[];fresh=[];times=[];negatives=[];pin_counts={}
    for source in sources:
        src=Path(source);pin_counts[src.name]=pincheck(src);m=json.loads((src/'manifest.json').read_text())
        outroot=root/src.name;outroot.mkdir()
        for t in m['targets']:
            file=src/t['file'];out=outroot/t['file']
            if t['mode']=='plain':model=m['models'][t['name']];text=r.p.plain(model['inputs'],model['gates'])
            elif t['mode'].endswith('-recovered'):
                a=next(a for a in m['attacks'] if Path(a['file']).stem+'-recovered.wasm'==t['file']);text=r.p.recovered_wat(a['model'])
            else:text=r.render(next(a['record'] for a in m['transforms'] if (a['name'],a['mode'])==(t['name'],t['mode'])))
            if t['stage']=='O3' and not t['mode'].endswith('-recovered'):
                raw=out.with_stem(out.stem+'-raw');r.p.save(text,raw);r.p.w.tool('wasm-opt',[raw,'-O3','-o',out])
            else:r.p.save(text,out)
            assert file.read_bytes()==out.read_bytes();replay.append(str(file))
            mod=r.p.w.parse(r.p.w.tool('wasm2wat',[out,'--fold-exprs']));idx=int(next(x[2][1] for x in mod[1:] if x[:2]==['export','"run"']))
            inputs=[0,1,0xffffffff,0x80000000]
            extra=''.join(f'(func (export "p{i}") (result i32) (call {idx} (i32.const {x})))' for i,x in enumerate(inputs))
            probe=out.with_stem(out.stem+'-wabt');r.p.save(r.p.w.emit(mod)[:-1]+extra+')',probe)
            result=r.p.w.tool('wasm-interp',[probe,'--run-all-exports'])
            for i,x in enumerate(inputs):assert f'p{i}() => i32:{old.logical(m["models"][t["name"]]["gates"],x)[-1]}' in result,result
            wabt.append({'file':str(file),'calls':4,'stdout':result})
        for a in m['attacks']:
            file=src/a['file'];record=r.p.rawdata(r.p.w.parse(r.p.w.tool('wasm2wat',[file,'--fold-exprs'])))
            certs.append({'file':str(file),**check_rules(record,a['model'],m['models'][a['name']]['gates'])})
            samples=[]
            for _ in range(11):start=time.perf_counter();r.eliminate(record);samples.append((time.perf_counter()-start)*1000)
            times.append({'file':str(file),'samples_ms':samples,'median_ms':statistics.median(samples)})
        for f in src.glob('*-no-false-minimum.smt2'):
            s=r.z3.Solver();s.set(timeout=15000);s.from_string(f.read_text());st=s.check();assert st==r.z3.unsat
            fresh.append({'file':str(f),'result':str(st)})
        for item in m['flat_controls']:
            if item['status']!='sat':continue
            c=item['counterexample'];gs=m['models'][item['name']]['gates'];I=m['models'][item['name']]['inputs'];E=sum(r.errors(I,gs,c['x'],c['state']))
            neighbors=[sum(r.errors(I,gs,c['x'],c['state']^(1<<j))) for j in range(len(gs))]
            assert E>0 and min(neighbors)>=E
            negatives.append({'name':item['name'],'energy':E,'neighbors':neighbors})
    # Distinct evaluator with the same table must be rejected, not trusted.
    record=m['transforms'][-1]['record'];text=r.render(record).replace('(i64.lt_s (local.get $q) (local.get $e))','(i64.gt_s (local.get $q) (local.get $e))')
    altered=root/'altered-evaluator.wasm';r.p.save(text,altered)
    try:r.recover(altered,root/'altered-recovered.wasm');raise AssertionError('Modified evaluator accepted')
    except ValueError as e:assert 'Unsupported evaluator' in str(e);rejection=str(e)
    # Mutated recovery rule must fail the independent source-output miter.
    bad=json.loads(json.dumps(a['model']));bad['flip']^=1
    try:check_rules(record,bad,m['models'][a['name']]['gates']);raise RuntimeError('Bad recovery accepted')
    except AssertionError as e:assert str(e)=='output mismatch';bad_recovery_detected=True
    result={'source_pin_counts':pin_counts,'byte_replay':replay,'wabt':wabt,'minimization_and_output_certificates':certs,'fresh_no_false_minimum':fresh,'flat_counterexamples':negatives,'core_timings':times,'modified_evaluator_rejected':rejection,'bad_recovery_detected':bad_recovery_detected,'z3':r.z3.get_version_string()}
    (root/'audit.json').write_text(json.dumps(result,indent=2),encoding='utf8');shutil.copyfile(Path(__file__),root/'source-relaxed-audit.py')
    pins={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
    (root/'pins.json').write_text(json.dumps(pins,indent=2),encoding='utf8')
    print(json.dumps({'byte_replay':len(replay),'wabt_calls':sum(x['calls'] for x in wabt),'certificates':len(certs),'no_false_minimum':len(fresh),'pins':len(pins)}))

if __name__=='__main__':main(sys.argv[1],sys.argv[2:])
