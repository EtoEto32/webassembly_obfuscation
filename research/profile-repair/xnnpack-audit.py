"""Reduced XNNPACK lookup body: relational proof and real Wasm mutation audit.

Not a build of the original C library. The vector algorithm is transcribed from
XNNPACK (Google LLC 2022), whose BSD license is copied into each output folder.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import random
import shutil
import subprocess
import time
import prototype as p

z=p.z;HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
X=z.BitVec('lookup_index',8);T=[z.BitVec('column_'+str(i),8) for i in range(16)]

def symbolic(h,r):
    expected=T[0]
    for i in range(1,16):expected=z.If(z.LShR(X,4)==i,T[i],expected)
    delta=[T[0]]
    for i in range(1,16):delta.append(T[i-1]^T[i]^(delta[i-8] if i>=8 else z.BitVecVal(0,8)))
    index=X;value=z.BitVecVal(0,8)
    for i in range(16):
        if 0<i<=8:index=index-16
        elif i>8:index=z.If(index<z.BitVecVal(-112,8),z.BitVecVal(-128,8),index-16)
        valid=z.Or(z.ULT(index,16),z.And(z.Not(h[i+1]),r[i+1],z.ULT(index,128)))
        value=value^z.If(valid,delta[i],z.BitVecVal(0,8))
    return z.If(z.And(z.Not(h[0]),r[0]),value,expected),expected

def check(selected,independent=False):
    profile=[z.Bool('lookup_R_'+str(i if independent else 0)) for i in range(17)]
    actual,expected=symbolic([i in selected for i in range(17)],profile)
    s=z.Solver();s.set(timeout=15000);s.add(actual!=expected);start=time.perf_counter();status=s.check()
    result={'status':str(status),'seconds':time.perf_counter()-start}
    if status==z.unknown:raise RuntimeError(s.reason_unknown())
    if status==z.sat:
        m=s.model();result.update(x=m.eval(X,model_completion=True).as_long(),tableColumn=[m.eval(t,model_completion=True).as_long() for t in T],profiles=[z.is_true(m.eval(r,model_completion=True)) for r in profile],actual=m.eval(actual).as_long(),expected=m.eval(expected).as_long())
    return result

def synthesize(independent):
    h=[z.Bool('lookup_h_'+str(i)) for i in range(17)];constraints=[];steps=[];start=time.perf_counter()
    for iteration in range(128):
        o=z.Optimize();o.set(timeout=15000);o.add(*constraints);o.minimize(z.Sum([z.If(v,1,0) for v in h]));o.minimize(z.Sum([z.If(v,1<<i,0) for i,v in enumerate(h)]))
        if o.check()!=z.sat:raise RuntimeError('optimizer did not solve')
        m=o.model();selected=[i for i,v in enumerate(h) if z.is_true(m.eval(v,model_completion=True))];witness=check(selected,independent);steps.append({'selected':selected,'query':witness})
        if witness['status']=='unsat':return {'selected':selected,'cost':len(selected),'steps':steps,'seconds':time.perf_counter()-start}
        actual,expected=symbolic(h,[z.BoolVal(v) for v in witness['profiles']])
        substitutions=[(X,z.BitVecVal(witness['x'],8))]+[(t,z.BitVecVal(v,8)) for t,v in zip(T,witness['tableColumn'])]
        constraints.append(z.simplify(z.substitute(actual==expected,*substitutions)))
    raise RuntimeError('iteration limit')

def vec(n):return '(i8x16.splat (i32.const '+str(n)+'))'

def module_text():
    # One static relaxed probe instruction, executed for all 256 byte indices.
    probe='''(func $probe (export "probe") (result i32) (local $index v128) (local $diff v128) (local $n i32)
      (local.set $index (v128.const i8x16 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15))
      (loop $again
        (local.set $diff (v128.or (local.get $diff) (v128.xor
          (i8x16.swizzle (v128.const i8x16 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16) (v128.and (local.get $index) (i8x16.splat (i32.const 143))))
          (i8x16.relaxed_swizzle (v128.const i8x16 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16) (local.get $index)))))
        (local.set $index (i8x16.add (local.get $index) (i8x16.splat (i32.const 16))))
        (local.set $n (i32.add (local.get $n) (i32.const 1)))
        (br_if $again (i32.lt_u (local.get $n) (i32.const 16))))
      (i32.eqz (v128.any_true (local.get $diff))))'''
    kernel=['(func $kernel (local $x v128) (local $y v128)']
    kernel.extend('(local $t'+str(i)+' v128) (local $d'+str(i)+' v128)' for i in range(16))
    kernel.extend('(local.set $t'+str(i)+' (v128.load (i32.const '+str(16*i)+')))' for i in range(16))
    for i in range(16):
        expr='(local.get $t0)' if i==0 else '(v128.xor (local.get $t'+str(i-1)+') (local.get $t'+str(i)+'))'
        if i>=8:expr='(v128.xor '+expr+' (local.get $d'+str(i-8)+'))'
        kernel.append('(local.set $d'+str(i)+' '+expr+')')
    kernel.append('(local.set $x (v128.load (i32.const 256)))')
    for i in range(16):
        if i:kernel.append('(local.set $x ('+('i8x16.sub' if i<=8 else 'i8x16.sub_sat_s')+' (local.get $x) '+vec(16)+'))')
        term='(i8x16.relaxed_swizzle (local.get $d'+str(i)+') (local.get $x))'
        kernel.append('(local.set $y '+(term if not i else '(v128.xor (local.get $y) '+term+')')+')')
    kernel.append('(v128.store (i32.const 512) (local.get $y)))')
    fallback='(func $fallback '+' '.join('(i32.store8 (i32.const '+str(512+i)+') (i32.load8_u (i32.load8_u (i32.const '+str(256+i)+'))))' for i in range(16))+')'
    return '(module (memory (export "memory") 1 1) '+probe+' '+' '.join(kernel)+' '+fallback+' (func (export "run") (if (call $probe) (then (call $kernel)) (else (call $fallback)))))'

def main(sources,out):
    out.mkdir(parents=True,exist_ok=False);(out/'wasm').mkdir();(out/'sources').mkdir()
    for name in ('xnnpack-audit.py','xnnpack-run.cjs','xnnpack-plan.md'):shutil.copy2(HERE/name,out/'sources'/name)
    shutil.copy2(sources/'LICENSE',out/'LICENSE-XNNPACK');shutil.copy2(sources/'provenance.json',out/'source-provenance.json')
    start=time.perf_counter()
    try:
        source=out/'wasm/source.wasm';p.compile_mod(p.w.parse(module_text()),source)
        # Re-read the compiled binary before mutating it, rather than generating each mode separately.
        mod=p.w.parse(p.w.tool('wasm2wat',[source,'--fold-exprs']))
        sites=[e for e in p.walk(mod) if e[0]==p.RELAXED];assert len(sites)==17
        modes={'source':[],'all':list(range(17)),'probe':[0],'kernel_all':list(range(1,17))}
        modes.update({'kernel_'+str(i):[i+1] for i in range(16)})
        rows=[]
        for mode,selected in modes.items():
            query=check(selected);files={}
            for profile in ('native','0','1'):
                target=copy.deepcopy(mod)
                for sid,node in enumerate(e for e in p.walk(target) if e[0]==p.RELAXED):
                    if sid in selected or profile=='0':node[0]=p.STRICT
                    elif profile=='1':node[0]=p.STRICT;node[2]=['v128.and',node[2],['i8x16.splat',['i32.const','143']]]
                dest=out/'wasm'/(mode+'-'+profile+'.wasm');p.compile_mod(target,dest);files[profile]=dest.name
            rows.append({'mode':mode,'selected':selected,'query':query,'files':files})
        rng=random.Random(2026102425)
        tables=[[0]*256,list(range(256)),list(reversed(range(256))),[255]*256]
        tables.extend([[1 if i==j else 0 for i in range(256)] for j in range(256)])
        tables.extend([[rng.randrange(256) for i in range(256)] for _ in range(16)])
        request={'directory':str(out/'wasm'),'rows':rows,'tables':tables,'seed':2026102425}
        (out/'input.json').write_text(json.dumps(request),encoding='utf8')
        command=['node',str(HERE/'xnnpack-run.cjs'),str(out/'input.json')];run=subprocess.run(command,capture_output=True,text=True,timeout=90)
        (out/'raw.json').write_text(json.dumps({'command':command,'returncode':run.returncode,'stdout':run.stdout,'stderr':run.stderr},indent=2),encoding='utf8')
        if run.returncode:raise RuntimeError(run.stderr)
        concrete=json.loads(run.stdout)
        for row in rows:
            records=[r for r in concrete['rows'] if r['mode']==row['mode']]
            if row['query']['status']=='unsat':assert all(r['mismatchBlocks']==0 for r in records),row['mode']
            else:assert next(r for r in records if r['profile']=='1')['mismatchBlocks']>0,row['mode']
        report={'rows':rows,'aware':synthesize(False),'independent':synthesize(True),'concrete':concrete,'elapsedSeconds':time.perf_counter()-start,
          'scope':'Reduced u16 body and complete probe, scalar lookup fallback; no full C build, tail, is_x86 or init-once. Actual x86 config selects u32. One arbitrary table column in SMT is sufficient because offsets are multiples of 16 and saturated negative indices produce zero; all 16 residues are also tested concretely.',
          'securityInterpretation':'Mutated binaries deliberately violate the original dispatch contract. No XNNPACK bug or exploitation claim.'}
        (out/'results.json').write_text(json.dumps(report,indent=2),encoding='utf8')
        print(json.dumps({'aware':report['aware']['selected'],'independent':report['independent']['selected'],'safeModes':[r['mode'] for r in rows if r['query']['status']=='unsat'],'calls':concrete['calls'],'outputBytesChecked':concrete['outputBytesChecked'],'seconds':report['elapsedSeconds']}))
    finally:
        (out/'sha256.json').write_text(json.dumps({str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest() for f in out.rglob('*') if f.is_file() and f.name!='sha256.json'},indent=2),encoding='utf8')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();main(a.source.resolve(),a.output.resolve())
