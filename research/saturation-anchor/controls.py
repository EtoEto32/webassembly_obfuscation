import json,random,subprocess,sys
from pathlib import Path
import prototype as p

src,out=map(Path,sys.argv[1:]);out.mkdir(parents=True,exist_ok=False);q=p.q
algebra=0;wrong_relaxed=0
for seed in range(128):
    e=p.perm('anchor-zero',seed)
    for x in range(16):
        for y in range(16):
            s=x+y;v=e[s] if s<16 else 0
            assert v==e[min(s,15)];algebra+=1
            if e[s%16]!=v:wrong_relaxed+=1
q.save(out/'algebra.json',dict(strict_checks=algebra,low_index_relaxed_disagreements=wrong_relaxed,scope='scalar models, not a second Wasm engine'))
clones=[]
for r in json.loads((src/'manifest.json').read_text()):
    if r['mode']!='anchor-zero' or r['counters_per_bank']!=256:continue
    for kind in ('all-strict','unsafe-all-relaxed'):
        m=q.read(src/r['file'])
        for e in q.walk(m):
            if kind=='all-strict' and e[0]=='i8x16.relaxed_swizzle':e[0]='i8x16.swizzle'
            if kind=='unsafe-all-relaxed' and e[0]=='i8x16.swizzle':e[0]='i8x16.relaxed_swizzle'
        f=out/(kind+'-'+r['file']);q.compile(q.w.emit(m),f)
        clones.append(dict(file=f.name,kind=kind))
code='''const fs=require('fs');const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[1]))).exports;
let bad=[];for(let i=0;i<256;i++){e.set(i,0,i>>4);e.set(i,1,i&15);}e.merge();
for(let i=0;i<256;i++){let actual=e.get(i,0),expected=Math.min((i>>4)+(i&15),15);if(actual!==expected)bad.push({x:i>>4,y:i&15,actual,expected});}
console.log(JSON.stringify({pairs:256,mismatches:bad.length,first:bad[0]||null}));'''
for r in clones:
    r.update(json.loads(subprocess.check_output(['node','-e',code,str(out/r['file'])],text=True)))
    if r['kind']=='all-strict':assert r['mismatches']==0
    else:assert r['mismatches']==120
q.save(out/'clones.json',clones)
bad_sources={
    'export-memory':p.build(256).replace('(module','(module (export "memory" (memory 0))',1),
    'changed-state':p.build(256).replace('(module','(module (global i32 (i32.const 1))',1),
    'wrapping-merge':p.build(256).replace('i8x16.min_u','i8x16.add'),
}
rejections=[]
for name,text in bad_sources.items():
    f=out/(name+'.wasm');q.compile(text,f)
    try:p.transform(f,out/(name+'-converted.wasm'),'anchor-zero')
    except q.Unsupported as e:rejections.append(dict(name=name,status='rejected',reason=str(e)))
    else:raise AssertionError(name+' accepted')
try:p.build(256,'anchor-zero',list(range(16)))
except q.Unsupported as e:rejections.append(dict(name='wrong-anchor',status='rejected',reason=str(e)))
else:raise AssertionError('wrong anchor accepted')
q.save(out/'rejections.json',rejections)
print(json.dumps(dict(algebra=algebra,strict_clones=4,unsafe_clones=4,rejected=len(rejections))))
