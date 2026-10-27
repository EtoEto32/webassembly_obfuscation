import copy
import json
from pathlib import Path
import re
import sys
import prototype as p
import native

def main(base,nativebase,out):
    base=Path(base);nativebase=Path(nativebase);out=Path(out);out.mkdir(parents=True,exist_ok=False);wabt=0;replays=0;controls=[]
    for name in ('and3','majority3','mux3'):
        r=p.read(base/(name+'-rotor.wasm'))
        for mode in ('native','tight'):
            g=copy.deepcopy(r)
            if mode=='tight':g['bound']=max(len(p.simulate(r,x)[1]) for x in range(8))
            for opt in ('raw','O3'):
                src=nativebase/(name+'-'+mode+('' if opt=='raw' else '-O3')+'.wasm');replay=out/(src.stem+'-replay.wasm');p.save(native.render(g),replay)
                if opt=='O3':p.w.tool('wasm-opt',[replay,'-O3','-o',replay.with_suffix('.opt.wasm')]);replay=replay.with_suffix('.opt.wasm')
                assert replay.read_bytes()==src.read_bytes();replays+=1
                mod=p.w.parse(p.w.tool('wasm2wat',[src,'--fold-exprs']));args=[(0,0,0),(-1,-1,-1),(0xaaaaaaaa,0xcccccccc,0xf0f0f0f0),(0x12345678,0x87654321,0xfafafafa)]
                for j,xs in enumerate(args):mod.append(p.w.parse(f'(module (func (export "probe{j}") (result i32) (call 0 '+' '.join(f'(i32.const {x})' for x in xs)+')))')[1])
                probe=out/(src.stem+'-interpreter.wasm');p.save(p.w.emit(mod),probe);raw=p.w.tool('wasm-interp',[probe,'--run-all-exports']);(out/(src.stem+'-interpreter.txt')).write_text(raw)
                found=[int(v) for v in re.findall(r'probe\d+\(\) => i32:(\d+)',raw)];assert len(found)==4
                for (a,b,c),y in zip(args,found):
                    expected={'and3':a&b&c,'majority3':(a&b)|(a&c)|(b&c),'mux3':(a&b)|(~a&c)}[name]&p.MASK
                    assert y==expected;wabt+=1
    for label,text in [('cross-lane','(i32.rotl (local.get 0) (i32.const 1))'),('partial-mask','(i32.and (local.get 0) (i32.const 255))'),('symbolic-add','(i32.add (local.get 0) (i32.const 1))')]:
        src=out/(label+'.wasm');p.save(f'(module (func (export "run") (param i32) (result i32) {text}))',src)
        try:native.recover(src)
        except ValueError:controls.append(label+' rejected')
        else:raise AssertionError(label+' accepted')
    result={'byte_replays':replays,'wabt_calls':wabt,'negative_controls':controls};(out/'audit.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))

if __name__=='__main__':main(*sys.argv[1:])
