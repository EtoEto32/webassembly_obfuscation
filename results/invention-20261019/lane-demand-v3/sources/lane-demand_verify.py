import argparse
import copy
import json
from pathlib import Path
import random
import prototype as p
import attack
from run import save,command

def eval_expr(e,x,y):
    op=e[0]
    if op=='local.get':return (x,y)[int(e[1])]&p.MASK
    if op=='i32.const':return int(e[1],0)&p.MASK
    a=eval_expr(e[1],x,y);b=eval_expr(e[2],x,y);s=b&31
    return {'i32.add':lambda:a+b,'i32.sub':lambda:a-b,'i32.mul':lambda:a*b,'i32.xor':lambda:a^b,'i32.and':lambda:a&b,'i32.or':lambda:a|b,'i32.shl':lambda:a<<s,'i32.shr_u':lambda:a>>s,'i32.rotl':lambda:(a<<s)|(a>>((32-s)&31)),'i32.rotr':lambda:(a>>s)|(a<<((32-s)&31))}[op]()&p.MASK

def main():
    ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();out=a.output;out.mkdir(parents=True,exist_ok=False);m=json.loads((a.input/'manifest.json').read_text());cases=[(0,0),(1,2),(0x7fffffff,0x80000000),(0xffffffff,0xffffffff),(0xaaaaaaaa,0x55555555),(0x12345678,0x9abcdef0)];records=[]
    for f in m['files']:
        mod=p.read(a.input/f['path'])
        for i,(x,y) in enumerate(cases):mod.append(['func',['export','"case'+str(i)+'"'],['result','i32'],['call','0',p.const(x),p.const(y)]])
        target=out/f['path'];p.compile_wat(p.emit(mod),target);log=p.w.tool('wasm-interp',[target,'--run-all-exports']);target.with_suffix('.log').write_text(log,encoding='utf-8')
        for i,(x,y) in enumerate(cases):assert 'case'+str(i)+'() => i32:'+str(eval_expr(m['models'][f['model']],x,y))+'\n' in log,(f,log)
        records.append(dict(path=f['path'],calls=len(cases)))
    save(out/'interpreter.json',dict(engine='WABT1.0.42',calls=len(cases)*len(records),mismatches=0,records=records))
    # Alternative expressions, seeds, and hand-composed input-dependent routes.
    extra=out/'random';extra.mkdir();rng=random.Random(20261020);models={};files=[]
    def expression(depth):
        if not depth or rng.randrange(4)==0:return rng.choice([p.get(0),p.get(1),p.const(rng.getrandbits(32))])
        op=rng.choice(sorted(p.BINARY|p.SHIFT));left=expression(depth-1)
        return [op,left,p.const(rng.randrange(32)) if op in p.SHIFT else expression(depth-1)]
    for i in range(12):
        name='random'+str(i);expr=expression(4);models[name]=expr;source=extra/(name+'.source.wasm');p.compile_wat(p.scalar_module(expr),source);files.append(dict(model=name,path=source.name))
        for opt in ('raw','O3'):
            path=extra/(name+'.'+opt+'.wasm')
            if opt=='raw':code,_=p.lifted(expr,'dynamic',seed=113*i+7);p.compile_wat(code,path)
            else:p.w.tool('wasm-opt',[extra/(name+'.raw.wasm'),'-O3','--enable-simd','-o',path])
            recovered=extra/(name+'.'+opt+'.recovered.wasm');attack.recover(path,recovered);files.extend([dict(model=name,path=path.name),dict(model=name,path=recovered.name)])
    save(extra/'manifest.json',dict(files=files,models=models));save(extra/'correctness.json',command(['node',Path(__file__).with_name('check.cjs'),extra]))
    controls=[]
    for name,body in [('division','(i32.div_u (local.get 0) (local.get 1))'),('dead_trap','(drop (i32.div_u (i32.const 1) (i32.const 0))) (local.get 0)')]:
        src=out/(name+'.wasm');p.compile_wat('(module (func (export "run") (param i32 i32) (result i32) '+body+'))',src)
        try:p.transform(src,out/(name+'.bad.wasm'),'dynamic')
        except ValueError as e:controls.append(dict(name=name,status='refused',reason=str(e)))
        else:raise AssertionError(name)
    vector=['i32x4.add',['i32x4.splat',p.get(0)],p.vec([0,1,2,3])]
    good=p.rotate(vector,p.get(1));bad_alignment=copy.deepcopy(good);bad_alignment[2][1][2][1][2]=p.const(1)
    bad_bounds=copy.deepcopy(good);bad_bounds[2][2]=p.bytesvec([31]*16)
    for name,v in [('cross_word',bad_alignment),('out_of_range_index',bad_bounds)]:
        src=out/(name+'.wasm');p.compile_wat(p.scalar_module(['i32x4.extract_lane','0',v]),src)
        try:attack.recover(src,out/(name+'.bad.wasm'))
        except ValueError as e:controls.append(dict(name=name,status='refused',reason=str(e)))
        else:raise AssertionError(name)
    # A surviving nonzero cursor must be evaluated, not silently set to zero.
    cursor=p.get(1);src=out/'nonzero-cursor.wasm';rec=out/'nonzero-cursor.recovered.wasm';p.compile_wat(p.scalar_module(['i32x4.extract_lane','0',p.rotate(vector,cursor)]),src);attack.recover(src,rec)
    witness=command(['node','-e',"const fs=require('fs');const f=process.argv.slice(1).map(p=>new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(p))).exports.run);let rows=[];for(let x of [0,1,-1,0x7fffffff])for(let y=0;y<8;y++){let a=f.map(g=>g(x,y)),expected=(x+(y&3))|0;if(a.some(z=>z!==expected))throw Error('cursor mismatch');rows.push({x,y,actual:a,expected});}console.log(JSON.stringify(rows));",src,rec]);controls.append(dict(name='nonzero_cursor',status='matched',calls=len(witness)*2,zero_cursor_would_be_wrong=sum(r['y']%4!=0 for r in witness),witnesses=witness))
    save(out/'controls.json',controls)
    print(json.dumps(dict(interpreter_calls=len(cases)*len(records),random_binaries=len(files),refusal_controls=4,nonzero_cursor_calls=64)))
if __name__=='__main__':main()
