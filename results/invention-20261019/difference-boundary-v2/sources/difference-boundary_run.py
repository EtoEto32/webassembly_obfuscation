"""Binary generation, adaptive recovery and persistent-state verification."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import random
import shutil
import subprocess
import sys
import prototype as p

HERE=Path(__file__).resolve().parent
def save(path,x):path.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def command(args,timeout=180):
    r=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=timeout)
    if r.returncode:raise RuntimeError(r.stdout+'\n'+r.stderr)
    return json.loads(r.stdout)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);ap.add_argument('--compare',type=Path);ap.add_argument('--quick',action='store_true');ap.add_argument('--sizes',type=int,nargs='+',default=[64,1024,8192]);o=ap.parse_args()
    out=o.output;out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir();hashes={}
    for path in [HERE/'prototype.py',HERE/'run.py',HERE/'check.cjs',p.ROOT/'research/zero-extent/prototype.py',p.ROOT/'research/connectivity-elimination/prototype.py']:
        name=path.parent.name+'_'+path.name;shutil.copyfile(path,out/'sources'/name);hashes[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    save(out/'environment.json',dict(platform=platform.platform(),python=sys.version,node=command(['node','-e','console.log(JSON.stringify({node:process.version,v8:process.versions.v8}))']),wabt=p.w.tool('wat2wasm',['--version']).strip(),binaryen=p.w.tool('wasm-opt',['--version']).strip(),sources=hashes))
    files=[];datasets={};transforms=[];attacks=[]
    def record(path,dataset,mode,level,recovered=False):
        probe=out/(path.stem+'.probe.wasm');text=p.w.tool('wasm2wat',[path]);p.c.compile_wat(text.rstrip()[:-1]+'(export "memory" (memory 0)))',probe)
        files.append(dict(path=path.name,dataset=dataset,mode=mode,opt=level,recovered=recovered,probe=probe.name,bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    for n in (o.sizes[:1] if o.quick else o.sizes):
        name='n'+str(n);rng=random.Random(20261019+n);bs=bytes(rng.randrange(1,256) for _ in range(n-1))+b'\xff'
        if n>1 and bs[-2]==255:bs=bs[:-2]+b'\xfe\xff'
        datasets[name]=list(bs);src=out/(name+'.plain.raw.wasm');p.c.compile_wat(p.wat(bs,'plain'),src)
        for mode in p.MODES:
            raw=out/(name+'.'+mode+'.raw.wasm')
            if mode!='plain':transforms.append(dict(dataset=name,**p.transform(src,raw,mode)))
            for level in ('raw','O3'):
                path=raw if level=='raw' else out/(name+'.'+mode+'.O3.wasm')
                if level=='O3':p.w.tool('wasm-opt',[raw,'-O3','--all-features','-o',path]);p.w.tool('wasm-validate',[path])
                record(path,name,mode,level)
                dst=out/(path.stem+'.recovered.wasm')
                try:
                    stats=p.recover(path,dst);record(dst,name,mode,level,True)
                    stats['same_as_original_raw']=dst.read_bytes()==src.read_bytes();assert stats['same_as_original_raw']
                except ValueError as e:stats=dict(status='unsupported',error=str(e))
                except Exception as e:stats=dict(status='error',error=repr(e))
                attacks.append(dict(path=path.name,**stats))
            print(name+' '+mode,flush=True)
        save(out/'manifest.json',dict(datasets=datasets,files=files));save(out/'transforms.json',transforms);save(out/'attacks.json',attacks)
    save(out/'correctness.json',command(['node',HERE/'check.cjs',out]))
    if o.compare:
        old={x['path']:x['sha256'] for x in json.loads((o.compare/'manifest.json').read_text())['files']}
        save(out/'replay.json',dict(same=[x['path'] for x in files if x['sha256']==old.get(x['path'])],different=[x['path'] for x in files if x['sha256']!=old.get(x['path'])]))
    result=dict(status='completed',binaries=len(files),attack_statuses={s:sum(x['status']==s for x in attacks) for s in sorted(set(x['status'] for x in attacks))})
    save(out/'summary.json',result);print(json.dumps(result))

if __name__=='__main__':main()
