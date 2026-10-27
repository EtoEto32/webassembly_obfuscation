import argparse
import copy
import json
from pathlib import Path
import random
import prototype as p
from run import save,command
HERE=Path(__file__).resolve().parent
def poly(a,x,u,mask=p.M):return (a[0]+a[1]*x+a[2]*u+a[3]*x*x+a[4]*x*u+a[5]*u*u)&mask
def ref(d,byte,n):
    x=d['x0'];y=d['y0']
    for _ in range(n):x,y=(poly(d['P'],x,byte)+d['b']*y)&p.M,(poly(d['Q'],x,byte)+poly(d['R'],x,byte)*y)&p.M
    return x
def main():
    ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=False);out=a.output;manifest=json.loads((a.input/'manifest.json').read_text());records=[]
    cases=[(0,0),(0,1),(0,64),(65535,1),(65535,2),(0xffffffff,0),(0xffffffff,1)]
    for f in manifest['files']:
        mod=p.read(a.input/f['path']);d=manifest['models'][f['model']]
        for i,(pointer,n) in enumerate(cases):mod.append(['func',['export','"case'+str(i)+'"'],['result','i32'],['memory.fill',['i32.const','0'],['i32.const','91'],['i32.const','65536']],['call','0',['i32.const',str(pointer)],['i32.const',str(n)]]])
        for addr in (0,1,65534,65535):mod.append(['func',['export','"probe'+str(addr)+'"'],['result','i32'],['i32.load8_u',['i32.const',str(addr)]]])
        target=out/f['path'];p.compile_wat(p.w.emit(mod),target);log=p.w.tool('wasm-interp',[target,'--run-all-exports']);target.with_suffix('.log').write_text(log,encoding='utf-8')
        for i,(pointer,n) in enumerate(cases):
            trap=n>0 and pointer+n>65536;expected='error:' if trap else 'i32:'+str(ref(d,91,n))+'\n'
            assert 'case'+str(i)+'() => '+expected in log,(f,i,log)
        for addr in (0,1,65534,65535):assert 'probe'+str(addr)+'() => i32:91\n' in log
        records.append(dict(path=f['path'],calls=len(cases),memory_probes=4))
    save(out/'interpreter.json',dict(engine='WABT 1.0.42',calls=len(records)*len(cases),memory_probes=len(records)*4,mismatches=0,records=records))
    # Division-free local equality for all small words and random full words.
    rng=random.Random(20261019);checks=0
    for width in (1,2,3,4):
        modulus=1<<width;mask=modulus-1
        for x in range(modulus):
            for y in range(modulus):
                for b in range(modulus):
                    for u in range(modulus):
                        P=(x*x+3*x*u+u+1)&mask;Q=(x*u+3*x+u*u+2)&mask;R=(x+u+1)&mask
                        xn=(P+b*y)&mask;yn=(Q+R*y)&mask;w=b*y&mask;wn=(b*Q+R*w)&mask
                        assert wn==b*yn&mask
                        assert (b*Q+R*((xn-P)&mask))&mask==wn
                        checks+=1
    for _ in range(20000):
        x,y,b,P,Q,R=[rng.getrandbits(32) for _ in range(6)];xn=(P+b*y)&p.M;yn=(Q+R*y)&p.M
        assert (b*Q+R*((xn-P)&p.M))&p.M==b*yn&p.M;checks+=1
    save(out/'algebra.json',dict(state_checks=checks,mismatches=0,full_word_random=20000,widths=[1,2,3,4],seed=20261019))
    # Distinct source states and update coefficients produce identical reduced binaries.
    extra=out/'noninjective';extra.mkdir();files=[];models={};collisions=[]
    for name,d in manifest['models'].items():
        b=d['b'];v2=(b&-b).bit_length()-1
        if not v2:continue
        delta=1<<(32-v2);other=copy.deepcopy(d);other['y0']=(other['y0']+delta)&p.M;other['Q'][0]=(other['Q'][0]+delta)&p.M
        source=extra/(name+'.source.wasm');target=extra/(name+'.history.wasm');p.compile_wat(p.wat(other,'source'),source);p.transform(source,target);same=target.read_bytes()==(a.input/(name+'.history.raw.wasm')).read_bytes();assert same
        models[name]=other;files += [dict(model=name,path=source.name),dict(model=name,path=target.name)];collisions.append(dict(model=name,kernel_size=1<<v2,delta=delta,distinct_initial_y=True,distinct_Q_constant=True,identical_history_bytes=same))
    d=copy.deepcopy(next(iter(manifest['models'].values())));d['b']=0;models['b0']=d
    for mode in ('source','history','quotient'):
        target=extra/('b0.'+mode+'.wasm');p.compile_wat(p.wat(d if mode=='source' else p.quotient(d),mode),target);files.append(dict(model='b0',path=target.name))
    save(extra/'manifest.json',dict(files=files,models=models));save(extra/'collisions.json',collisions);save(extra/'correctness.json',command(['node',HERE/'check.cjs',extra]))
    # Valid but outside-profile code must not be silently transformed.
    base=next(f for f in manifest['files'] if f['mode']=='source' and f['opt']=='raw');source=p.read(a.input/base['path']);controls=[]
    variants={}
    z=copy.deepcopy(source);next(x for x in z[1:] if x[0]=='func')[-1]=['local.get','4'];variants['exposes_y']=z
    z=copy.deepcopy(source);z.append(['export','"coefficients"',['memory','1']]);variants['exports_private']=z
    z=copy.deepcopy(source);next(x for x in z[1:] if x[0]=='func').insert(-1,['i32.store',['i32.const','0'],['i32.const','77']]);variants['public_store']=z
    for name,mod in variants.items():
        path=out/(name+'.wasm');p.compile_wat(p.w.emit(mod),path)
        try:p.transform(path,out/(name+'.transformed.wasm'))
        except ValueError as error:controls.append(dict(name=name,rejected=str(error)))
        else:raise AssertionError('Unsafe source accepted')
    history=p.read(a.input/base['path'].replace('.source.','.history.'));next(x for x in history[1:] if x[0]=='func').insert(-1,['i32.store','1',['i32.const','0'],['i32.const','0']]);path=out/'private_store.wasm';p.compile_wat(p.w.emit(history),path)
    try:p.recover(path,out/'unsafe-recovered.wasm')
    except ValueError as error:controls.append(dict(name='private_store',rejected=str(error)))
    else:raise AssertionError('Unsafe recovery accepted')
    # An incorrect history update: omit advancing the previous input.
    bad=p.wat(p.quotient(manifest['models'][base['model']]),'history').replace('(local.set 5 (local.get 6))','(nop)');p.compile_wat(bad,out/'wrong-history.wasm')
    witness=command(['node','-e',"const fs=require('fs');let v=process.argv.slice(1).map(p=>{let e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(p))).exports;new Uint8Array(e.memory.buffer).set([1,2,3]);return e.run(0,3)});console.log(JSON.stringify(v));",a.input/base['path'],out/'wrong-history.wasm']);assert witness[0]!=witness[1];controls.append(dict(name='wrong_previous_input',input=[1,2,3],values=witness))
    save(out/'controls.json',controls);print(json.dumps(dict(wabt_calls=len(records)*len(cases),algebra_states=checks,noninjective_pairs=len(collisions),extra_binaries=len(files),refusal_controls=4,wrong_recurrence_detected=True)))
if __name__=='__main__':main()
