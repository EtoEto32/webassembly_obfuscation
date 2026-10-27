"""Byte replay, separate validator/interpreter, all-input scalar comparison."""
import argparse,hashlib,json,re,shutil,subprocess,sys,time
from pathlib import Path
import prototype as p
sys.path.insert(0,str(p.ROOT/'.tools/encoding-synthesis-python'))
import z3

def sha(f):return hashlib.sha256(Path(f).read_bytes()).hexdigest()
def save(f,v):Path(f).write_text(json.dumps(v,indent=2),encoding='utf8')

def run(main,output):
    main=Path(main).resolve();out=Path(output).resolve();out.mkdir(parents=True,exist_ok=False)
    pins=json.loads((main/'pins.json').read_text());assert all(sha(main/f)==h for f,h in pins.items())
    rows=json.loads((main/'manifest.json').read_text());defs=json.loads((main/'definitions.json').read_text());replay=[];interpret=[];smt=[];timings=[]
    args=[z3.BitVec('x',32),z3.BitVec('y',32)]
    def symbolic(e):
        op=e[0]
        if op=='local.get':return args[int(e[1])]
        if op=='i32.const':return z3.BitVecVal(int(e[1],0),32)
        a=symbolic(e[1]);b=symbolic(e[2]) if len(e)>2 else None
        if op=='i32.eqz':return z3.If(a==0,z3.BitVecVal(1,32),z3.BitVecVal(0,32))
        return {'i32.and':lambda:a&b,'i32.or':lambda:a|b,'i32.xor':lambda:a^b,'i32.shr_u':lambda:z3.LShR(a,b&31),'i32.shl':lambda:a<<(b&31),'i32.add':lambda:a+b,'i32.sub':lambda:a-b}[op]()
    for row in rows:
        target=out/row['file'];name=row['name'];mode=row['mode'];version=row['version']
        if mode=='plain':
            if version=='raw':p.compile(p.source(defs[name]['clauses']),target)
            else:p.w.tool('wasm-opt',[out/f'{name}.plain.raw.wasm','-O3','-o',target])
        elif mode=='validator':
            if version=='raw':p.transform(out/f'{name}.plain.raw.wasm',target)
            else:p.w.tool('wasm-opt',[out/f'{name}.validator.raw.wasm','-O3','-o',target])
        else:p.recover(out/f'{name}.validator.{version}.wasm',target)
        assert sha(target)==sha(main/row['file']);replay.append(row['file'])
        if mode!='validator':
            m=p.read(target)
            inputs=[(0,0),(1,1),(0xffffffff,0xffffffff),(0x80000000,0x7fffffff),tuple(defs[name]['witness']),(123456789,987654321)]
            for i,(a,b) in enumerate(inputs):m.append(p.w.parse(f'(module (func (export "probe{i}") (result i32) (call 0 (i32.const {a}) (i32.const {b}))))')[1])
            f=out/('interp-'+row['file']);p.compile(p.w.emit(m),f);log=p.w.tool('wasm-interp',[f,'--run-all-exports']);f.with_suffix('.log').write_text(log,encoding='utf8')
            actual=[]
            for i,(a,b) in enumerate(inputs):
                line=next(x for x in log.splitlines() if x.startswith(f'probe{i}()'));got=int(re.search(r'i32:(\d+)',line)[1])
                want=int(all(any(((a if word==0 else b)>>bit&1)^neg for word,bit,neg in clause) for clause in defs[name]['clauses']))
                assert got==want;actual.append(got)
            interpret.append(dict(file=row['file'],actual=actual))
        if mode=='recovered':
            m=p.read(target);f=next(x for x in m[1:] if x[0]=='func');e=[x for x in f[1:] if x[0] not in ('type','param','result')]
            assert len(e)==1
            solver=z3.Solver();solver.set(timeout=10000);solver.add(symbolic(p.expression(defs[name]['clauses']))!=symbolic(e[0]));start=time.perf_counter();status=str(solver.check());assert status=='unsat'
            smt.append(dict(file=row['file'],status=status,seconds=time.perf_counter()-start))
        if mode=='validator':
            for repeat in range(7):timings.append(dict(file=row['file'],repeat=repeat,**p.recover(target,out/f'repeat-{repeat}-{row["file"]}')))
    validations=[]
    for row in json.loads((main/'queries.json').read_text()):
        r=subprocess.run([str(p.w.WABT/'wasm-validate.exe'),str(main/row['file'])],capture_output=True,text=True,timeout=30)
        assert r.returncode in (0,1) and (r.returncode==0)==row['expected'],(row,r.returncode,r.stderr)
        validations.append(dict(file=row['file'],expected=row['expected'],valid=r.returncode==0,returncode=r.returncode,stderr=r.stderr))
    rejects=[]
    for name,wat in {
       'memory':'(module (memory 1) (func (export "run") (param i32 i32) (result i32) (i32.const 1)))',
       'add':'(module (func (export "run") (param i32 i32) (result i32) (i32.add (local.get 0) (local.get 1))))',
       'wrong-arity':'(module (func (export "run") (param i32) (result i32) (local.get 0)))'}.items():
        src=out/f'reject-{name}.wasm';p.compile(wat,src)
        try:p.transform(src,out/f'unexpected-{name}.wasm');raise AssertionError('unexpected acceptance')
        except ValueError as e:rejects.append(dict(name=name,reason=str(e)))
    # Tamper a structural opcode in the template; the recovery recognizer must reject it.
    m=p.read(main/'access.validator.raw.wasm');segment=next(x for x in m[1:] if x[0]=='data');b=bytearray(p.decode_string(segment[2]));b[b.index(bytes([0x6a,0x1a,0x0b]))]=0x7c
    segment[2]='"'+''.join('\\%02x'%x for x in b)+'"';bad=out/'bad-template.wasm';p.compile(p.w.emit(m),bad)
    try:p.recover(bad,out/'bad-recovered.wasm');raise AssertionError('bad template accepted')
    except ValueError as e:rejects.append(dict(name='altered-template',reason=str(e)))
    save(out/'audit.json',dict(pins_verified=len(pins),replay=replay,interpreter=interpret,query_validation=validations,smt=smt,z3_version=z3.get_version_string(),analysis_repeats=timings,rejections=rejects))
    for f in Path(__file__).parent.iterdir():
        if f.suffix in ('.py','.cjs'):shutil.copy2(f,out/('source-'+f.name))
    save(out/'pins.json',{str(f.relative_to(out)):sha(f) for f in out.rglob('*') if f.is_file() and f.name!='pins.json'})
    print(json.dumps(dict(pins_verified=len(pins),replayed=len(replay),wabt_calls=sum(len(x['actual']) for x in interpret),query_validations=len(validations),smt_unsat=len(smt),recoveries_repeated=len(timings),rejections=len(rejects),passed=True)))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('main');ap.add_argument('output');a=ap.parse_args();run(a.main,a.output)
