"""Reproduce six public-binary word attacks and independent JS checks."""
import json
from pathlib import Path
import subprocess
import sys
from shared import h,load
attack=load('bf_word_batch_attack',Path(__file__).with_name('word-attack.py'))


def main(base,out):
    base=Path(base).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);rows=[]
    for name in ('muladd','square','mixcarry'):
        for opt in ('','-O3'):
            source=base/(name+'-feedback-0'+opt+'.wasm');dest=out/(name+opt+'-recovered.wasm')
            result=attack.run(source,dest);rows.append({'name':name,'optimization':opt or 'raw',**result})
            (out/'attacks.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows[-1]),flush=True)
    p=subprocess.run(['node',str(Path(__file__).with_name('word-check.cjs')),str(out)],capture_output=True,text=True,timeout=180)
    (out/'check.stdout.log').write_text(p.stdout);(out/'check.stderr.log').write_text(p.stderr)
    if p.returncode:raise RuntimeError(p.stderr)
    print(p.stdout)

if __name__=='__main__':main(*sys.argv[1:])
