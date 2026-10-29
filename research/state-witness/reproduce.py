"""Run the saved experiments from source into a fresh output directory."""
import argparse,hashlib,json,shutil,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]


def main(out):
    out=out.resolve();out.mkdir(parents=True,exist_ok=False);logs=[]
    shutil.copy2(__file__,out/'reproduce.py')
    tasks=[('run.py',[out/'probe']),('cross.py',[out/'probe',out/'cross']),('boundary.py',[out/'boundary']),
           ('observability.py',[out/'observability']),('spec-run.py',[ROOT/'.tools/state-witness-spec',out/'spec']),
           ('bench.py',[out/'probe',out/'performance'])]
    try:
        for name,args in tasks:
            cmd=[sys.executable,str(HERE/name),*map(str,args)];start=time.perf_counter()
            r=subprocess.run(cmd,capture_output=True,text=True,encoding='utf8',timeout=240)
            logs.append({'command':cmd,'code':r.returncode,'seconds':time.perf_counter()-start,'stdout':r.stdout,'stderr':r.stderr})
            (out/'stages.json').write_text(json.dumps(logs,indent=2),encoding='utf8')
            if r.returncode:raise RuntimeError(r.stderr)
            print(json.dumps({'stage':name,'passed':True}),flush=True)
    finally:
        hashes={p.relative_to(out).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()}
        (out/'sha256.json').write_text(json.dumps(hashes,indent=2),encoding='utf8')


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('out',type=Path);main(a.parse_args().out)
