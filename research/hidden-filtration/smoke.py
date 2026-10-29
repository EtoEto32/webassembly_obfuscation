import json
from pathlib import Path
import prototype as p


def fixtures():
    def make(steps, result, n=2):
        body=''.join(f'(local.set {n+i} {e})' for i,e in enumerate(steps))
        return f'(module (func (export "run") (param {" ".join(["i32"]*n)}) (result i32) (local {" ".join(["i32"]*len(steps))}) {body} {result}))'
    g=lambda i:f'(local.get {i})'
    op=lambda o,a,b:f'(i32.{o} {a} {b})'
    rot=lambda i,r:op('rotl',g(i),f'(i32.const {r})')
    base=[rot(0,3),rot(1,27),op('and',g(2),g(3)),op('xor',g(4),g(0)),rot(5,5),op('xor',g(5),g(1)),op('and',g(6),g(7))]
    yield 'mix8',make(base,op('xor',g(8),g(0)))
    base2=[rot(0,11),op('xor',g(0),g(1)),op('and',g(2),g(3)),op('or',g(4),g(1)),rot(5,7),op('xor',g(6),g(2)),op('and',g(7),g(5)),rot(8,13),op('xor',g(9),g(3))]
    yield 'select10',make(base2,op('or',g(10),g(0)))
    base3=[rot(0,3),rot(1,17),op('xor',g(2),g(3)),op('and',g(4),g(0)),rot(5,9),op('xor',g(6),g(1)),op('or',g(7),g(5)),op('and',g(8),g(4)),rot(9,23),op('xor',g(10),g(6)),op('and',g(11),g(8))]
    yield 'chain12',make(base3,op('xor',g(12),g(2)))


def build(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False);records=[]
    for name,text in fixtures():
        src=out/(name+'-plain.wasm');p.save(text,src)
        for mode in ('pipeline','linear','nonlinear'):
            dest=out/(name+'-'+mode+'.wasm')
            meta=p.transform(src,dest,mode)
            p.w.tool('wasm-opt',[dest,'-O3','--enable-bulk-memory','-o',dest.with_name(dest.stem+'-O3.wasm')])
            p.w.tool('wasm-validate',[dest.with_name(dest.stem+'-O3.wasm')])
            records.append(dict(name=name,mode=mode,path=str(dest.resolve()),**meta))
        p.w.tool('wasm-opt',[src,'-O3','-o',src.with_name(src.stem+'-O3.wasm')])
    (out/'manifest.json').write_text(json.dumps(records,indent=2),encoding='utf8')
    return records


if __name__=='__main__':
    import sys
    print(json.dumps(build(sys.argv[1]),indent=2))
