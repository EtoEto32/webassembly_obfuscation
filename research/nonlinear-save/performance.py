import json, random, statistics, subprocess, sys
from pathlib import Path
import prototype as p
def main(folder,dest):
    folder=Path(folder).resolve();out=Path(dest).resolve();out.mkdir(parents=True,exist_ok=False)
    rows=json.loads((folder/'manifest.json').read_text());variants=[]
    for row in rows:
        if row['opt']!='O3' or row['mode'] not in ('plain','full','linear','color','color-recovered'):continue
        mod=p.q.read(folder/row['file']);exp={e[1].strip('"'):int(e[2][1]) for e in mod[1:] if e[0]=='export'}
        body='''(func (export "bench") (param i32 i32) (result i32) (local i32 i32)
         (block (loop (br_if 1 (i32.ge_u (local.get 2) (local.get 0)))
          (local.set 1 (i32.add (i32.mul (local.get 1) (i32.const 1664525)) (i32.const 1013904223)))
          (call RESET (i32.shr_u (local.get 1) (i32.const 16))) (call RUN (i32.const -1))
          (local.set 3 (i32.add (i32.mul (local.get 3) (i32.const 33)) (call PEEK)))
          (local.set 2 (i32.add (local.get 2) (i32.const 1))) (br 0))) (local.get 3))'''
        for name in ('reset','run','peek'):body=body.replace(name.upper(),str(exp[name]))
        f=out/(Path(row['file']).stem+'-bench.wasm');p.q.compile(p.q.w.emit(mod)[:-1]+body+')',f)
        variants.append({'name':row['name'],'mode':row['mode'],'file':f.name,'core_bytes':row['bytes'],'linear_memory_bytes':65536})
    p.q.save(out/'inputs.json',variants)
    script='''const fs=require('fs'),path=require('path'),d=process.argv[1],rows=JSON.parse(fs.readFileSync(path.join(d,'inputs.json')));let count=0;for(const name of ['copy0','copy1','copy2'])for(const n of [0,1,31,1024])for(const seed of [0,1,0xffffffff]){const xs=rows.filter(r=>r.name===name).map(r=>new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(d,r.file)))).exports.bench(n,seed));if(new Set(xs).size!==1)throw Error('wrapper mismatch');count+=xs.length;}console.log(count);'''
    result=subprocess.run(['node','-e',script,str(out)],capture_output=True,text=True,timeout=60);assert result.returncode==0,result.stderr
    p.q.save(out/'wrapper-check.json',{'calls':int(result.stdout),'mismatches':0})
    schedule=[(r,k) for r in variants for k in range(3)];random.Random(213099).shuffle(schedule);raw=[]
    for row,k in schedule:
        result=subprocess.run(['node','--no-liftoff','--no-wasm-lazy-compilation',str(p.ROOT/'research/span-mask/bench.cjs'),str(out/row['file'])],capture_output=True,text=True,timeout=60)
        assert result.returncode==0,result.stderr
        raw.append({**row,'repeat':k,'measurement':json.loads(result.stdout)});p.q.save(out/'raw.json',raw)
        if len(raw)%15==0:print('processes',len(raw),flush=True)
    summary=[]
    for row in variants:
        ms=[r['measurement'] for r in raw if r['file']==row['file']];meds=[statistics.median(m['ns_per_call']) for m in ms]
        summary.append({**row,'median_ns':statistics.median(meds),'process_medians':meds,'min_ns':min(v for m in ms for v in m['ns_per_call']),'max_ns':max(v for m in ms for v in m['ns_per_call']),'max_rss_kib':max(m['max_rss_kib'] for m in ms)})
    result={'rows':summary,'processes':len(raw),'batches':sum(len(r['measurement']['batches']) for r in raw),'under_10ms':sum(b['ms']<10 for r in raw for b in r['measurement']['batches'])};p.q.save(out/'summary.json',result);print(json.dumps(result))
if __name__=='__main__':main(*sys.argv[1:])
