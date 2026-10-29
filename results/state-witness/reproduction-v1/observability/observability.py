"""Keep introspection differences separate from original-interface witnesses."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent


def main(out):
    out.mkdir(parents=True,exist_ok=False);rows=[]
    for exposed in (False,True):
        name='reachable' if exposed else 'dormant'
        wat='''(module (memory 0 1) (data "x")
          (func (export "drop") data.drop 0)
          (func (export "read") (result i32) (i32.const 7))'''
        if exposed:wat+='(func (export "init") (memory.init 0 (i32.const 0) (i32.const 1) (i32.const 0)))'
        wat+=')';src=out/(name+'.wasm');dest=out/(name+'-observed.wasm')
        k.p.compile_wat(wat,src);meta=k.transform(src,dest)
        rows.append({'name':name,'source':src.name,'observed':dest.name,'manifest':meta})
    (out/'manifest.json').write_text(json.dumps({'rows':rows},indent=2))
    for name in ('observability.py','observability.cjs','observer.cjs'):shutil.copy2(HERE/name,out/name)
    r=subprocess.run(['node',str(HERE/'observability.cjs'),str(out.resolve())],capture_output=True,text=True,timeout=30)
    (out/'log.json').write_text(json.dumps({'code':r.returncode,'stdout':r.stdout,'stderr':r.stderr},indent=2))
    (out/'sha256.json').write_text(json.dumps({x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in out.iterdir()},indent=2))
    if r.returncode:raise RuntimeError(r.stderr)
    print(r.stdout)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('out',type=Path);main(a.parse_args().out)
