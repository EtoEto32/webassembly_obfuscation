import argparse,json,re,subprocess
from pathlib import Path
import prototype as q
from run import save
p=q.p;HERE=Path(__file__).resolve().parent

def main(main,out):
    main=Path(main);out=Path(out);out.mkdir(parents=True,exist_ok=False);rows=json.loads((main/'manifest.json').read_text());wabt=[];files=[]
    steps=[(0,1,1,0),(2,0,2,3),(65535,0,2,65535),(0,0,0,0)]
    for row in rows:
        src=main/row['file'];m=p.w.parse(p.w.tool('wasm2wat',[src,'--fold-exprs','--no-debug-names']))
        exports={e[1]:e[2][1] for e in m[1:] if e[0]=='export'}
        for i,(d,s,n,a) in enumerate(steps):
            f=f'(func (export "check{i}") (result i32) (call {exports[chr(34)+"copy"+chr(34)]} (i32.const {d}) (i32.const {s}) (i32.const {n})) (call {exports[chr(34)+"read"+chr(34)]} (i32.const {a})))'
            m.append(p.w.parse('(module '+f+')')[1])
        dst=out/row['file'];p.compile(p.w.emit(m),dst);files.append(str(dst.resolve()))
        log=p.w.tool('wasm-interp',[dst,'--run-all-exports']);(out/(dst.stem+'.log')).write_text(log,encoding='utf-8')
        actual=[]
        for i in range(4):
            line=next(x for x in log.splitlines() if x.startswith(f'check{i}()'))
            values=re.findall(r'i32:(\d+)',line);actual.append(int(values[0]) if values else 'trap')
        wabt.append(dict(file=dst.name,actual=actual))
    save(out/'files.json',files)
    script='''const fs=require('fs');let out=[];for(const file of JSON.parse(fs.readFileSync(process.argv[1]))){const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(file))).exports;let a=[];for(let i=0;i<4;i++){try{a.push(e['check'+i]()>>>0)}catch(x){if(!(x instanceof WebAssembly.RuntimeError))throw x;a.push('trap')}}out.push(a)}console.log(JSON.stringify(out));'''
    expected=json.loads(subprocess.check_output(['node','-e',script,str(out/'files.json')],text=True))
    for row,want in zip(wabt,expected):row.update(expected=want,match=row['actual']==want)
    save(out/'cross-engine.json',wabt);assert all(x['match'] for x in wabt)
    # Exhaustively validate decoder identities over the pair alphabet.
    correct=0
    for a in range(256):
        for b in range(256):
            encoded=q.encode(bytes([a,b]),'coupled');assert q.encode(encoded,'coupled')==bytes([a,b]);correct+=1
    for x in range(256):
        y=q.rol((5*x)&255,3);assert (q.rol(y,5)*205)&255==x
    save(out/'summary.json',dict(wabt_files=len(wabt),cross_engine_calls=4*len(wabt),all_match=True,pair_involution_checks=correct,uniform_inverse_checks=256))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('main');a.add_argument('output');v=a.parse_args();main(v.main,v.output)
