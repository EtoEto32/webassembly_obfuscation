import collections
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import attack
import prototype as p


def main(base,out):
    base=Path(base).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);rows=[]
    for name in ('mix8','select10','chain12'):
        for mode in ('pipeline','linear','nonlinear'):
            for opt in ('','-O3'):
                src=base/(name+'-'+mode+opt+'.wasm');r,ms=attack.read(src);attempts=[];start=time.perf_counter()
                for degree in (1,2):
                    res,text=attack.recover(r,degree,45);attempts.append(res)
                    if text:break
                row={'name':name,'mode':mode,'optimization':opt or 'raw','read_ms':ms,'analysis_ms':(time.perf_counter()-start)*1000,'attempts':attempts,'status':res['status'],'source':str(src)}
                if text:
                    dest=out/(src.stem+'-recovered.wasm');p.save(text,dest);optimized=dest.with_name(dest.stem+'-O3.wasm');p.w.tool('wasm-opt',[dest,'-O3','-o',optimized]);p.w.tool('wasm-validate',[optimized]);row['output']=str(dest);row['optimized']=str(optimized)
                rows.append(row);(out/'attacks.json').write_text(json.dumps(rows,indent=2));print(json.dumps({k:row[k] for k in ('name','mode','optimization','status','analysis_ms')}),flush=True)
    check=subprocess.run(['node',str(p.HERE/'check.cjs'),str(out)],capture_output=True,text=True,timeout=180)
    (out/'check.stdout.log').write_text(check.stdout);(out/'check.stderr.log').write_text(check.stderr)
    if check.returncode:raise RuntimeError(check.stderr)
    (out/'summary.json').write_text(json.dumps({'targets':len(rows),'attempts':sum(len(r['attempts']) for r in rows),'statuses':dict(collections.Counter(r['status'] for r in rows)),'correctness':json.loads(check.stdout)},indent=2))
    (out/'pins.json').write_text(json.dumps({str(f.relative_to(p.ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in out.rglob('*') if f.is_file() and f.name!='pins.json'},indent=2))

if __name__=='__main__':main(*sys.argv[1:])
