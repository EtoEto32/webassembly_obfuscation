import argparse,json,re,subprocess
from pathlib import Path
import prototype as q
def load(d,n):return json.loads((d/n).read_text(encoding='utf-8'))
def main(data,replay,perf,verify,out):
    data,replay,perf,verify,out=map(Path,(data,replay,perf,verify,out));out.mkdir(parents=True,exist_ok=False);a=load(data,'manifest.json');b=load(replay,'manifest.json');assert len(a)==len(b)==30;hashes=[]
    for x,y in zip(a,b):
        assert x['file']==y['file']
        for k,h in [('file','sha256'),('recovered','recovered_sha256')]:
            v=q.digest(data/x[k]);assert v==x[h]==y[h]==q.digest(replay/y[k]);hashes.append(dict(file=x[k],sha256=v))
    assert load(data,'checks.json')==load(replay,'checks.json')
    assert load(data,'checks.json')['wasm_calls']==708480 and load(data,'checks.json')['mismatches']==0
    assert sum(x['analysis']['tables'] for x in a)==24
    assert load(verify,'summary.json')==dict(binaryen_checks=480,files=60,all_pass=True)
    native=load(perf,'native.json');assert len(native)==126
    for name in ('add','xor','mixed'):assert len({r['checksum'] for r in native if r['file'].startswith(name+'-')})==1
    for r in load(replay,'sources.json'):assert q.digest(q.ROOT/r['path'])==r['sha256']==q.digest(replay/'sources'/r['snapshot'])
    # A valid Wasm with one wrong table entry must actually change behavior.
    src=data/'add-table-s7-raw.wasm';m=q.read(src);changed=False
    def corrupt(e):
        nonlocal changed
        if not isinstance(e,list):return e
        if not changed and e[0]=='v128.bitselect':
            try:t,a,b=q.extract(e)
            except q.Unsupported:pass
            else:t[0][0]^=1;changed=True;return q.table_expr(t,a,b)
        return [corrupt(x) for x in e]
    m=corrupt(m);assert changed;bad=out/'corrupt.wasm';q.compile(q.w.emit(m),bad)
    code='const fs=require("fs");const f=p=>new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(p))).exports.run;const a=f(process.argv[1]),b=f(process.argv[2]);let w=null;for(let x=0;x<16&&!w;x++)for(let y=0;y<16&&!w;y++){const args=[Math.imul(x,0x01010101),Math.imul(y,0x01010101),0];const p=a(...args),q=b(...args);if(p!==q)w={args,original:p,corrupt:q};}if(!w)process.exit(2);console.log(JSON.stringify(w));'
    witness=json.loads(subprocess.check_output(['node','-e',code,str(src),str(bad)],text=True))
    try:q.lower(bad)
    except q.Unsupported as e:corrupt_rejection=str(e)
    else:raise AssertionError('corrupt table should not be Latin')
    # Check the added guard on mutation of i32 input parameters.
    f=out/'parameter-write.wasm';q.compile('(module (func (export "run") (param i32 i32 i32) (result i32) (local.set 0 (i32x4.extract_lane 0 (i32x4.splat (local.get 1)))) (i32x4.extract_lane 0 (i32x4.splat (local.get 0)))))',f)
    try:q.lower(f)
    except q.Unsupported as e:assert str(e)=='parameter mutation outside profile';parameter_rejection=str(e)
    else:raise AssertionError('parameter guard')
    links=0
    for f in Path(__file__).parent.glob('*.md'):
        for target in re.findall(r'\]\(([^)]+)\)',f.read_text(encoding='utf-8')):
            if target.startswith(('http:','https:','#')):continue
            assert (f.parent/target.split('#')[0]).exists(),(f,target);links+=1
    q.save(out/'binary-hashes.json',hashes);q.save(out/'negative-extra.json',dict(corruption_witness=witness,corrupt_rejection=corrupt_rejection,parameter_rejection=parameter_rejection));q.save(out/'summary.json',dict(passed=True,reproduced_targets=30,reproduced_recoveries=30,main_calls=708480,binaryen_checks=480,algebra_pairs=49152,performance_processes=126,table_targets=12,recovered_tables=24,local_links=links,goal_complete=False));print(json.dumps(load(out,'summary.json')))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('data');p.add_argument('replay');p.add_argument('performance');p.add_argument('verify');p.add_argument('output');v=p.parse_args();main(v.data,v.replay,v.performance,v.verify,v.output)
