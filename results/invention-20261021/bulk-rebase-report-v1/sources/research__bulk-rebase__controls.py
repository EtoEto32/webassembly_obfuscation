"""Exhaustive small model, real-Wasm negative controls, and scope rejections."""
import itertools,json,subprocess,sys
from pathlib import Path
import prototype as p
src,out=map(Path,sys.argv[1:]);out.mkdir(parents=True,exist_ok=False);q=p.q
perm,key=p.configuration(7)
encode=lambda a:bytearray((perm[v&15]|(perm[v>>4]<<4))^key[i&15] for i,v in enumerate(a))
count=0
for size in range(1,9):
    for values in itertools.product((3,171),repeat=size):
        initial=bytes(values);physical=encode(initial)
        for n in range(size+1):
            for s in range(size-n+1):
                for d in range(size-n+1):
                    expected=bytearray(initial);expected[d:d+n]=initial[s:s+n]
                    actual=bytearray(physical);actual[d:d+n]=physical[s:s+n]
                    for i in range(n):actual[d+i]^=key[(s+i)&15]^key[(d+i)&15]
                    assert actual==encode(expected);count+=1
q.save(out/'model.json',dict(cases=count,mismatches=0,domain='all binary-valued states of 1..8 bytes; all valid source/dest/length triples; fixed bijection and public position mask'))

mutants=[]
base=q.read(src/'p1-bulk-scalar-s7-raw.wasm')
for name in ('omit-repair','repair-before-copy','forward-only','omit-upfront-bounds'):
    mode='direct-scalar' if name in ('forward-only','omit-upfront-bounds') else 'bulk-scalar'
    module=q.read(src/f'p1-{mode}-s7-raw.wasm');fs=[x for x in module[1:] if x[0]=='func'];index=len(fs)-2
    body=p.expr(p.copy_body(mode,perm,key,65536))
    if name=='omit-repair':body=['func',['param','i32','i32','i32'],['memory.copy',['local.get','0'],['local.get','1'],['local.get','2']]]
    elif name=='repair-before-copy':
        cp=next(x for x in body[1:] if isinstance(x,list) and x[0]=='memory.copy');body.remove(cp);body.append(cp)
    elif name=='forward-only':
        # Last top-level if is the copy-direction selection, not the bounds check.
        direction=body[-1];assert direction[0]=='if' and direction[1][0]=='i32.le_u';body[-1:]=direction[2][1:]
    else:
        guard=next(x for x in body[1:] if isinstance(x,list) and x[0]=='if');assert guard[1][0]=='i32.or';body.remove(guard)
    module[module.index(fs[index])]=body;target=out/(name+'.wasm');q.compile(q.w.emit(module),target)
    mutants.append(dict(file=target.name,name=name,d=0 if name=='omit-upfront-bounds' else 1,s=65535 if name=='omit-upfront-bounds' else 0,n=2 if name=='omit-upfront-bounds' else 31))
q.save(out/'mutants.json',mutants)
subprocess.run(['node',str(Path(__file__).with_name('controls.cjs')),str(out)],check=True,timeout=60)

cases={
 'export-memory':'(module (memory (export "memory") 1 1))',
 'grow':'(module (memory 1 1) (func (drop (memory.grow (i32.const 0)))))',
 'wide-load':'(module (memory 1 1) (func (result i32) (i32.load (i32.const 0))))',
 'nonzero-offset':'(module (memory 1 1) (func (result i32) (i32.load8_u offset=1 (i32.const 0))))',
 'import':'(module (import "h" "f" (func)) (memory 1 1))',
 'three-pages':'(module (memory 3 3))',
 'shared':'(module (memory 1 1 shared))',
 'memory-fill':'(module (memory 1 1) (func (memory.fill (i32.const 0) (i32.const 0) (i32.const 1))))',
}
rejections=[]
for name,text in cases.items():
    f=out/(name+'.wasm')
    if name=='shared':
        f.with_suffix('.wat').write_text(text,encoding='utf-8')
        q.w.tool('wat2wasm',[f.with_suffix('.wat'),'--enable-threads','-o',f]);q.w.tool('wasm-validate',[f,'--enable-threads'])
        m=q.w.parse(q.w.tool('wasm2wat',[f,'--enable-threads','--fold-exprs','--no-debug-names']))
        try:p.profile(m);raise AssertionError('accepted '+name)
        except q.Unsupported as e:rejections.append(dict(name=name,stage='profile on valid threads-enabled input; default CLI validator also excludes threads',reason=str(e)))
    else:
        q.compile(text,f)
        try:p.transform(f,out/(name+'-transformed.wasm'));raise AssertionError('accepted '+name)
        except q.Unsupported as e:rejections.append(dict(name=name,stage='CLI transformation',reason=str(e)))
q.save(out/'rejections.json',rejections)
print(json.dumps(dict(model_cases=count,mutants=len(mutants),rejections=len(rejections))))
