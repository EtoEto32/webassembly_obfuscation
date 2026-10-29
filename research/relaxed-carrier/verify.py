"""Second-engine, algebra, and refusal controls; separate from timed runs."""
import argparse
import json
from pathlib import Path
import random
import prototype as p
from run import save,command

def ref(model,a,b,c):
    m=p.U32;a&=m;b&=m;c&=m
    def rot(x,k):return ((x<<k)|(x>>(32-k)))&m
    if model=='majority':return (a&b)|(c&(a|b))
    acc=0
    for r in range(int(model[3:])):
        t=((a&b)^rot(c,(r*7+3)&31)^((r+1)*0x9e3779b9)^acc)&m
        a=(b^(t>>(r%5+1)))&m;b=(c|(t<<(r%3+1)))&m;c=(t^rot(a,(r*3+5)&31))&m;acc=t>>7
    return a^b^c
def main():
    ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    manifest=json.loads((a.input/'manifest.json').read_text());cases=[(0,0,0),(1,2,3),(-1,-1,-1),(0x80000000,0x7fffffff,0),(0x55aa55aa,0xabcdef01,0x12345678),(0xffffffff,1,0x80000000)]
    checks=[]
    for entry in manifest['files']:
        mod=p.read(a.input/entry['path'])
        for i,values in enumerate(cases):mod.append(['func',['export','"check'+str(i)+'"'],['result','i32'],['call','0',*[p.c(v) for v in values]]])
        target=a.output/entry['path'];p.compile_wat(p.w.emit(mod),target);text=p.w.tool('wasm-interp',[target,'--run-all-exports']);target.with_suffix('.log').write_text(text,encoding='utf-8')
        for i,values in enumerate(cases):
            expected=ref(entry['model'],*values)
            if 'check'+str(i)+'() => i32:'+str(expected)+'\n' not in text:raise AssertionError((entry,i,expected,text))
        checks.append(dict(path=entry['path'],calls=len(cases)))
    save(a.output/'interpreter.json',dict(engine='WABT 1.0.42',binaries=len(checks),calls=len(checks)*len(cases),mismatches=0,records=checks))
    tested=0;wrong=0;rng=random.Random(20261019)
    triples=[(x,y,m) for x in range(16) for y in range(16) for m in range(16)]+[(rng.getrandbits(32),rng.getrandbits(32),rng.getrandbits(32)) for _ in range(5000)]
    for x,y,m in triples:
        z=x^m;v=y^m
        for expected,encoded in ((x&y,(z&v)^((z^v)&m)),(x|y,(z|v)^((z^v)&m)),(x^y,z^v^m)):
            assert encoded^m==expected;tested+=1
        wrong+=((z&v)^m)!=(x&y)
        for k in (0,1,7,16,31,32,33):
            k&=31
            for fun in (lambda q:(q<<k)&p.U32,lambda q:q>>k,lambda q:((q<<k)|(q>>(32-k)))&p.U32,lambda q:((q>>k)|(q<<(32-k)))&p.U32):
                assert fun(z)^fun(m)==fun(x);tested+=1
    save(a.output/'algebra.json',dict(triples=len(triples),identity_checks=tested,mismatches=0,wrong_and_failures=wrong,seed=20261019))
    # Pure range controls do not permit arbitrary operand erasure.
    vec=lambda n:['v128.const','i32x4',*([hex(n)]*4)]
    def wrap(expr,local=None):return ['module',['func',['param','i32','i32','i32'],['result','i32'],*([['local','v128']] if local else []),expr],['export','"run"',['func','0']]]
    def swizzle(index):return ['i32x4.extract_lane','0',['i8x16.relaxed_swizzle',vec(p.U32),index]]
    controls=[]
    for name,index,want in [('in_range',vec(0),0),('unknown',p.op('i32x4.splat',p.get(0)),0),('out_of_range',vec(0x10101010),1)]:
        mod=wrap(swizzle(index));_,found=p.simplify(mod);assert found==want;controls.append(dict(name=name,proven=found));p.compile_wat(p.w.emit(mod),a.output/(name+'.wasm'))
    badsources=[('division',wrap(p.op('i32.div_u',p.get(0),p.get(1)))),('memory',['module',['memory','1'],*wrap(['i32.load',p.get(0)])[1:]])]
    for name,mod in badsources:
        path=a.output/(name+'.wasm');p.compile_wat(p.w.emit(mod),path)
        for action in ('transform','simplify'):
            try:
                if action=='transform':p.transform(path,a.output/(name+'.transformed.wasm'),'relaxed')
                else:p.simplify(p.read(path))
            except ValueError as error:controls.append(dict(name=name,action=action,rejected=str(error)))
            else:raise AssertionError('Unsafe acceptance')
    # Directly observable relaxed value has multiple permitted values. Its
    # refinement is NOT a general deterministic equivalence theorem.
    raw=p.read(a.output/'out_of_range.wasm');reduced,count=p.simplify(raw);p.compile_wat(p.w.emit(reduced),a.output/'observable-refinement.wasm')
    direct=command(['node','-e',"const fs=require('fs');let values=process.argv.slice(1).map(p=>new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(p))).exports.run(0,0,0));console.log(JSON.stringify(values));",a.output/'out_of_range.wasm',a.output/'observable-refinement.wasm'])
    controls.append(dict(name='observable_relaxed_value',observed_node_values=direct,permitted_original_lane_values=[0,255],refined_lane_value=0,full_result_set_equivalent=False))
    save(a.output/'controls.json',controls)
    print(json.dumps(dict(engine_calls=len(checks)*len(cases),algebra_checks=tested,wrong_and_failures=wrong,controls=len(controls),mismatches=0)))
if __name__=='__main__':main()
