"""Feasibility probe: rANS decoder update vs a corrected packed affine chain."""
import argparse,importlib.util,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('sq_common',ROOT/'research/isotope-swizzle/prototype.py');q=importlib.util.module_from_spec(s);s.loader.exec_module(q)
class Unsupported(ValueError):pass
MASK=(1<<32)-1
def demand(ok,why):
    if not ok:raise Unsupported(why)
def source(ops):
    v='(local.get 0)'
    for a,b in ops:v=f'(i32.add (i32.mul {v} (i32.const {a})) (i32.const {b}))'
    return f'(module (func (export "run") (param i32) (result i32) {v}))'
def parse(m):
    demand(all(x[0] in ('type','func','export') for x in m[1:]),'closed pure module')
    fs=[x for x in m[1:] if x[0]=='func'];demand(len(fs)==1,'one function')
    f=fs[0];demand([x for x in f[1:] if isinstance(x,list) and x[0]=='param']==[['param','i32']],'i32 parameter')
    demand([x for x in f[1:] if isinstance(x,list) and x[0]=='result']==[['result','i32']],'i32 result')
    demand([x for x in m[1:] if x[0]=='export']==[['export','"run"',['func','0']]],'only run export')
    code=[x for x in f[1:] if isinstance(x,list) and x[0] not in ('param','result','type')];demand(len(code)==1,'single expression')
    ops=[]
    def visit(e):
        if e==['local.get','0']:return
        demand(e[0]=='i32.add' and e[2][0]=='i32.const','affine add')
        t=e[1];demand(t[0]=='i32.mul' and t[2][0]=='i32.const','affine multiply')
        visit(t[1]);ops.append((int(t[2][1])&MASK,int(e[2][1])&MASK))
    visit(code[0]);demand(1<=len(ops)<=15,'1..15 stages');return ops
def generate(ops,freq,mode):
    demand(mode in ('decoder','lift'),'mode');M=sum(freq);k=M.bit_length()-1
    demand(M==1<<k and len(freq)==len(ops)+1 and min(freq)>0,'power-of-two positive partition')
    B=[sum(freq[:i]) for i in range(len(freq))];W=(1<<(32+k))-1
    z='(local.get 1)';rem=f'(i64.and {z} (i64.const {M-1}))'
    def update(i):
        a,b=ops[i]
        if mode=='decoder':
            value=f'(i64.add (i64.mul (i64.const {freq[i]}) (i64.shr_u {z} (i64.const {k}))) (i64.sub {rem} (i64.const {B[i]})))'
        else:
            c=(M*b+B[i+1]-a*B[i])&W
            value=f'(i64.and (i64.add (i64.mul {z} (i64.const {a})) (i64.const {c})) (i64.const {W}))'
        return f'(local.set 1 {value})'
    dispatch=update(len(ops)-1)
    for i in range(len(ops)-2,-1,-1):
        dispatch=f'(if (i64.lt_u {rem} (i64.const {B[i+1]})) (then {update(i)}) (else {dispatch}))'
    wat=f'''(module (func (export "run") (param i32) (result i32) (local i64 i32)
      (local.set 1 (i64.or (i64.shl (i64.extend_i32_u (local.get 0)) (i64.const {k})) (i64.const {B[0]})))
      (loop
       (if (i64.ge_u {rem} (i64.const {B[-1]})) (then (return (i32.wrap_i64 (i64.shr_u {z} (i64.const {k}))))))
       (if (i32.ge_u (local.get 2) (i32.const {len(ops)})) (then (unreachable)))
       {dispatch}
       (local.set 2 (i32.add (local.get 2) (i32.const 1))) (br 0))
      (unreachable)))'''
    return wat
def transform(src,dst,mode):
    start=time.perf_counter();ops=parse(q.read(src));n=len(ops)+1;M=1<<(n-1).bit_length();freq=[1]*n
    for i in range(M-n):freq[(i*3+1)%n]+=1
    q.compile(generate(ops,freq,mode),dst)
    return dict(mode=mode,stages=len(ops),M=M,frequencies=freq,elapsed_ms=(time.perf_counter()-start)*1000,source_sha256=q.digest(src),output_sha256=q.digest(dst),watchdog_limit=len(ops),watchdog='diagnostic unreachable; never fires for lift')
def recover(src,dst):
    import subprocess
    # This attack receives only the executable; the affine-family assumption is explicit.
    js="const e=new WebAssembly.Instance(new WebAssembly.Module(require('fs').readFileSync(process.argv[1]))).exports; console.log(JSON.stringify([0,1,2].map(x=>e.run(x)>>>0)))"
    start=time.perf_counter();ys=json.loads(subprocess.check_output(['node','-e',js,str(src)],text=True,timeout=30));a=(ys[1]-ys[0])&MASK;b=ys[0]
    demand((2*a+b)&MASK==ys[2],'third query disagrees with affine family')
    q.compile(source([(a,b)]),dst)
    return dict(queries=3,inputs=[0,1,2],outputs=ys,a=a,b=b,elapsed_ms=(time.perf_counter()-start)*1000,assumption='whole function is affine; three queries do not certify arbitrary binaries')
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=['transform','recover']);ap.add_argument('source',type=Path);ap.add_argument('output',type=Path);ap.add_argument('--mode',choices=['decoder','lift'],default='lift');args=ap.parse_args()
    print(json.dumps(transform(args.source,args.output,args.mode) if args.command=='transform' else recover(args.source,args.output)))
