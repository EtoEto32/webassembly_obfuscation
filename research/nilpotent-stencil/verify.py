import argparse
import json
from pathlib import Path
import random
import prototype as p
import attack
from run import save,command

HERE=Path(__file__).resolve().parent


def evaluate(e,x,y):
    cache={}
    def go(n):
        key=id(n)
        if key in cache:return cache[key]
        if n[0]=='local.get':value=(x,y)[int(n[1])]
        elif n[0]=='i32.const':value=int(n[1],0)
        else:
            a,b=go(n[1]),go(n[2]);value={'i32.add':lambda:a+b,'i32.sub':lambda:a-b,'i32.mul':lambda:a*b}[n[0]]()
        cache[key]=value&p.MASK;return cache[key]
    return go(e)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();out=a.output;out.mkdir(parents=True,exist_ok=False)
    m=json.loads((a.input/'manifest.json').read_text());cases=[(0,0),(1,2),(0x7fffffff,0x80000000),(0xffffffff,0xffffffff),(0xaaaaaaaa,0x55555555),(0x12345678,0x9abcdef0)];records=[]
    for f in m['files']:
        mod=p.read(a.input/f['path'])
        for i,(x,y) in enumerate(cases):mod.append(['func',['export','"case'+str(i)+'"'],['result','i32'],['call','0',p.const(x),p.const(y)]])
        path=out/f['path'];p.compile_wat(p.emit(mod),path);log=p.w.tool('wasm-interp',[path,'--run-all-exports']);path.with_suffix('.log').write_text(log,encoding='utf-8')
        for i,(x,y) in enumerate(cases):assert 'case'+str(i)+'() => i32:'+str(evaluate(m['models'][f['model']],x,y))+'\n' in log,(f,log)
        records.append(dict(path=f['path'],calls=len(cases)))
    save(out/'interpreter.json',dict(engine='WABT1.0.42',calls=len(records)*len(cases),mismatches=0,records=records))
    rng=random.Random(40319);extra=out/'random';extra.mkdir();models={};files=[]
    def expression(depth):
        if not depth or rng.randrange(5)==0:return rng.choice([p.get(0),p.get(1),p.const(rng.getrandbits(32))])
        return [rng.choice(sorted(p.OPS)),expression(depth-1),expression(depth-1)]
    for i in range(12):
        name='random'+str(i);expr=['i32.add',['i32.mul',p.get(0),p.get(1)],expression(5)];models[name]=expr;source=extra/(name+'.source.wasm');p.compile_wat(p.scalar_dag(expr),source);files.append(dict(model=name,path=source.name))
        for opt in ('raw','O3'):
            path=extra/(name+'.'+opt+'.wasm')
            if opt=='raw':p.transform(source,path)
            else:p.w.tool('wasm-opt',[extra/(name+'.raw.wasm'),'-O3','--enable-simd','-o',path])
            rec=extra/(path.stem+'.recovered.wasm');attack.recover(path,rec);files.extend([dict(model=name,path=path.name),dict(model=name,path=rec.name)])
    save(extra/'manifest.json',dict(models=models,files=files));save(extra/'correctness.json',command(['node',HERE.parent/'lane-demand/check.cjs',extra]))
    controls=[]
    def refused(name,src,kind):
        try:
            if kind=='source':p.transform(src,out/(name+'.rejected.wasm'))
            else:attack.recover(src,out/(name+'.rejected.wasm'))
        except ValueError as error:controls.append(dict(name=name,status='refused',reason=str(error)))
        else:raise AssertionError('Unsafe acceptance: '+name)
    for name,body in [('division','(i32.div_u (local.get 0) (local.get 1))'),('xor','(i32.xor (local.get 0) (local.get 1))'),('dead_trap','(drop (i32.div_u (i32.const 1) (i32.const 0))) (local.get 0)')]:
        src=out/(name+'.wasm');p.compile_wat('(module (func (export "run") (param i32 i32) (result i32) '+body+'))',src);refused(name,src,'source')
    quartic=m['models']['quartic']
    negative=[]
    for name,shift,weights,xy in [('insufficient_shift',7,(4,-6,4,-1),(0,0)),('wrong_weights',8,(4,-6,4,0),(0,1))]:
        src=out/(name+'.wasm');code,_=p.lifted(quartic,'constant',shift=shift,weights=weights);p.compile_wat(code,src);refused(name,src,'recovery');negative.append(dict(path=src.name,x=xy[0],y=xy[1],expected=evaluate(quartic,*xy)))
    # A non-polynomial pointwise operation must not enter the coefficient model.
    v=['v128.xor',['i32x4.add',['i32x4.splat',p.get(0)],p.vec([256,512,768,1024])],['i32x4.splat',p.get(1)]]
    terms=[['i32.mul',p.const(c),['i32x4.extract_lane',str(i),v]] for i,c in enumerate((4,-6,4,-1))];expr=terms[0]
    for term in terms[1:]:expr=['i32.add',expr,term]
    # Bind the vector so all observations refer to the same binary DAG node.
    src=out/'vector_xor.wasm';body='(local v128) (local.set 2 '+p.emit(v)+')';obs=p.emit(expr).replace(p.emit(v),'(local.get 2)');p.compile_wat('(module (func (export "run") (param i32 i32) (result i32) '+body+obs+'))',src);refused('vector_xor',src,'recovery');negative.append(dict(path=src.name,x=0,y=1024,expected=1024))
    save(out/'negative-inputs.json',negative)
    witnesses=command(['node','-e',"const fs=require('fs'),p=require('path'),root=process.argv[1];let a=JSON.parse(fs.readFileSync(p.join(root,'negative-inputs.json')));for(let r of a){const f=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(p.join(root,r.path)))).exports.run;r.actual=f(r.x,r.y)>>>0;if(r.actual===r.expected)throw Error('Missing counterexample');}console.log(JSON.stringify(a));",out]);save(out/'counterexamples.json',witnesses)
    # Real Wasm witnesses for loss of injectivity in every individual lane map.
    maps=[]
    for k in range(1,5):
        delta=['i32.shl',['i32.sub',p.const(0),['i32.shr_u',p.get(0),p.const(10)]],p.const(8)]
        expr=['i32.add',p.get(0),['i32.mul',p.const(k),delta]];path=out/('lane'+str(k)+'.wasm');p.compile_wat(p.scalar_dag(expr),path);maps.append(dict(path=path.name,k=k,a=(4-k)*256,b=1024))
    save(out/'lane-inputs.json',maps)
    collisions=command(['node','-e',"const fs=require('fs'),p=require('path'),root=process.argv[1];let a=JSON.parse(fs.readFileSync(p.join(root,'lane-inputs.json')));for(let r of a){const f=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(p.join(root,r.path)))).exports.run;r.values=[f(r.a,0)>>>0,f(r.b,0)>>>0];if(r.a===r.b||r.values[0]!==r.values[1])throw Error('Collision missing');}console.log(JSON.stringify(a));",out]);save(out/'lane-collisions.json',collisions)
    save(out/'controls.json',controls)
    # Independent integer-arithmetic finite-difference check at reduced and full widths.
    algebra=[]
    for bits in (4,8,12,16,32):
        mask=(1<<bits)-1;shift=(bits+3)//4;count=0
        for degree in range(1,33):
            for _ in range(100):
                x=rng.getrandbits(bits);d=(rng.getrandbits(bits)<<shift)&mask
                expected=pow(x,degree,1<<bits);actual=sum(c*pow((x+k*d)&mask,degree,1<<bits) for k,c in enumerate((4,-6,4,-1),1))&mask
                assert actual==expected;count+=1
        algebra.append(dict(bits=bits,shift=shift,checks=count,mismatches=0))
    save(out/'algebra.json',algebra)
    print(json.dumps(dict(interpreter_calls=len(records)*len(cases),random_binaries=len(files),refusal_controls=len(controls),counterexamples=len(witnesses),noninjective_lanes=len(collisions),algebra_checks=sum(r['checks'] for r in algebra))))


if __name__=='__main__':main()
