import hashlib
import itertools
import json
from pathlib import Path
import random
import shutil
import statistics
import sys
import time
import prototype as p

def logical(gates,x):
    vals=[]
    def get(a):return x>>a[1]&1 if a[0]=='input' else vals[a[1]]
    for op,a,b in gates:
        u,v=get(a),get(b);vals.append(u&v if op=='and' else u|v if op=='or' else u^v)
    return vals
def energy(r,s):return sum(c for m,c in r['terms'] if s&m==m)
def sweep(r,s):
    for j in range(r['inputs'],r['inputs']+r['n']):
        t=s^(1<<j)
        if energy(r,t)<energy(r,s):s=t
    return s

def main(src,dst):
    src=Path(src);root=Path(dst);root.mkdir(parents=True,exist_ok=False)
    for f,h in json.loads((src/'pins.json').read_text()).items():assert hashlib.sha256((src/f).read_bytes()).hexdigest()==h
    manifest=json.loads((src/'manifest.json').read_text());records=[];replay=[];interpreter=[]
    for target in manifest['targets']:
        file=src/target['file']
        if target['mode']=='plain':I,g=manifest['models'][target['name']].values();text=p.plain(I,g)
        elif target['mode'].endswith('-recovered'):
            attack=next(x for x in manifest['attacks'] if Path(x['file']).stem+'-recovered.wasm'==target['file']);text=p.recovered_wat(attack['model'])
        else:
            trans=next(x for x in manifest['transforms'] if x['name']==target['name'] and x['mode']==target['mode']);text=p.render(trans['record'])
        out=root/target['file']
        # Recovered targets are emitted without subsequent O3 in main run.
        if target['stage']=='O3' and not target['mode'].endswith('-recovered'):
            raw=out.with_stem(out.stem+'-regen-raw');p.save(text,raw);p.w.tool('wasm-opt',[raw,'-O3','-o',out])
        else:p.save(text,out)
        assert out.read_bytes()==file.read_bytes();replay.append(target['file'])
        if target['negative']:continue
        mod=p.w.parse(p.w.tool('wasm2wat',[file,'--fold-exprs']));idx=int(next(x[2][1] for x in mod[1:] if x[:2]==['export','"run"']))
        probes=[0,1,0xffffffff,0x80000000];extra=''
        for i,x in enumerate(probes):extra+=f'(func (export "probe{i}") (result i32) (call {idx} (i32.const {x})))'
        wrapped=out.with_stem(out.stem+'-probes');p.save(p.w.emit(mod)[:-1]+extra+')',wrapped)
        result=p.w.tool('wasm-interp',[wrapped,'--run-all-exports'])
        model=manifest['models'][target['name']]
        for i,x in enumerate(probes):assert f'probe{i}() => i32:{logical(model["gates"],x)[-1]}' in result,result
        interpreter.append({'file':file.name,'calls':4,'stdout':result})
    # Full-state correctness and wrong local minima in a small example.
    small=[['xor',['input',0],['input',1]],['and',['gate',0],['input',0]],['or',['gate',1],['input',1]]]
    small_rows=[]
    for mode,gauge in itertools.product(('dag','lex','flat'),(False,True)):
        r,c=p.build(2,small,mode,gauge);mismatch=0;first=None
        for x,s0 in itertools.product(range(4),range(8)):
            s=x|(s0<<2)
            for _ in range(3):s=sweep(r,s)
            physical=[s>>(2+c['permutation'][i])&1 for i in range(3)]
            decoded=[v^f for v,f in zip(physical,c['complements'])];expected=logical(small,x)
            if decoded!=expected:mismatch+=1;first=first or {'input':x,'initial':s0,'decoded':decoded,'expected':expected}
        if mode!='flat':assert mismatch==0
        small_rows.append({'mode':mode,'gauge':gauge,'states':32,'mismatches':mismatch,'first':first})
    # Compare each recovered local rule to its source gate for every assignment
    # to the union of their dependencies. This is post-hoc verification only.
    rule_cases=0;times=[]
    for tr in manifest['transforms']:
        if tr['mode']=='flat-gauge':continue
        r=tr['record'];I=r['inputs'];c=tr['certificate'];gates=manifest['models'][tr['name']]['gates'];m=p.recover_model(r)
        for i,(op,a,b) in enumerate(gates):
            physical=I+c['permutation'][i];rule=next(v for v in m['rules'] if v['coordinate']==physical)
            def coord(v):return v[1] if v[0]=='input' else I+c['permutation'][v[1]]
            support=sorted(set(rule['args']+[coord(a),coord(b)]))
            for state in range(1<<len(support)):
                assigned={k:state>>q&1 for q,k in enumerate(support)}
                def get(v):return assigned[coord(v)]^(c['complements'][v[1]] if v[0]=='gate' else 0)
                u,v=get(a),get(b);expected=(u&v if op=='and' else u|v if op=='or' else u^v)^c['complements'][i]
                index=sum(assigned[k]<<q for q,k in enumerate(rule['args']));assert (rule['truth']>>index&1)==expected;rule_cases+=1
        samples=[]
        for _ in range(11):start=time.perf_counter();p.recover_model(r);samples.append((time.perf_counter()-start)*1000)
        times.append({'name':tr['name'],'mode':tr['mode'],'samples_ms':samples,'median_ms':statistics.median(samples)})
    # A valid but modified evaluator must not pass a coefficient-only attack.
    tr=manifest['transforms'][0];text=p.render(tr['record']);text=text.replace('(i64.lt_s (local.get $q) (local.get $e))','(i64.gt_s (local.get $q) (local.get $e))')
    altered=root/'altered-evaluator.wasm';p.save(text,altered)
    try:p.recover(altered,root/'altered-recovered.wasm');raise AssertionError('Accepted unrelated evaluator')
    except ValueError as e:assert 'differs' in str(e);rejection=str(e)
    source_rejections=[]
    cases={'memory':'(module (memory 1) (func (export "run") (param i32) (result i32) (local.get 0)))',
           'forward':'(module (func (export "run") (param i32) (result i32) (local i32 i32) (local.set 1 (i32.and (local.get 2) (i32.const 1))) (local.set 2 (i32.const 0)) (local.get 2)))',
           'nonboolean':'(module (func (export "run") (param i32) (result i32) (local i32) (local.set 1 (i32.add (local.get 0) (i32.const 1))) (local.get 1)))'}
    for name,text in cases.items():
        out=root/('reject-'+name+'.wasm');p.save(text,out)
        try:p.source(out);raise AssertionError('Unsupported source accepted')
        except ValueError as e:source_rejections.append({'name':name,'reason':str(e)})
    result={'byte_replay':replay,'wabt':interpreter,'small_all_initial_states':small_rows,'local_rule_cases':rule_cases,'core_timings':times,'altered_evaluator_rejection':rejection,'source_rejections':source_rejections}
    (root/'audit.json').write_text(json.dumps(result,indent=2),encoding='utf8');shutil.copyfile(p.HERE/'audit.py',root/'source-audit.py')
    (root/'pins.json').write_text(json.dumps({x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in root.iterdir() if x.is_file()},indent=2),encoding='utf8')
    print(json.dumps({'byte_replay':len(replay),'wabt_calls':sum(x['calls'] for x in interpreter),'local_rule_cases':rule_cases,'small':small_rows},indent=2))

if __name__=='__main__':main(*sys.argv[1:])
