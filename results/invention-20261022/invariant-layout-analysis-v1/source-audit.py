import argparse,json,platform,random,re,struct,subprocess
from pathlib import Path
import prototype as p
import run as runner
import attack

def oracle(mem,name,xyz):
    ptr,x,n=xyz;base=(ptr&0xfffffff0)//4
    for i in range(n&31):
        j=(i+x)&3 if name=='coupled' else i&3;a=base+j;b=base+((j+1)&3);u,v=mem[a],mem[b]
        if name=='mix':t=(u+v+x)&p.MASK;z=(((t<<7)|(t>>25))&p.MASK)^2654435769
        elif name=='coupled':z=u*1664525+(v^x)
        else:z=u^v^((x+i)&p.MASK)
        mem[b if name=='coupled' else a]=z&p.MASK
    return mem[base]^mem[base+3]

def run(main,output):
    main,out=Path(main).resolve(),Path(output).resolve();out.mkdir(parents=True,exist_ok=False)
    rows=json.loads((main/'manifest.json').read_text());replays=[];engines=[];controls=[]
    for row in rows:
        if row['negative']:continue
        src=main/row['file'];dst=out/row['file']
        if row['mode']=='recovered':attack.recover(main/row['file'].replace('.recovered.wasm','.wasm'),dst,out/('replay-'+src.stem))
        elif row['opt']=='O3':p.q.tool('wasm-opt',[out/row['file'].replace('.O3.wasm','.raw.wasm'),'--enable-simd','-O3','-o',dst])
        elif row['mode']=='plain':p.q.compile(runner.source(row['name']),dst)
        else:p.transform(main/f'{row["name"]}.plain.raw.wasm',dst,row['mode'])
        assert dst.read_bytes()==src.read_bytes();replays.append(dict(file=src.name,byte_equal=True,sha256=p.q.digest(src)))
        m=p.q.read(src);idx={x[1]:x[2][1] for x in m[1:] if x[0]=='export'}
        mem=[0]*16384
        for i in range(16):mem[i]=((i+1)*0x9e3779b1)&p.MASK
        probes=[(0,1,1),(16,0xdeadbeef,4),(65520,7,9),(32,0xffffffff,17)];want=[]
        for i,xyz in enumerate(probes):
            want.append(oracle(mem,row['name'],xyz));args=' '.join(f'(i32.const {x})' for x in xyz)
            m.append(p.sx.parse(f'(module (func (export "probe{i}") (result i32) (call {idx[chr(34)+"run"+chr(34)]} {args})))')[1])
        m.append(p.sx.parse(f'(module (func (export "trap_probe") (result i32) (call {idx[chr(34)+"edge"+chr(34)]} (i32.const 4) (i32.const 123) (i32.const 0))))')[1]);mem[0]=123
        raw=struct.pack('<16384I',*mem)
        if row['mode'] not in ('plain','recovered'):raw=p.codec(raw,row['mode'])
        offsets=list(range(0,64,4))+list(range(65520,65536,4))
        for i,a in enumerate(offsets):m.append(p.sx.parse(f'(module (func (export "word{i}") (result i32) (i32.load (i32.const {a}))))')[1])
        wrapper=out/(src.stem+'.interp.wasm');p.q.compile(p.sx.emit(m),wrapper)
        text=p.sx.tool('wasm-interp',[wrapper,'--run-all-exports']);(out/(src.stem+'.interp.txt')).write_text(text,encoding='utf8')
        got=[int(x)&p.MASK for x in re.findall(r'probe\d+\(\) => i32:(-?\d+)',text)]
        words=[int(x)&p.MASK for x in re.findall(r'word\d+\(\) => i32:(-?\d+)',text)]
        assert got==want and words==[struct.unpack_from('<I',raw,a)[0] for a in offsets],src
        assert 'trap_probe() => error:' in text,text
        engines.append(dict(file=src.name,value_calls=4,trap_calls=1,memory_probes=20))
    # Page boundaries and zero-page memory use separate finite input series.
    extra=out/'pages';extra.mkdir();manifest=[]
    for pages in (0,2):
        plain=extra/f'pages{pages}.plain.raw.wasm';p.q.compile(runner.source('mix',pages),plain)
        for mode in ('plain','transport'):
            raw=extra/f'pages{pages}.{mode}.raw.wasm'
            if mode!='plain':p.transform(plain,raw,mode)
            opt=extra/f'pages{pages}.{mode}.O3.wasm';p.q.tool('wasm-opt',[raw,'--enable-simd','-O3','-o',opt])
            for kind,file in (('raw',raw),('O3',opt)):
                m=p.q.read(file)
                # O3 can remove an unused zero-page memory after proving every access traps.
                if not any(t[0]=='memory' for t in m[1:]):
                    assert pages==0
                    m.append(['memory','0','0'])
                m.append(['export','"__physical"',['memory','0']]);probe=extra/(file.stem+'.probe.wasm');p.q.compile(p.sx.emit(m),probe)
                manifest.append(dict(name='mix',mode=mode,opt=kind,file=file.name,probe=probe.name,negative=False,pages=pages))
    p.q.save(extra/'manifest.json',manifest)
    p.q.save(extra/'custom-inputs.json',[dict(fn='run',args=[a,x,n]) for a in (0,65520,65536,131056,131068,131072,0xfffffff0) for x in (0,1,0xdeadbeef) for n in (0,3,17)]+[dict(fn='edge',args=[a,0x12345678,0]) for a in (0,4)])
    check=subprocess.run(['node',str(Path(__file__).with_name('check.cjs')),str(extra)],capture_output=True,text=True,check=True)
    p.q.save(out/'page-summary.json',json.loads(check.stdout))
    for label,wat in [('unaligned','(module (memory 1 1) (func (export "run") (param i32) (result i32) (i32.load (local.get 0))))'),('export-memory','(module (memory (export "memory") 1 1))'),('grow','(module (memory 1 1) (func (export "run") (result i32) (memory.grow (i32.const 0))))')]:
        file=out/f'control-{label}.wasm';p.q.compile(wat,file)
        try:p.lower(p.q.read(file),'transport')
        except ValueError as e:controls.append(dict(name=label,status='rejected',reason=str(e)))
        else:raise AssertionError(label)
    rng=random.Random(221123);wide=0
    for _ in range(4096):
        x=[rng.getrandbits(32) for _ in range(4)];i=rng.randrange(4);new=rng.getrandbits(32);s=p.phase(x);y=p.rotate(x,s);j=(i+s)%4;old=y[j];y[j]=new;x[i]=new
        assert p.rotate(y,p.h(new)-p.h(old))==p.rotate(x,p.phase(x));wide+=1
    p.q.save(out/'replay.json',replays);p.q.save(out/'interpreter.json',engines);p.q.save(out/'controls.json',controls)
    p.q.save(out/'environment.json',dict(platform=platform.platform(),python=platform.python_version(),processor=platform.processor(),node=subprocess.check_output(['node','--version'],text=True).strip(),wabt=p.sx.tool('wasm-validate',['--version']).strip(),binaryen=p.q.tool('wasm-opt',['--version']).strip()))
    p.q.save(out/'wide-model.json',dict(cases=wide,seed=221123));runner.pin(out)
    print(json.dumps(dict(regenerated=len(replays),interpreter_value_calls=4*len(engines),interpreter_trap_calls=len(engines),interpreter_memory_probes=20*len(engines),wide_model_cases=wide,controls=len(controls))))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('main');ap.add_argument('output');a=ap.parse_args();run(a.main,a.output)
