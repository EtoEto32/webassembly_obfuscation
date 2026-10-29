import pathlib,sys,json,subprocess,random,statistics
import prototype as p
root=p.ROOT;src=root/'results/invention-20261019/isotope-swizzle-v2'
out=root/sys.argv[1];out.mkdir(parents=True,exist_ok=False)
rows=[]
for r in json.loads((src/'manifest.json').read_text()):
    if r['opt']!='O3' or r['mode']=='plain':continue
    name=r['file'];dst=out/name
    result=p.lower(src/name,dst)
    inverse=out/(dst.stem+'-strict.wasm');back=p.lower(dst,inverse,True)
    # Existing attack after a proved semantics-preserving normalization.
    attack=p.q.lower(inverse,out/(dst.stem+'-recovered.wasm'))
    opt=out/(dst.stem+'-reopt.wasm');p.q.tool('wasm-opt',[dst,'-O3','--all-features','-o',opt])
    rows.append(dict(file=name,source=str(src/name),kernel=r['kernel'],mode=r['mode'],seed=r['seed'],lowering=result,normalization=back,attack=attack,bytes=dst.stat().st_size,source_bytes=(src/name).stat().st_size,reoptimized=str(opt)))
(out/'manifest.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
script='''const fs=require('fs'),path=require('path');const root=process.argv[1];const rows=JSON.parse(fs.readFileSync(path.join(root,'manifest.json')));const xs=JSON.parse(fs.readFileSync(process.argv[2]));let calls=0;for(const r of rows){const get=f=>new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(f))).exports.run;const orig=get(r.source),fns=[get(path.join(root,r.file)),get(r.reoptimized),get(path.join(root,r.file.replace('.wasm','-recovered.wasm')))];for(const x of xs){const y=orig(...x);calls++;for(const f of fns){if(f(...x)!==y)throw Error('mismatch '+r.file);calls++;}}}console.log(JSON.stringify({calls,inputs:xs.length,conditions:rows.length,mismatches:0}));'''
c=subprocess.run(['node','-e',script,str(out),str(src/'inputs.json')],capture_output=True,text=True,check=True)
(out/'checks.json').write_text(c.stdout,encoding='utf-8')
jobs=[(r,kind,rep) for r in rows for kind in ('original','lowered','reoptimized') for rep in range(3)];random.Random(20261021).shuffle(jobs);bench=[]
for r,kind,rep in jobs:
    f=r['source'] if kind=='original' else r['reoptimized'] if kind=='reoptimized' else out/r['file']
    a=json.loads(subprocess.check_output(['node',str(root/'research/isotope-swizzle/bench.cjs'),str(f)],text=True,timeout=30));bench.append(dict(a,file=r['file'],kind=kind,rep=rep))
    (out/'runtime.json').write_text(json.dumps(bench,indent=2),encoding='utf-8')
summary=[]
for r in rows:
    groups={k:[a for a in bench if a['file']==r['file'] and a['kind']==k] for k in ('original','lowered','reoptimized')}
    assert len({a['checksum'] for group in groups.values() for a in group})==1
    med={k:statistics.median(statistics.median(a['ns']) for a in group) for k,group in groups.items()}
    summary.append(dict(file=r['file'],ns=med,ratio=med['lowered']/med['original'],reoptimized_ratio=med['reoptimized']/med['original'],changed=r['lowering']['changed'],tables=r['attack']['tables']))
(out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(c.stdout);print(json.dumps({'processes':len(bench),'ratio_range':[min(r['ratio'] for r in summary),max(r['ratio'] for r in summary)]}))
