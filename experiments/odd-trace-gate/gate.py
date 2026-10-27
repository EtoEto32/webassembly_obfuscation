"""Small gate for cyclic trace evaluation over Wasm i32; no novelty claim."""
import argparse,hashlib,importlib.util,json,math,random,subprocess,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sp=importlib.util.spec_from_file_location('ot_common',ROOT/'research/isotope-swizzle/prototype.py');q=importlib.util.module_from_spec(sp);sp.loader.exec_module(q)
MASK=0xffffffff
def c(n):return '(i32.const '+str(n if n<2**31 else n-2**32)+')'
def source(n,edges=None):
    size=n*n*4
    if edges is None:edges={(i,(i+1)%n):('(i32.add (local.get 0) (local.get 1))' if i==0 else '(i32.sub (local.get 2) (local.get 3))' if i==1 else c(1)) for i in range(n)}
    zero=' '.join(f'(i32.store {c(4*i)} {c(0)})' for i in range(n*n))
    init=' '.join(f'(i32.store {c(4*(i*n+j))} {value})' for (i,j),value in sorted(edges.items()))
    result=f'(i32.mul (local.get $sum) {c(pow(n,-1,2**32))})' if n%2 else f'(i32.div_u (local.get $sum) {c(n)})'
    return f'''(module (memory 1 1)
    (func $mm (param $a i32) (param $b i32) (param $dst i32)
      (local $i i32) (local $j i32) (local $k i32) (local $v i32)
      (loop $rows
        (local.set $j {c(0)})
        (loop $cols
          (local.set $k {c(0)}) (local.set $v {c(0)})
          (loop $dot
            (local.set $v (i32.add (local.get $v)
              (i32.mul
                (i32.load (i32.add (local.get $a) (i32.mul {c(4)} (i32.add (i32.mul (local.get $i) {c(n)}) (local.get $k)))))
                (i32.load (i32.add (local.get $b) (i32.mul {c(4)} (i32.add (i32.mul (local.get $k) {c(n)}) (local.get $j))))))))
            (local.set $k (i32.add (local.get $k) {c(1)}))
            (br_if $dot (i32.lt_u (local.get $k) {c(n)})))
          (i32.store (i32.add (local.get $dst) (i32.mul {c(4)} (i32.add (i32.mul (local.get $i) {c(n)}) (local.get $j)))) (local.get $v))
          (local.set $j (i32.add (local.get $j) {c(1)}))
          (br_if $cols (i32.lt_u (local.get $j) {c(n)})))
        (local.set $i (i32.add (local.get $i) {c(1)}))
        (br_if $rows (i32.lt_u (local.get $i) {c(n)}))))
    (func $trace (param i32 i32 i32 i32) (result i32)
      (local $step i32) (local $sum i32) (local $i i32)
      {zero} {init}
      (memory.copy {c(size)} {c(0)} {c(size)})
      (local.set $step {c(1)})
      (loop $power
        (call $mm {c(0)} {c(size)} {c(2*size)})
        (memory.copy {c(size)} {c(2*size)} {c(size)})
        (local.set $step (i32.add (local.get $step) {c(1)}))
        (br_if $power (i32.lt_u (local.get $step) {c(n)})))
      (loop $diag
        (local.set $sum (i32.add (local.get $sum) (i32.load (i32.add {c(size)} (i32.mul (local.get $i) {c((n+1)*4)})))))
        (local.set $i (i32.add (local.get $i) {c(1)}))
        (br_if $diag (i32.lt_u (local.get $i) {c(n)})))
      (local.get $sum))
    (func (export "run") (param i32 i32 i32 i32) (result i32) (local $sum i32)
      (local.set $sum (call $trace (local.get 0) (local.get 1) (local.get 2) (local.get 3))) {result}))'''
def probe(src,dst):
    m=q.read(src)
    # Called only on the raw generated module, before O3 may inline $trace.
    m.append(['export','"trace"',['func','1']]);q.compile(q.w.emit(m),dst)
def expr_ok(e):
    if e[0]=='i32.const':return len(e)==2
    if e[0]=='local.get':return len(e)==2 and 0<=int(e[1])<4
    return e[0] in ('i32.add','i32.sub','i32.mul') and len(e)==3 and all(expr_ok(x) for x in e[1:])
