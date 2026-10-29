import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time
from compile import transform, tool
from attack import recover


def run(out):
    out.mkdir(parents=True,exist_ok=False);(out/'source').mkdir()
    for p in Path(__file__).parent.glob('*'):
        if p.is_file():shutil.copy2(p,out/'source'/p.name)
    x='(local.get 0)';y='(local.get 1)'
    fixtures={
        'mix':f'(i32.add (i32.xor {x} {y}) (i32.rotl {x} (i32.const 7)))',
        'carry':f'(i32.xor (i32.add {x} {y}) (i32.rotl {y} (i32.const 13)))',
        'mask':f'(i32.add (i32.and {x} (i32.rotl {y} (i32.const 3))) (i32.xor {y} (i32.const 1831565813)))'}
    rows=[];transforms=[]
    for family,expr in fixtures.items():
        wp=out/(family+'.wat');src=out/(family+'.wasm');dst=out/(family+'-alias.wasm')
        wp.write_text(f'(module (func (export "run") (param i32 i32) (result i32) {expr}))',encoding='utf-8')
        tool('wat2wasm',[wp,'-o',src],True);transforms.append({'family':family,**transform(src,dst)})
        for opt in ('raw','O2','O3'):
            for mode,p in [('plain',src),('alias',dst)]:
                if opt!='raw':
                    q=out/f'{family}-{mode}-{opt}.wasm';tool('wasm-opt',[p,'--all-features','-'+opt,'-o',q]);p=q
                row={'family':family,'mode':mode,'optimization':opt,'wasm':p.name,'bytes':p.stat().st_size,
                     'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
                if mode=='alias':
                    rp=out/f'{family}-recovered-{opt}.wasm'
                    try:
                        a=recover(p,rp);row['attack']={'status':'recovered','seconds':a['seconds'],'calls':a['calls']}
                        row['recovered']=rp.name
                    except (ValueError,KeyError,IndexError) as e:
                        row['attack']={'status':'unsupported','error':str(e)}
                rows.append(row)
    r={'rows':rows,'transforms':transforms,'source_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()
          for p in (out/'source').glob('*') if p.is_file()}}
    (out/'manifest.json').write_text(json.dumps(r,indent=2),encoding='utf-8')
    print(json.dumps({'conditions':len(rows),'attacks':[x['attack']['status'] for x in rows if 'attack' in x]}))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);a=ap.parse_args();run(a.output)
