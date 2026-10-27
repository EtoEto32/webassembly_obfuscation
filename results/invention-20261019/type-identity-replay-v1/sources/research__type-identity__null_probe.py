import argparse,json,subprocess
from pathlib import Path
import prototype as q
def main(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False);src=out/'source.wasm';wat=src.with_suffix('.wat')
    wat.write_text('(module (type $t (struct)) (global eqref (struct.new_default $t)) (func (export "run") (param i32 i32) (result i32) (local eqref) (ref.is_null (local.get 2))))',encoding='utf-8');q.tool('wasm-as',[wat,*q.FEATURES,'-o',src])
    dst=out/'lower.wasm';info=q.lower(src,dst);info.pop('output')
    values=[]
    for f in (src,dst):
        script='const fs=require("fs");const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[1]))).exports;console.log(e.run(0,0))'
        values.append(int(subprocess.check_output(['node','-e',script,str(f)],text=True)))
    q.save(out/'result.json',dict(values=values,match=values[0]==values[1],analysis=info,source_sha256=q.digest(Path(q.__file__))));print(values)
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('output');main(a.parse_args().output)
