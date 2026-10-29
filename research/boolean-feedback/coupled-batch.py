import json
from pathlib import Path
import subprocess
import sys
from shared import h,load
attack=load('bf_coupled_batch_attack',Path(__file__).with_name('coupled-attack.py'))


def main(base,out):
    base=Path(base).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);rows=[]
    for name in ('mix8','select10','chain12'):
        for mode in ('feedback','coupled'):
            for opt in ('','-O3'):
                source=base/(name+'-'+mode+opt+'.wasm');dest=out/(source.stem+'-recovered.wasm');result=attack.run(source,dest)
                rows.append({'name':name,'mode':mode,'optimization':opt or 'raw',**result});(out/'attacks.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows[-1]),flush=True)
    result=subprocess.run(['node',str(h.HERE/'check.cjs'),str(out)],capture_output=True,text=True,timeout=180);(out/'check.stdout.log').write_text(result.stdout);(out/'check.stderr.log').write_text(result.stderr)
    if result.returncode:raise RuntimeError(result.stderr)
    print(result.stdout)

if __name__=='__main__':main(*sys.argv[1:])
