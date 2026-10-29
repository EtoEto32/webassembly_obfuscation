"""Replay recovery artifacts; independently interpret small execution probes."""
import copy,json,platform,re,subprocess,sys
from pathlib import Path
import recover as r
q=r.q;ROOT=Path(__file__).resolve().parents[2]
isolated,rawrec,optrec,main,out=map(Path,sys.argv[1:]);out.mkdir(parents=True,exist_ok=False)
replay=[];recovery=[]
for opt,old in [('raw',rawrec),('O3',optrec)]:
    dst=out/opt;recovery.append(dict(opt=opt,**r.recover(isolated/f'isolated-{opt}.wasm',dst)))
    for mode in ('certified','recovered-state','recovered-io'):
        f=mode+'.wasm';assert (dst/f).read_bytes()==(old/f).read_bytes()
        replay.append(dict(opt=opt,mode=mode,sha256=q.digest(dst/f),byte_identical=True))
q.save(out/'replay.json',dict(artifacts=replay,recovery=recovery))
triple=(0x80000000,0x12345678,0xfedcba98)
rotr=lambda x,n:((x>>n)|(x<<(32-n)))&0xffffffff
a,b,c=triple;want=((rotr(a,2)^rotr(a,13)^rotr(a,22))+((a&b)^(a&c)^(b&c)))&0xffffffff
engine=[]
for row in json.loads((main/'manifest.json').read_text()):
    module=q.read(main/row['file']);findex=next(x[2][1] for x in module[1:] if x[:2]==['export','"run"'])
    probe=['func',['export','"probe"'],['result','i32'],['call',findex,*[['i32.const',str(x)] for x in triple]]]
    module.append(probe);dst=out/('interp-'+row['file']);q.compile(q.w.emit(module),dst)
    stdout=q.w.tool('wasm-interp',[dst,'--run-all-exports'])
    (out/(dst.stem+'.log')).write_text(stdout,encoding='utf-8')
    match=re.search(r'probe\(\) => i32:(\d+)',stdout);assert match and int(match[1])==want
    engine.append(dict(file=row['file'],input=triple,expected=want,actual=int(match[1])))
q.save(out/'interpreter.json',engine)
diagnostics=[]
for row in json.loads((main/'manifest.json').read_text()):
    if row['opt']!='O3':continue
    text=subprocess.check_output(['node','--no-liftoff','--no-wasm-lazy-compilation','--print-wasm-code','-e','new WebAssembly.Module(require("fs").readFileSync(process.argv[1]));',str(main/row['file'])],text=True,timeout=30)
    (out/(row['mode']+'-compiler.log')).write_text(text,encoding='utf-8')
    compilers=re.findall(r'compiler:\s*(\S+)',text);assert compilers and set(compilers)=={'TurboFan'}
    diagnostics.append(dict(file=row['file'],compilers=compilers))
q.save(out/'compiler.json',diagnostics)
old=ROOT/'experiments/sha256-fixedpoint/artifacts/fixedpoint.wasm'
assert q.digest(old)=='96465f7c6c8be7fc99b2523524d669ada5663645796713c7aaa342831e577e79'
sources=list(Path(__file__).parent.glob('*.py'))+list(Path(__file__).parent.glob('*.cjs'))+[ROOT/'research/isotope-swizzle/prototype.py',ROOT/'research/connectivity-elimination/prototype.py']
q.save(out/'source-hashes.json',[dict(file=str(f.relative_to(ROOT)),sha256=q.digest(f)) for f in sources])
q.save(out/'environment.json',dict(python=sys.version,platform=platform.platform(),processor=platform.processor(),node=subprocess.check_output(['node','--version'],text=True).strip(),wabt=q.w.tool('wasm-validate',['--version']).strip(),binaryen=q.tool('wasm-opt',['--version']).strip(),original_sha256=q.digest(old)))
print(json.dumps(dict(replayed=len(replay),interpreter_probes=len(engine),compiler_diagnostics=len(diagnostics))))