def extract(src):
    m=q.read(src)
    if any(e[0] not in ('type','func','export','memory') for e in m[1:]):raise ValueError('closed matrix profile')
    if [e for e in m[1:] if e[0]=='memory']!=[['memory','1','1']]:raise ValueError('private fixed memory')
    exports=[e for e in m[1:] if e[0]=='export']
    if len(exports)!=1 or exports[0][1]!='"run"':raise ValueError('run only')
    for f in [e for e in m[1:] if e[0]=='func']:
        body=[x for x in f[1:] if x[0] not in ('type','param','result','local')];values={};found=False
        for e in body:
            if e[0]=='memory.copy':
                if any(x[0]!='i32.const' for x in e[1:]):break
                d,s,l=[int(x[1],0) for x in e[1:]]
                if s!=0 or l!=d or l%4:break
                n=math.isqrt(l//4)
                if n*n*4!=l or not 2<=n<=16:break
                found=True;break
            if e[0]!='i32.store':break
            children=[x for x in e[1:] if isinstance(x,list)];attrs=[x for x in e[1:] if isinstance(x,str)]
            if len(children)!=2 or children[0][0]!='i32.const' or not expr_ok(children[1]):break
            a=int(children[0][1],0)
            for attr in attrs:
                if attr.startswith('offset='):a+=int(attr[7:],0)
                elif not attr.startswith('align='):raise ValueError('attribute')
            values[a]=children[1]
        if not found:continue
        edges={}
        for a,e in values.items():
            if a%4 or not 0<=a<l:raise ValueError('matrix bounds')
            if e[0]=='i32.const' and int(e[1],0)==0:continue
            edges[(a//4//n,a//4%n)]=q.w.emit(e)
        if len(edges)!=n:raise ValueError('not a simple cycle')
        succ={i:j for i,j in edges}
        if len(succ)!=n or set(succ.values())!=set(range(n)):raise ValueError('degree')
        visited=set();v=0
        while v not in visited:visited.add(v);v=succ[v]
        if len(visited)!=n or v!=0:raise ValueError('not one cycle')
        if n%2==0:raise ValueError('even cycle cannot recover arbitrary i32 from trace')
        # Verify the evaluator and multiplier, not only the initialization.
        with tempfile.TemporaryDirectory(dir=ROOT/'tmp',prefix='odd-trace-check-') as td:
            test=Path(td)/'reference.wasm';q.compile(source(n,edges),test)
            if q.read(test)!=m:
                opt=Path(td)/'O3.wasm';q.tool('wasm-opt',[test,'-O3','--enable-bulk-memory','-o',opt])
                if q.read(opt)!=m:raise ValueError('unsupported evaluator shape')
        return n,edges
    raise ValueError('matrix initialization not found')
def recover(src,dst):
    t=time.perf_counter();n,edges=extract(src);terms=list(edges.values());value=c(1)
    for x in terms:
        if x!=c(1):value=f'(i32.mul {value} {x})'
    q.compile(f'(module (func (export "run") (param i32 i32 i32 i32) (result i32) {value}))',dst)
    return {'length':n,'elapsed_ms':1000*(time.perf_counter()-t),'bytes':Path(dst).stat().st_size,'input_sha256':q.digest(src),'output_sha256':q.digest(dst)}
def model():
    rows=[]
    for w in range(1,7):
        mod=1<<w
        for n in range(2,9):
            for f in range(mod):
                # Independent literal matrix multiplication, not L*f as oracle implementation.
                a=[[0]*n for _ in range(n)]
                for i in range(n):a[i][(i+1)%n]=f if i==0 else 1
                b=[r[:] for r in a]
                for _ in range(n-1):b=[[sum(b[i][k]*a[k][j] for k in range(n))%mod for j in range(n)] for i in range(n)]
                trace=sum(b[i][i] for i in range(n))%mod;assert trace==n*f%mod
                if n%2:assert trace*pow(n,-1,mod)%mod==f
                rows.append({'width':w,'length':n,'f':f,'trace':trace})
    return {'cases':len(rows),'odd_cases':sum(r['length']%2 for r in rows),'rows':rows}
def run(out):
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);rows=[];attacks=[]
    for n in (2,3,4,5,7,8):
        raw=out/f'L{n}-raw.wasm';q.compile(source(n),raw);pr=out/f'L{n}-raw-probe.wasm';probe(raw,pr)
        for opt in ('raw','O3'):
            f=raw if opt=='raw' else out/f'L{n}-O3.wasm'
            if opt=='O3':q.tool('wasm-opt',[raw,'-O3','--enable-bulk-memory','-o',f]);q.w.tool('wasm-validate',[f])
            t={'length':n,'opt':opt,'path':str(f),'bytes':f.stat().st_size,'probe':str(pr) if opt=='raw' else None}
            if n%2:
                recovered=out/f'L{n}-{opt}-recovered.wasm'
                try:info=recover(f,recovered);t['recovered']=str(recovered);attacks.append({'length':n,'opt':opt,'status':'recovered',**info})
                except (ValueError,RuntimeError,subprocess.TimeoutExpired) as e:attacks.append({'length':n,'opt':opt,'status':type(e).__name__,'reason':str(e)})
            rows.append(t)
    (out/'targets.json').write_text(json.dumps(rows,indent=2));(out/'recovery.json').write_text(json.dumps(attacks,indent=2));(out/'model.json').write_text(json.dumps(model(),indent=2))
    cp=subprocess.run(['node',str(Path(__file__).with_name('check.cjs')),str(out/'targets.json'),str(out/'checks.json')],capture_output=True,text=True,timeout=60)
    (out/'stdout.txt').write_text(cp.stdout);(out/'stderr.txt').write_text(cp.stderr)
    if cp.returncode:raise RuntimeError(cp.stderr)
    print(cp.stdout.strip());print(json.dumps(attacks,indent=2))
if __name__=='__main__':
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='command',required=True);a=sub.add_parser('run');a.add_argument('out');a=sub.add_parser('recover');a.add_argument('src');a.add_argument('dst');args=ap.parse_args()
    if args.command=='run':run(args.out)
    else:print(json.dumps(recover(args.src,args.dst)))
