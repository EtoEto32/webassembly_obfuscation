import argparse,hashlib,json,shutil
from pathlib import Path
import prototype as p
def main(out):
    out.mkdir(parents=True,exist_ok=False);shutil.copy2(__file__,out/'boundary.py');shutil.copy2(Path(__file__).with_name('prototype.py'),out/'prototype.py')
    cases={
      'import':'(import "h" "f" (func)) (memory 1 2)',
      'start':'(memory 1 2) (func) (start 0)',
      'memory-export':'(memory (export "memory") 1 2)',
      'global-export':'(memory 1 2) (global (export "g") (mut i32) (i32.const 0))',
      'unbounded':'(memory 1)',
      'externref-table':'(memory 1 2) (table 1 2 externref)',
      'reference-signature':'(memory 1 2) (func (export "ref") (param funcref))',
      'reference-global':'(memory 1 2) (global funcref (ref.null func))',
      'large-cap':'(memory 1 257)'}
    rows=[]
    for name,wat in cases.items():
        src=out/(name+'.wasm');p.compile_wat('(module '+wat+')',src)
        try:p.transform(src,out/(name+'-bad.wasm'))
        except ValueError as e:rows.append({'case':name,'validWasm':True,'rejected':True,'reason':str(e)})
        else:raise AssertionError('unsupported accepted: '+name)
    result={'rows':rows,'rejected':len(rows)};(out/'results.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    (out/'sha256.json').write_text(json.dumps({x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in out.iterdir() if x.is_file()},indent=2),encoding='utf8');print(json.dumps({'rejected':len(rows)}))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('out',type=Path);main(a.parse_args().out)
