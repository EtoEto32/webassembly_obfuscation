import argparse,json,re,struct,subprocess,shutil
from pathlib import Path
import prototype as q
import recover as r
from run import save
p=q.p;HERE=Path(__file__).resolve().parent

def main(main,out):
    main=Path(main);out=Path(out);out.mkdir(parents=True,exist_ok=False);allowed=r.profiles();extra=[]
    snap=out/'sources';snap.mkdir()
    for f in HERE.glob('*'):
        if f.suffix in ('.py','.cjs'):shutil.copyfile(f,snap/f.name)
    expressions={op:f'({op} '+ ' '.join(f'(local.get {j})' for j in range(q.ARITY[op]))+')' for op in q.OPS}
    expressions.update(argument='(local.get 0)',constant='(i32.const -2147483648)',mutable='(local.set 0 (i32.xor (local.get 0) (local.get 1))) (i32.sub (local.get 0) (local.get 2))',zero_local='(i32.add (local.get 3) (local.get 1))')
    for label,body in expressions.items():
        name=label.replace('.','_');src=out/(name+'-source.wasm');extra_local='(local i32)' if label=='zero_local' else ''
        p.compile(f'(module (func (export "run") (param i32 i32 i32) (result i32) {extra_local} {body}))',src)
        raw=out/(name+'-raw.wasm');q.transform(src,raw,47);target=out/(name+'-O3.wasm');q.optimize(raw,target)
        dst=out/(name+'-recovered.wasm');attack=r.recover(target,dst,allowed)
        extra.append(dict(source=src.name,target=target.name,recovered=dst.name,arity=3,attack=attack))
    src=out/'arity16-source.wasm';p.compile('(module (func (export "run") (param '+('i32 '*16)+') (result i32) (i32.xor (local.get 0) (i32.add (local.get 8) (local.get 15)))))',src)
    target=out/'arity16-raw.wasm';q.transform(src,target,4);dst=out/'arity16-recovered.wasm';attack=r.recover(target,dst,allowed);extra.append(dict(source=src.name,target=target.name,recovered=dst.name,arity=16,attack=attack))
    # Deliberately wrong runtime: allow consumers before their dependencies publish.
    src=out/'negative-source.wasm';p.compile('(module (func (export "run") (param i32 i32 i32) (result i32) (i32.mul (i32.add (local.get 0) (i32.const 1)) (i32.const 3))))',src)
    n,_,root=p.read(src);data,_=q.graph(root,n,37);text=q.scheduler(data,True)
    line=next(x for x in text.splitlines() if '(i32.eqz (i32.and (i32.and' in x)
    wrong=out/'negative-no-dependency.wasm';p.compile(text.replace(line,'  (nop)'),wrong)
    rejects=[]
    try:r.decode(wrong.read_bytes(),allowed);raise AssertionError('wrong runtime accepted')
    except ValueError as e:rejects.append(dict(case='changed-runtime',reason=str(e)))
    cyc=bytearray(data);root_id=struct.unpack_from('<I',cyc,8)[0]
    for offset in (4,12):struct.pack_into('<I',cyc,q.BASE+32*root_id+offset,root_id)
    cyclic=out/'negative-cycle.wasm';p.compile(q.scheduler(cyc,True),cyclic)
    try:r.decode(cyclic.read_bytes(),allowed);raise AssertionError('cycle accepted')
    except ValueError as e:
        assert 'cyclic dependency' in str(e)
        rejects.append(dict(case='cyclic-data',reason=str(e)))
    unsupported={
      'division':'(module (func (export "run") (param i32) (result i32) (i32.div_u (local.get 0) (i32.const 2))))',
      'memory':'(module (memory 1) (func (export "run") (param i32) (result i32) (i32.load (local.get 0))))',
      'loop':'(module (func (export "run") (param i32) (result i32) (loop (nop)) (local.get 0)))',
      'import':'(module (import "e" "f" (func)) (func (export "run") (param i32) (result i32) (local.get 0)))'}
    for name,wat in unsupported.items():
        f=out/(name+'-unsupported.wasm');p.compile(wat,f)
        try:q.transform(f,out/(name+'-unexpected.wasm'));raise AssertionError(name+' accepted')
        except ValueError as e:rejects.append(dict(case=name,reason=str(e)))
    save(out/'extra.json',extra);save(out/'rejections.json',rejects)
    subprocess.run(['node',str(HERE/'verify.cjs'),str(main),str(out)],check=True,timeout=120)
    expected=json.loads((out/'wabt-expected.json').read_text());wabt=[]
    for index,item in enumerate(expected):
        src=Path(item['path']);m=p.w.parse(p.w.tool('wasm2wat',[src,'--enable-all','--fold-exprs','--no-debug-names']))
        for j,e in enumerate(m):
            if isinstance(e,list) and e[0]=='import':m[j]=['memory','1','1','shared']
        idx=next(e[2][1] for e in m[1:] if isinstance(e,list) and e[0]=='export' and e[1]=='"run"')
        for i,a in enumerate(item['inputs']):
            body=f'(func (export "check{i}") (result i32) (call {idx} '+ ' '.join(f'(i32.const {v})' for v in a)+'))'
            m.append(p.w.parse('(module '+body+')')[1])
        f=out/f'wabt-{index}.wasm';p.compile(p.w.emit(m),f)
        log=p.w.tool('wasm-interp',[f,'--enable-threads','--run-all-exports']);(out/f'wabt-{index}.log').write_text(log)
        got=[int(x) for x in re.findall(r'check\d+\(\) => i32:(\d+)',log)];want=[x&0xffffffff for x in item['expected']]
        wabt.append(dict(file=str(src),expected=want,actual=got,match=got==want))
    save(out/'wabt.json',wabt)
    assert all(x['match'] for x in wabt)
    save(out/'summary.json',dict(extra_targets=len(extra),wabt_files=len(wabt),wabt_checks=sum(len(x['actual']) for x in wabt),all_wabt_match=True,rejected=len(rejects)))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('main');a.add_argument('output');v=a.parse_args();main(v.main,v.output)
