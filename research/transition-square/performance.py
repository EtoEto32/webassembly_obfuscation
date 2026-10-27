import json,random,statistics,subprocess,sys
from pathlib import Path
import prototype as p

def main(folder,dest):
    folder=Path(folder).resolve();out=Path(dest).resolve();out.mkdir(parents=True,exist_ok=False)
    rows=json.loads((folder/'manifest.json').read_text());variants=[]
    for row in rows:
        if row['opt']!='O3' or row['mode'] not in ('plain','base','square','square-recovered') or row['seed'] not in (0,213071):continue
        source=folder/row['file'];m=p.q.read(source)
        body='''(func (export "bench") (param i32 i32) (result i32) (local i32 i32)
          (block (loop (br_if 1 (i32.ge_u (local.get 2) (local.get 0)))
            (local.set 1 (i32.add (i32.mul (local.get 1) (i32.const 1664525)) (i32.const 1013904223)))
            (local.set 3 (i32.add (i32.mul (local.get 3) (i32.const 33)) (call 0 (local.get 1))))
            (local.set 2 (i32.add (local.get 2) (i32.const 1))) (br 0))) (local.get 3))'''
        target=out/(source.stem+'-bench.wasm');p.q.compile(p.q.w.emit(m)[:-1]+body+')',target)
        memory=next((int(e[1])*65536 for e in m[1:] if e[0]=='memory'),0)
        variants.append({'name':row['name'],'mode':row['mode'],'file':target.name,'core_bytes':row['bytes'],'linear_memory_bytes':memory})
    p.q.save(out/'inputs.json',variants)
    script='''const fs=require('fs'),path=require('path'),d=process.argv[1],rows=JSON.parse(fs.readFileSync(path.join(d,'inputs.json')));let calls=0;
     for(const name of ['bits4','bits8','bits12'])for(const n of [0,1,31,1024])for(const seed of [0,1,0x41b3917]){
       const values=rows.filter(x=>x.name===name).map(x=>new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(d,x.file)))).exports.bench(n,seed));
       if(new Set(values).size!==1)throw Error('wrapper mismatch');calls+=values.length;}console.log(calls);'''
    check=subprocess.run(['node','-e',script,str(out)],capture_output=True,text=True,timeout=60);assert check.returncode==0,check.stderr
    p.q.save(out/'wrapper-check.json',{'calls':int(check.stdout),'mismatches':0})
    schedule=[(r,i) for r in variants for i in range(3)];random.Random(213073).shuffle(schedule);raw=[]
    for row,i in schedule:
        result=subprocess.run(['node','--no-liftoff','--no-wasm-lazy-compilation',str(p.ROOT/'research/span-mask/bench.cjs'),str(out/row['file'])],capture_output=True,text=True,timeout=60)
        if result.returncode:raise RuntimeError(result.stderr)
        raw.append({**row,'repeat':i,'measurement':json.loads(result.stdout)});p.q.save(out/'raw.json',raw)
        if len(raw)%12==0:print('processes',len(raw),flush=True)
    summary=[]
    for row in variants:
        measurements=[r['measurement'] for r in raw if r['file']==row['file']];meds=[statistics.median(m['ns_per_call']) for m in measurements]
        summary.append({**row,'median_ns':statistics.median(meds),'process_medians':meds,'min_ns':min(v for m in measurements for v in m['ns_per_call']),'max_ns':max(v for m in measurements for v in m['ns_per_call']),'max_rss_kib':max(m['max_rss_kib'] for m in measurements)})
    result={'rows':summary,'processes':len(raw),'batches':sum(len(r['measurement']['batches']) for r in raw),'under_10ms':sum(b['ms']<10 for r in raw for b in r['measurement']['batches'])}
    p.q.save(out/'summary.json',result);print(json.dumps(result))
if __name__=='__main__':main(*sys.argv[1:])
