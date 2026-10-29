"""Attempt to obtain the same quotient using the existing wasm-merge linker."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time
import transform as t

HERE=Path(__file__).resolve().parent


def main(source,reference,out):
    out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
    for name in ('merge-baseline.py','merge-baseline.cjs','plan.md'):shutil.copy2(HERE/name,out/'sources'/name)
    shutil.copy2(reference/'reference.json',out/'reference.json');mf=json.loads((source/'manifest.json').read_text());shutil.copy2(source/'manifest.json',out/'manifest.json')
    records=[]
    try:
        for rec in mf['records']:
          folder=out/rec['folder'];folder.mkdir();src=folder/'original.wasm';shutil.copy2(source/rec['folder']/'original.wasm',src)
          for alias in rec['aliases']:
            p=alias['partition'];stem='merge'+str(alias['id']);wp=folder/(stem+'-wrapper.wat');wrapper=wp.with_suffix('.wasm');dest=folder/(stem+'.wasm')
            imports=' '.join('(import "host" "m%d" (memory 1 3))'%i for i in alias['representatives'])
            exports=' '.join('(export "m%d" (memory %d))'%(i,p[i]) for i in range(rec['n']))
            wp.write_text('(module '+imports+' '+exports+')',encoding='utf8');t.w.tool('wat2wasm',[wp,'-o',wrapper])
            cmd=[t.w.BINARYEN/'wasm-merge.exe',wrapper,'env',src,'app','--enable-multimemory','--enable-bulk-memory','--enable-bulk-memory-opt','--skip-export-conflicts','-o',dest]
            start=time.perf_counter();r=subprocess.run(list(map(str,cmd)),capture_output=True,text=True,timeout=30);elapsed=time.perf_counter()-start
            row={'fixture':rec['folder'],'alias':alias['id'],'command':list(map(str,cmd)),'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'seconds':elapsed}
            if r.returncode:raise RuntimeError(row)
            t.w.tool('wasm-validate',[dest]);row['bytes']=dest.stat().st_size;records.append(row)
        (out/'builds.json').write_text(json.dumps(records,indent=2),encoding='utf8')
        cmd=['node',str(HERE/'merge-baseline.cjs'),str(out)];r=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
        (out/'run.json').write_text(json.dumps({'command':cmd,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr},indent=2),encoding='utf8')
        if r.returncode:raise RuntimeError(r.stderr)
        print(r.stdout)
    finally:
        (out/'sha256.json').write_text(json.dumps({str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file() and p.name!='sha256.json'},indent=2),encoding='utf8')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('reference',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();main(a.source.resolve(),a.reference.resolve(),a.output.resolve())
