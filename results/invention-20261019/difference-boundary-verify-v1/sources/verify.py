"""Independent finite model, another engine, and deliberately incorrect rules."""
import argparse
import itertools
import json
from pathlib import Path
import re
import shutil
import statistics
import time
import prototype as p
from run import save,command,HERE

def hash_bytes(a):
    h=2166136261
    for b in a:h=((h^b)*16777619)&0xffffffff
    return h

def main():
    ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('output',type=Path);o=ap.parse_args();out=o.output;out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
    shutil.copyfile(Path(__file__),out/'sources/verify.py')
    count=0
    for N in range(1,9):
        for values in itertools.product((0,255),repeat=N):
            A=bytes(values);D=p.encode(A,'two')
            for n in range(N+1):
                for s in range(N-n+1):
                    for d in range(N-n+1):
                        expected=bytearray(A);expected[d:d+n]=A[s:s+n];got=bytearray(D)
                        if n:
                            lo,hi=sorted((d,s));c0=c1=0
                            for j in range(lo,hi):c0^=D[j];c1^=D[j+n]
                            got[d:d+n]=D[s:s+n];got[d]^=c0
                            if d+n<N:got[d+n]^=c1
                            if n<hi-lo:
                                l=m=r=0
                                for j in range(lo,lo+n):l^=D[j]
                                for j in range(lo+n,hi):m^=D[j]
                                for j in range(hi,hi+n):r^=D[j]
                                assert (l^m,m^r)==(c0,c1)
                        assert got==p.encode(expected,'two');count+=1
    manifest=json.loads((o.input/'manifest.json').read_text());interpreter=[]
    for q in manifest['files']:
        A=bytearray(manifest['datasets'][q['dataset']]);N=len(A)
        args=[(0,1,3),(N-5,0,5),(N,N,0),(0,N,1),(0xffffffff,1,2),(1,0,N-1)]
        text=p.w.tool('wasm2wat',[o.input/q['path']]);mod=p.w.parse(text)
        exports={x[1]:x[2][1] for x in mod[1:] if x[0]=='export'};cp=exports['"copy"'];dg=exports['"digest"']
        extra='';expected=[]
        for i,(d,s,n) in enumerate(args):
            extra+=f'(func (export "check{i}") (result i32) (call {cp} (i32.const {d}) (i32.const {s}) (i32.const {n})) (call {dg}))'
            trap=d+n>N or s+n>N
            if not trap:A[d:d+n]=bytes(A[s:s+n])
            expected.append('trap' if trap else hash_bytes(A))
        target=out/('interp.'+q['path']);p.c.compile_wat(text.rstrip()[:-1]+extra+')',target)
        log=p.w.tool('wasm-interp',[target,'--run-all-exports']);target.with_suffix('.log').write_text(log,encoding='utf-8')
        got=[]
        for i in range(6):
            line=next(l for l in log.splitlines() if l.startswith('check'+str(i)+'()'))
            got.append(int(line.split('i32:')[1]) if '=> i32:' in line else 'trap')
        assert got==expected,(q,got,expected);interpreter.append(dict(path=q['path'],expected=expected,actual=got))
    # Actual Wasm witnesses, starting each counterexample from fresh state.
    bs=bytes([3,16,29,44,57,78,91,104,117,130,143,156,169,182,195,208])
    normal=p.wat(p.encode(bs,'two'),'two');cp='(memory.copy (local.get $d) (local.get $s) (local.get $n))'
    mutants={
        'omit-start':normal.replace('(i32.xor (i32.load8_u (local.get $d)) (local.get $c0))','(i32.load8_u (local.get $d))'),
        'omit-end':normal.replace('(local.get $c1)))))','(i32.const 0)))))'),
        'late-corrections':normal.replace(cp,'').replace('(local.set $lo',cp+' (local.set $lo',1),
    }
    rt=p.wat(p.encode(bs,'roundtrip'),'roundtrip')
    wrapped=re.sub(r'\(i64.extend_i32_u (\(local.get \$[dsn]\))\)',r'\1',rt)
    mutants['wrap-check']=wrapped.replace('i64.gt_u','i32.gt_u').replace('i64.add','i32.add').replace('i64.const','i32.const')
    cases=[(d,s,n) for n in range(1,17) for d in range(17-n) for s in range(17-n)] + [(0xffffffff,0xffffffff,2)]
    save(out/'negative-inputs.json',dict(initial=list(bs),cases=cases))
    negative=[]
    js='''const fs=require('fs');const j=JSON.parse(fs.readFileSync(process.argv[2]));const m=new WebAssembly.Module(fs.readFileSync(process.argv[1]));let found=null;for(const [d,s,n]of j.cases){let e=new WebAssembly.Instance(m).exports,a=Uint8Array.from(j.initial),want=d+n>a.length||s+n>a.length;if(!want){let old=a.slice(s,s+n);a.set(old,d);}let trapped=false;try{e.copy(d,s,n);}catch(x){trapped=true;}let h=2166136261;for(let x of a)h=Math.imul(h^x,16777619)>>>0;let actual=e.digest()>>>0;if(trapped!==want||actual!==h){found={d,s,n,expectedTrap:want,actualTrap:trapped,expectedDigest:h,actualDigest:actual};break;}}console.log(JSON.stringify(found));'''
    for name,text in mutants.items():
        target=out/(name+'.wasm');p.c.compile_wat(text,target)
        witness=command(['node','-e',js,target,out/'negative-inputs.json']);assert witness,name;negative.append(dict(name=name,**witness))
    refusals=[]
    for name,text in [('export-memory',p.wat(bs,'plain')[:-1]+'(export "memory" (memory 0)))'),('changed-hash',p.wat(bs,'plain').replace('16777619','16777621')),('extra-store',p.wat(bs,'plain').replace(cp,cp+' (i32.store8 (i32.const 0) (i32.const 7))'))]:
        target=out/(name+'.wasm');p.c.compile_wat(text,target)
        try:p.transform(target,out/(name+'.converted.wasm'),'shared');raise AssertionError(name+' accepted')
        except ValueError as e:refusals.append(dict(name=name,error=str(e)))
    timings=[]
    for name,values in manifest['datasets'].items():
        for mode in p.MODES:
            data=p.encode(bytes(values),mode);samples=[]
            for _ in range(11):
                start=time.perf_counter();decoded=p.decode(data,mode);samples.append((time.perf_counter()-start)*1000);assert decoded==bytes(values)
            timings.append(dict(dataset=name,mode=mode,decode_samples_ms=samples,median_ms=statistics.median(samples)))
    result=dict(status='completed',finite_model_checks=count,interpreter_exports_checked=6*len(interpreter),interpreter_traps=sum(sum(x=='trap' for x in q['actual']) for q in interpreter),interpreter=interpreter,negative_witnesses=negative,refusals=refusals,decode_timing=timings)
    save(out/'verification.json',result);print(json.dumps({k:v for k,v in result.items() if k not in ('interpreter','decode_timing')}))

if __name__=='__main__':main()
