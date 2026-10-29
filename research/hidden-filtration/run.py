import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import time
import attack
import prototype as p
import smoke


def run(out,seconds):
    out=Path(out).resolve();records=smoke.build(out);attacks=[]
    manifest={'environment':{'python':platform.python_version(),'os':platform.platform(),'wabt':p.w.tool('wat2wasm',['--version']).strip(),'binaryen':p.w.tool('wasm-opt',['--version']).strip()},'transformations':records,'attacks':attacks}
    for row in records:
        for opt in (False,True):
            src=Path(row['path']);src=src.with_name(src.stem+'-O3.wasm') if opt else src
            for degree in (1,2):
                dest=out/(src.stem+f'-recovered-d{degree}.wasm')
                t=time.perf_counter()
                try:res=attack.run(src,dest,degree,seconds)
                except ValueError as e:res={'status':'unsupported','error':str(e)}
                except Exception as e:res={'status':'crash','error':repr(e)}
                record={'name':row['name'],'mode':row['mode'],'optimization':'O3' if opt else 'raw','degree':degree,**res,'wall_ms':(time.perf_counter()-t)*1000}
                attacks.append(record);(out/'experiment.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
                print(json.dumps({k:record[k] for k in ('name','mode','optimization','degree','status','wall_ms')}),flush=True)
    check=subprocess.run(['node',str(p.HERE/'check.cjs'),str(out)],capture_output=True,text=True,timeout=300)
    (out/'check.stdout.log').write_text(check.stdout,encoding='utf8');(out/'check.stderr.log').write_text(check.stderr,encoding='utf8')
    if check.returncode:raise RuntimeError('Correctness failed')
    manifest['correctness']=json.loads(check.stdout)
    pins={str(f.relative_to(p.ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in out.rglob('*') if f.is_file() and f.name not in ('experiment.json','pins.json')}
    (out/'pins.json').write_text(json.dumps(pins,indent=2),encoding='utf8');(out/'experiment.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    print(json.dumps({'complete':True,'attacks':len(attacks),'calls':manifest['correctness']['total_calls']}),flush=True)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('output');a.add_argument('--seconds',type=float,default=60);a.add_argument('--dense-elimination',action='store_true');q=a.parse_args()
    if q.dense_elimination:attack.eliminate=attack.eliminate_dense
    run(q.output,q.seconds)
