import argparse,subprocess
from pathlib import Path
import prototype as q
def main(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False);rows=[[1,0,0],[0,1,1]]
    src=out/'source.wasm';q.p.compile(q.packed(rows),src)
    for mode in ('plain','branch','gc','groups'):
        dst=out/(mode+'.wasm');print(q.transform(src,dst,mode,2,4))
        print(q.lower(dst,out/(mode+'-lower.wasm'))|{'output':None})
        print(subprocess.check_output(['node','-e','const fs=require("fs");const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[1]))).exports;console.log([e.run(0,1),e.run(1,1),e.run(0,2)])',str(dst)],text=True))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('output');main(a.parse_args().output)
