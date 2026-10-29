import argparse, json, platform, random, subprocess
from pathlib import Path
from run import p,q,HERE
from recover import expose

def main(main,extra,dst):
    main=Path(main);extra=Path(extra);dst=Path(dst);dst.mkdir(parents=True,exist_ok=False)
    # Numerical property is algebraic; samples check this codec implementation.
    r=random.Random(211064)
    for _ in range(1024):
        raw=bytes(r.randrange(256) for _ in range(16));assert p.codec_bytes(p.codec_bytes(raw),True)==raw
    assert p.codec_bytes(bytes(16))==bytes(16)
    rejections=[]
    for name,text in [('export-memory','(module (memory (export "m") 1 1))'),('grow','(module (memory 1 1)(func (drop (memory.grow (i32.const 0)))))'),('memory64','(module (memory i64 1 1))'),('import','(module (import "m" "f" (func))(memory 1 1))')]:
        f=dst/f'reject-{name}.wasm';q.compile(text,f)
        try:p.lower(q.read(f),'block')
        except q.Unsupported as e:rejections.append(dict(name=name,reason=str(e)))
        else:raise AssertionError(name)
    q.save(dst/'rejections.json',rejections)
    # Reproduce the actual proposal on all page sizes, including O3.
    replay=[]
    for pages in (0,1,2):
        f=dst/f'p{pages}.replay.raw.wasm';p.transform(main/f'p{pages}.plain.raw.wasm',f,'block')
        o=dst/f'p{pages}.replay.O3.wasm';q.tool('wasm-opt',[f,'-O3','--enable-memory64','--enable-simd','--enable-sign-ext','-o',o])
        for opt,target in [('raw',f),('O3',o)]:
            ref=main/f'p{pages}.block.{opt}.wasm';assert q.digest(ref)==q.digest(target);replay.append(dict(file=ref.name,sha256=q.digest(ref),match=True))
    q.save(dst/'replay.json',replay)
    # Independent interpreter: trap followed by observation in the same instance.
    interpreter=[]
    for mode in ('plain','lifted','byte','block','block-high'):
        base=extra if mode=='block-high' else main
        for opt in ('raw','O3'):
            src=base/f'p1.{mode}.{opt}.wasm';m=q.read(src)
            ex={x[1][1:-1]:x[2][1] for x in m[1:] if x[0]=='export'}
            probes=[('i32_st2',[65535,0xabcd],None),('i32_ld1u',[65535],'i32'),('i64_st8',[13,0x123456789abcdef],None),('i64_ld8',[13],'i64'),('offset_store',[8,42],None),('prefix',[65533,0x1234],None),('i32_ld4',[4],'i32')]
            for j,(name,args,result) in enumerate(probes):
                vals=[f'({"i64" if name.startswith("i64_st") and k==1 else "i32"}.const {v})' for k,v in enumerate(args)]
                text=f'(module (func (export "probe{j}") '+(f'(result {result}) ' if result else '')+f'(call {ex[name]} '+ ' '.join(vals)+')))'
                m.extend(q.w.parse(text)[1:])
            f=dst/f'{mode}.{opt}.interp.wasm';q.compile(q.w.emit(m),f)
            out=q.w.tool('wasm-interp',[f,'--run-all-exports']);(dst/f'{mode}.{opt}.interpreter.txt').write_text(out,encoding='utf-8')
            lines=[x for x in out.splitlines() if x.startswith('probe')]
            assert len(lines)==7,(f,lines)
            for j in (0,4,5):assert 'error: out of bounds memory access' in lines[j],lines
            for j,want in [(1,'i32:0'),(2,'=>'),(3,'i64:81985529216486895'),(6,'i32:4660')]:assert want in lines[j],lines
            interpreter.append(dict(file=src.name,observations=7,traps=3,match=True))
    q.save(dst/'interpreter.json',interpreter)
    recovery=[]
    for mode in ('byte','block','block-high'):
        base=extra if mode=='block-high' else main
        for pages in (1,2):
            for opt in ('raw','O3'):
                src=base/f'p{pages}.{mode}.{opt}.wasm';attack=dst/f'attack-p{pages}-{mode}-{opt}';attack.mkdir();ids=expose(src,attack/'exposed.wasm')
                c=subprocess.run(['node',str(HERE/'recover.cjs'),str(attack.resolve())],capture_output=True,text=True,timeout=60)
                (attack/'stdout.txt').write_text(c.stdout,encoding='utf-8');(attack/'stderr.txt').write_text(c.stderr,encoding='utf-8')
                if c.returncode:raise RuntimeError(c.stderr)
                # Score only after recovery. The attack never receives this source.
                code='''const fs=require('fs'),e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[1]))).exports;
                  const w=[0x80000000,1,0x7fffffff,0x2468ace0];for(let i=0;i<4;i++)e.i32_st4(32+4*i,w[i]);
                  e.bench(257,13);fs.writeFileSync(process.argv[2],Buffer.from(new Uint8Array(e.__physical.buffer)));'''
                c=subprocess.run(['node','-e',code,str(main/f'p{pages}.plain.raw.probe.wasm'),str(attack/'oracle.bin')],capture_output=True,text=True,timeout=30)
                if c.returncode:raise RuntimeError(c.stderr)
                assert (attack/'oracle.bin').read_bytes()==(attack/'logical.bin').read_bytes()
                recovery.append(dict(file=src.name,candidate_ids=ids,result=json.loads((attack/'recovery.json').read_text()),logical_sha256=q.digest(attack/'logical.bin'),match=True))
    q.save(dst/'recovery.json',recovery)
    q.save(dst/'environment.json',dict(platform=platform.platform(),python=platform.python_version(),node=subprocess.check_output(['node','--version'],text=True).strip(),wabt=q.w.tool('wat2wasm',['--version']).strip(),binaryen=q.tool('wasm-opt',['--version']).strip()))
    print(json.dumps(dict(codec_roundtrips=1024,rejections=len(rejections),reproduced=len(replay),interpreter_observations=sum(x['observations'] for x in interpreter),recoveries=len(recovery))))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('main');ap.add_argument('extra');ap.add_argument('output');a=ap.parse_args();main(a.main,a.extra,a.output)
