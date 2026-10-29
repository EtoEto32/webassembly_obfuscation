import argparse,json,platform,re,subprocess
from pathlib import Path
import prototype as p
import attack
import run as runner

def oracle(name,xyz):
    x,y,z=xyz
    if name=='arith':s=(x+y)&p.MASK;return ((s^z)*s)&p.MASK
    if name=='blend':return (((x&y)+z)&p.MASK)^y
    return (((x*y+y)&p.MASK)|z)&p.MASK

def run(main,output):
    main,out=Path(main).resolve(),Path(output).resolve();out.mkdir(parents=True,exist_ok=False)
    rows=json.loads((main/'manifest.json').read_text());replay=[];interpreter=[];controls=[]
    probes=[(0,0,0),(1,2,3),(0xffffffff,0xffffffff,0xffffffff),(0x80000000,1,7),(0x7fffffff,0x80000000,65535),(2,2,2),(0,7,0),(255,65535,3)]
    for row in rows:
        src=main/row['file'];dst=out/row['file']
        if row['negative']:
            try:attack.extract(src)
            except ValueError as e:controls.append(dict(file=src.name,status='rejected',reason=str(e)))
            else:raise AssertionError('bad accepted')
            continue
        if row['mode'].endswith('-recovered'):
            wat,_=attack.extract(main/row['file'].replace('.recovered.wasm','.wasm'));p.compile_wat(wat,dst)
        elif row['opt']=='O3':p.tool('wasm-opt',[out/row['file'].replace('.O3.wasm','.raw.wasm'),'-O3','-o',dst])
        elif row['mode']=='plain':
            body=runner.FIXTURES[row['name']];p.compile_wat(f'(module (func (export "run") (param i32 i32 i32) (result i32) (local i32 i32) {body}))',dst)
        else:p.transform(main/f'{row["name"]}.plain.raw.wasm',dst,row['mode'])
        assert src.read_bytes()==dst.read_bytes();replay.append(dict(file=src.name,sha256=p.digest(src),byte_equal=True))
        mod=p.w.read(src);idx=next(x[2][1] for x in mod[1:] if x[0]=='export' and x[1]=='"run"')
        for k,xyz in enumerate(probes):
            args=' '.join('(i32.const '+str(x)+')' for x in xyz)
            mod.append(p.w.sx.parse(f'(module (func (export "probe{k}") (result i32) (call {idx} {args})))')[1])
        wrapper=out/(src.stem+'.probe.wasm');p.compile_wat(p.w.sx.emit(mod),wrapper)
        text=p.tool('wasm-interp',[wrapper,'--run-all-exports']);found=[int(v)&p.MASK for v in re.findall(r'probe\d+\(\) => i32:(-?\d+)',text)]
        assert found==[oracle(row['name'],a) for a in probes],text
        interpreter.append(dict(file=src.name,calls=len(probes),outputs=found))
    # Two more initialized states, separately counted from main inputs.
    extra=[]
    for name in runner.FIXTURES:
        nodes,result=p.source(main/f'{name}.plain.raw.wasm')
        for initial in (0xdeadbeef,0xffffffff):
            dst=out/f'{name}.initial-{initial}.wasm';p.compile_wat(p.emit(nodes,result,'rotated',initial),dst)
            script="const fs=require('fs');const ex=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[1]))).exports;console.log(JSON.stringify(JSON.parse(process.argv[2]).map(a=>ex.run(...a)>>>0)))"
            r=subprocess.run(['node','-e',script,str(dst),json.dumps(probes)],capture_output=True,text=True,check=True)
            got=json.loads(r.stdout);assert got==[oracle(name,a) for a in probes]
            extra.append(dict(file=dst.name,initial=initial,calls=len(probes),outputs=got))
    base=(main/'arith.rotated.raw.wat').read_text()
    short=out/'short-bound.wasm';p.compile_wat(base.replace('(i32.const 96)','(i32.const 95)'),short)
    try:attack.extract(short)
    except ValueError as e:controls.append(dict(file=short.name,status='rejected',reason=str(e),semantic_failure_claimed=False))
    else:raise AssertionError('short bound accepted')
    for name,body in [('division','(i32.div_u (local.get 0) (local.get 1))'),('internal-rotate','(i32.rotl (i32.add (local.get 0) (local.get 1)) (i32.const 7))')]:
        dst=out/('source-'+name+'.wasm');p.compile_wat(f'(module (func (export "run") (param i32 i32 i32) (result i32) {body}))',dst)
        try:p.source(dst)
        except ValueError as e:controls.append(dict(file=dst.name,status='rejected',reason=str(e)))
        else:raise AssertionError('unsupported source accepted')
    p.save(out/'replay.json',replay);p.save(out/'interpreter.json',interpreter);p.save(out/'initials.json',extra);p.save(out/'controls.json',controls)
    p.save(out/'environment.json',dict(platform=platform.platform(),python=platform.python_version(),processor=platform.processor(),node=subprocess.check_output(['node','--version'],text=True).strip(),wabt=p.tool('wasm-validate',['--version']).strip(),binaryen=p.tool('wasm-opt',['--version']).strip()))
    runner.pin(out);print(json.dumps(dict(regenerated=len(replay),interpreter_calls=sum(x['calls'] for x in interpreter),extra_initial_calls=sum(x['calls'] for x in extra),controls=len(controls))))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('main');ap.add_argument('output');a=ap.parse_args();run(a.main,a.output)
