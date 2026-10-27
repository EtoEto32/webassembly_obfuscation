import argparse,json,random,subprocess
from pathlib import Path
import prototype as p
def main(out):
    d=Path(out);d.mkdir(parents=True,exist_ok=False);m=dict(protocol='resource-trigger-controls-v1',rows=[],negative=[])
    for n in (1,3,13,128):
        rng=random.Random(103+n);e=p.g(0)
        for i in range(n):
            op=p.STEPS[rng.randrange(4)]
            payload=['i32.xor',['i32.shr_s',p.g(1),p.c(rng.randrange(32))],p.c(rng.getrandbits(32))]
            if i%3==1:payload=['i32.and',['i32.sub',p.g(1),p.c(17)],p.c(0x80000001)]
            e=['i32.'+op,e,payload]
        source=d/(f'n{n}-source.wasm');p.q.compile(p.w.emit(p.mod(e)),source)
        for mode in ('plain','direct','immediate','deferred'):
            raw=d/(f'n{n}-{mode}-raw.wasm');p.transform(source,raw,mode,77+n);opt=raw.with_name(raw.name.replace('-raw','-o3'));p.jco('opt',raw,'-o',opt,'--quiet','--','-O3','--strip-debug')
            for target in (raw,opt):
                rec=target.with_name(target.stem+'-recovered.wasm');r=p.recover(target,rec);r.pop('code');js=target.with_suffix('');p.transpile(target,js)
                m['rows'].append(dict(id=target.stem,n=n,mode=mode,opt=target==opt,source=source.name,component=target.name,recovered=rec.name,js=js.name,expression=e,recovery=r,sha256=p.q.digest(target),recovered_sha256=p.q.digest(rec)))
        p.q.save(d/'manifest.json',m);print('control',n,flush=True)
    result=subprocess.run(['node',str(Path(__file__).with_name('check.cjs')),str(d/'manifest.json')],capture_output=True,text=True,timeout=120);(d/'check.log').write_text(result.stdout+result.stderr,encoding='utf-8');print(result.stdout,result.stderr)
    if result.returncode:raise RuntimeError('control check failed')
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('output');v=a.parse_args();main(v.output)
