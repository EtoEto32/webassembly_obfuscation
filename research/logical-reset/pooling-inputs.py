import argparse,hashlib,json,shutil
from pathlib import Path
import prototype as p
from fixtures import fixture

def main(out):
    out.mkdir(parents=True,exist_ok=False);rows=[]
    for file in ('pooling-inputs.py','prototype.py','fixtures.py'):
        shutil.copy2(Path(__file__).with_name(file),out/file)
    for name,pages in [('small',1),('medium',4),('large',64)]:
        original=out/(name+'-source.wasm')
        p.compile_wat(fixture(name,pages,max(pages+1,8),4)['wat'],original)
        for mode in ('source','full','plain'):
            binary=original if mode=='source' else out/(name+'-'+mode+'.wasm')
            if mode!='source':p.transform(original,binary,mode)
            for job in ('work-only','grow-drop'):
                if mode=='plain' and job!='work-only':continue
                m=p.read(binary)
                exports={x[1][1:-1]:x[2][1] for x in m[1:] if x[0]=='export'}
                body=[]
                if mode!='source':body.append(f'(call {exports["__lr_reset"]})')
                if job=='grow-drop':
                    body += [f'(drop (call {exports["grow"]} (i32.const 1)))',f'(drop (call {exports["tgrow"]} (i32.const 3)))',
                             f'(call {exports["init"]} (i32.const 0) (i32.const 0) (i32.const 3))',
                             f'(call {exports["tinit"]} (i32.const 0) (i32.const 0) (i32.const 3))',
                             f'(call {exports["ddrop"]})',f'(call {exports["edrop"]})']
                body.append(f'(call {exports["work"]} (local.get 0))')
                # Retain the same existing API on both sides to avoid artificial DCE.
                m.append(p.expr('(func (export "__request") (param i32) (result i32) '+' '.join(body)+')'))
                raw=out/f'{name}-{job}-{mode}-request.wasm';p.compile_wat(p.w.emit(m),raw)
                opt=raw.with_name(raw.stem+'-O3.wasm')
                p.tool('wasm-opt',[raw,'-O3','--enable-bulk-memory','--enable-reference-types','-o',opt])
                rows.append({'fixture':name,'pages':pages,'job':job,'mode':mode,'file':opt.name,'bytes':opt.stat().st_size})
    (out/'manifest.json').write_text(json.dumps({'rows':rows},indent=2),encoding='utf8')
    (out/'sha256.json').write_text(json.dumps({x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in out.iterdir() if x.is_file()},indent=2),encoding='utf8')
    print(json.dumps({'rows':len(rows)}))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('out',type=Path);main(a.parse_args().out)
