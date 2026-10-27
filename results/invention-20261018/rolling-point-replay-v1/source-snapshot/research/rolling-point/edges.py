"""Additional valid-domain endpoints and independent RFC parameter check."""
import argparse
import json
from pathlib import Path
import subprocess
import transform as T


def run(directory):
    dest=directory/'edges';dest.mkdir(exist_ok=False)
    rows=[]
    for length,b in [(1,0),(1,255),(255,0),(255,255)]:
        pattern=bytes([b])*length;name=f'l{length}-b{b}'
        original=dest/(name+'-plain-raw.wasm');T.assemble(T.source(pattern),original)
        for method in ('plain','recompute','rolling'):
            raw=dest/(name+'-'+method+'-raw.wasm')
            if method!='plain':T.transform(original,raw,method)
            for opt in ('raw','O3'):
                out=raw if opt=='raw' else dest/(name+'-'+method+'-O3.wasm')
                if opt!='raw':
                    T.tool('wasm-opt',[raw,'-O3','--enable-multimemory','--enable-bulk-memory','-o',out])
                    T.tool('wasm-validate',[out])
                rows.append({'file':out.name,'pattern':pattern.hex()})
    (dest/'manifest.json').write_text(json.dumps({'prime':hex(T.P),'q':hex(T.Q),'entries':rows},indent=2))
    proc=subprocess.run(['node',str(Path(__file__).with_name('edges.cjs')),str(dest)],capture_output=True,text=True,check=True,timeout=120)
    print(proc.stdout.strip())


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directory',type=Path);run(p.parse_args().directory)
