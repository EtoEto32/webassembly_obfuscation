"""Diagnose refinement rounds; instrumented modules are not used for timing."""
import json,statistics,subprocess,sys
from pathlib import Path
import prototype as p

def refine(labels,a,x):
    values=[base if bit==32 else base+(((x>>bit)&1)^flip) for base,bit,flip in labels]
    groups={};old=[groups.setdefault(v,i) for i,v in enumerate(values)]
    edges=[[(j,w) for j,w in enumerate(row) if w] for row in a]
    for iteration in range(1,len(a)+1):
        groups={};new=[]
        for i,row in enumerate(edges):
            masses={}
            for j,w in row:masses[old[j]]=masses.get(old[j],0)+w
            key=(old[i],tuple(sorted(masses.items())));new.append(groups.setdefault(key,i))
        if old==new:return iteration,old
        old=new
    raise AssertionError('partition did not stabilize')

def main(folder,dest):
    folder=Path(folder).resolve();out=Path(dest).resolve();out.mkdir(parents=True,exist_ok=False)
    cases=json.loads((folder/'cases.json').read_text());jobs=[];stats=[]
    for name,case in cases.items():
        labels,a,roots=p.graph(p.source(folder/(name+'-plain-raw.wasm')),213071);models={}
        for mode,weights in [('base',a),('square',p.square(a))]:
            wat=p.render(labels,weights,roots).replace('(func (export "run")','(global (export "rounds") (mut i32) (i32.const 0)) (func (export "run")',1)
            wat=wat.replace('(local.set $n','(global.set 0 (i32.const 0)) (local.set $n',1)
            wat=wat.replace('(memory.fill','(global.set 0 (i32.add (global.get 0) (i32.const 1))) (memory.fill',1)
            f=out/(name+'-'+mode+'.wasm');p.q.compile(wat,f)
            tests=[];parts=[]
            for x in range(1<<case['bits']):
                count,part=refine(labels,weights,x);tests.append({'input':x,'rounds':count,'value':int(part[roots[0]]==part[roots[1]])});parts.append(part)
            models[mode]=parts;spec=f.with_suffix('.tests.json');p.q.save(spec,tests);jobs.append({'file':f.name,'tests':spec.name})
            counts=[t['rounds'] for t in tests];stats.append({'name':name,'mode':mode,'inputs':len(tests),'mean_rounds':statistics.mean(counts),'min_rounds':min(counts),'max_rounds':max(counts)})
        assert models['base']==models['square']
    p.q.save(out/'jobs.json',jobs)
    script='''const fs=require('fs'),path=require('path'),d=process.argv[1];let calls=0;
     for(const j of JSON.parse(fs.readFileSync(path.join(d,'jobs.json')))){
       const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(d,j.file)))).exports;
       for(const t of JSON.parse(fs.readFileSync(path.join(d,j.tests)))){
         const value=e.run(t.input);if(value!==t.value||e.rounds.value!==t.rounds)throw Error(JSON.stringify({file:j.file,t,value,rounds:e.rounds.value}));calls++;}}
     console.log(JSON.stringify({calls,mismatches:0}));'''
    proc=subprocess.run(['node','-e',script,str(out)],capture_output=True,text=True,timeout=60)
    (out/'check.stdout.txt').write_text(proc.stdout,encoding='utf-8');(out/'check.stderr.txt').write_text(proc.stderr,encoding='utf-8')
    if proc.returncode:raise RuntimeError(proc.stderr)
    result={'rows':stats,'wasm_check':json.loads(proc.stdout),'instrumented':'global round counter, not used in performance'}
    p.q.save(out/'summary.json',result);print(json.dumps(result))
if __name__=='__main__':main(*sys.argv[1:])
