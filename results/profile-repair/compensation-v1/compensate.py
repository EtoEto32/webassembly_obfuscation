"""Generate profile-conditioned table representations for a fixed Wasm lookup.

This is a limited generator, not a transformer for arbitrary XNNPACK binaries.
The lookup schedule comes from XNNPACK; see LICENSE-XNNPACK in each result.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time
import prototype as p

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];N=16

def coefficient(index,profile,mask):
    out=0;j=index
    for site in range(N):
        if 0<site<=8:j=(j-16)&255
        elif site>8:j=max(-128,(j if j<128 else j-256)-16)&255
        if j<16 or (profile and not (mask>>site)&1 and j<128):out^=1<<site
    return out

def inverse(rows):
    a=[v|(1<<(N+i)) for i,v in enumerate(rows)]
    for col in range(N):
        pivot=next((i for i in range(col,N) if (a[i]>>col)&1),None)
        if pivot is None:raise ValueError('singular coefficient matrix')
        a[col],a[pivot]=a[pivot],a[col]
        for i in range(N):
            if i!=col and (a[i]>>col)&1:a[i]^=a[col]
    assert all(v&65535==1<<i for i,v in enumerate(a))
    return [v>>N for v in a]

def multiply(a,b):
    rows=[]
    for v in a:
        total=0
        for i in range(N):
            if (v>>i)&1:total^=b[i]
        rows.append(total)
    return rows

def certificate(mask):
    if isinstance(mask,bool) or not isinstance(mask,int) or not 0<=mask<=65535:raise ValueError('16-bit strict mask')
    rows=[]
    for profile in (0,1):
        a=[coefficient(i*16,profile,mask) for i in range(N)];e=inverse(a)
        assert multiply(a,e)==[1<<i for i in range(N)]
        assert all(coefficient(x,profile,mask)==a[x//16] for x in range(256))
        rows.append({'profile':profile,'A':a,'E':e,'product':multiply(a,e)})
    known=[1]
    for i in range(1,16):known.append((1<<(i-1))^(1<<i)^(known[i-8] if i>=8 else 0))
    return {'mask':mask,'profiles':rows,'matchesXnnpackR1':rows[1]['E']==known,'matchesIdentityR0':rows[0]['E']==[1<<i for i in range(N)]}

def vector(n):return '(i8x16.splat (i32.const '+str(n)+'))'

def swizzle(data,index,profile,strict=False):
    if strict or profile==0:return '(i8x16.swizzle '+data+' '+index+')'
    if profile==1:return '(i8x16.swizzle '+data+' (v128.and '+index+' '+vector(143)+'))'
    return '(i8x16.relaxed_swizzle '+data+' '+index+')'

def encoding(rows):
    statements=[]
    for i,row in enumerate(rows):
        terms=['(v128.load (i32.const '+str(j*16)+'))' for j in range(N) if (row>>j)&1]
        expr=terms[0]
        for term in terms[1:]:expr='(v128.xor '+expr+' '+term+')'
        statements.append('(v128.store (i32.const '+str(512+i*16)+') '+expr+')')
    return ' '.join(statements)

def source(mask=0,profile=None,kind='adaptive'):
    cert=certificate(mask)
    if kind not in ('adaptive','scalar','strict','dispatch'):raise ValueError(kind)
    probe='(i8x16.extract_lane_u 0 '+swizzle(vector(1),vector(16),profile)+')'
    init=['(func $init (export "init") (result i32) (global.set $profile '+probe+')']
    identity=encoding([1<<i for i in range(N)])
    if kind=='strict':init.append(identity)
    elif kind in ('adaptive','dispatch'):
        init.append('(if (global.get $profile) (then '+encoding(cert['profiles'][1]['E'])+') (else '+encoding(cert['profiles'][0]['E'])+'))')
    init.append('(global.set $ready (i32.const 1)) (global.get $profile))')
    check='(if (i32.or (i32.gt_u (local.get $n) (i32.const 65536)) (i32.or (i32.and (local.get $n) (i32.const 15)) (i32.eqz (global.get $ready)))) (then unreachable))'
    scalar=['(func $scalar (param $n i32) (local $p i32) '+check+' (block $done (br_if $done (i32.eqz (local.get $n))) (loop $loop']
    for lane in range(16):scalar.append('(i32.store8 (i32.add (local.get $p) (i32.const '+str(131072+lane)+')) (i32.load8_u (i32.load8_u (i32.add (local.get $p) (i32.const '+str(1024+lane)+')))))')
    scalar.append('(local.set $p (i32.add (local.get $p) (i32.const 16))) (br_if $loop (i32.lt_u (local.get $p) (local.get $n))))))')
    kernel=['(func $kernel (param $n i32) (local $p i32) (local $x v128) (local $y v128)']
    kernel.extend('(local $d'+str(i)+' v128)' for i in range(N));kernel.append(check)
    kernel.append('(block $done (br_if $done (i32.eqz (local.get $n)))')
    kernel.extend('(local.set $d'+str(i)+' (v128.load (i32.const '+str(512+i*16)+')))' for i in range(N))
    kernel.append('(loop $loop (local.set $x (v128.load (i32.add (local.get $p) (i32.const 1024))))')
    for i in range(N):
        if i:kernel.append('(local.set $x ('+('i8x16.sub' if i<=8 else 'i8x16.sub_sat_s')+' (local.get $x) '+vector(16)+'))')
        expr=swizzle('(local.get $d'+str(i)+')','(local.get $x)',profile,kind=='strict' or bool((mask>>i)&1))
        kernel.append('(local.set $y '+(expr if i==0 else '(v128.xor (local.get $y) '+expr+')')+')')
    kernel.append('(v128.store (i32.add (local.get $p) (i32.const 131072)) (local.get $y)) (local.set $p (i32.add (local.get $p) (i32.const 16))) (br_if $loop (i32.lt_u (local.get $p) (local.get $n))))))')
    call='(call $scalar (local.get $n))' if kind=='scalar' else '(call $kernel (local.get $n))'
    if kind=='dispatch':call='(if (global.get $profile) (then (call $kernel (local.get $n))) (else (call $scalar (local.get $n))))'
    return '(module (memory (export "memory") 4 4) (global $ready (mut i32) (i32.const 0)) (global $profile (mut i32) (i32.const 0)) '+' '.join(init+scalar+kernel)+' (func (export "run") (param $n i32) '+call+'))'

def instrument(mod):
    result=copy.deepcopy(mod);sites=[]
    for node in list(p.walk(result)):
        if node[0] in ('v128.load','v128.store','i32.load8_u','i32.store8'):
            sid=len(sites);sites.append({'id':sid,'op':node[0]});node[1]=['call','$trace',['i32.const',str(sid)],node[1]]
    result.insert(1,['import','"env"','"trace"',['func','$trace',['param','i32','i32'],['result','i32']]])
    return result,sites

def main(out):
    out.mkdir(parents=True,exist_ok=False);(out/'wasm').mkdir();start=time.perf_counter()
    for name in ('compensate.py','compensation-plan.md'):shutil.copy2(HERE/name,out/name)
    shutil.copy2(ROOT/'.tools/xnnpack-c754a15/LICENSE',out/'LICENSE-XNNPACK')
    try:
        rows=[]
        for profile in (None,0,1):
            for name,mask,kind in [('adaptive',0,'adaptive'),('first',1,'adaptive'),('alternating',0x5555,'adaptive'),('all_mask',65535,'adaptive'),('strict',0,'strict'),('scalar',0,'scalar'),('dispatch',0,'dispatch')]:
                mode=name+'-'+('native' if profile is None else str(profile));mod=p.w.parse(source(mask,profile,kind));file=out/'wasm'/(mode+'.wasm');p.compile_mod(mod,file)
                traced,sites=instrument(mod);p.compile_mod(traced,out/'wasm'/(mode+'-trace.wasm'))
                optimized=out/'wasm'/(mode+'-O3.wasm')
                run=subprocess.run([str(ROOT/'.tools/binaryen-version_133/bin/wasm-opt.exe'),str(file),'-O3','--enable-simd','--enable-relaxed-simd','-o',str(optimized)],capture_output=True,text=True,timeout=30)
                if run.returncode:raise RuntimeError(run.stderr)
                p.w.tool('wasm-validate',[optimized])
                effective=65535 if kind=='strict' else mask
                rows.append({'mode':mode,'kind':kind,'mask':effective,'profile':profile,'certificate':certificate(effective) if kind!='scalar' else None,'file':file.name,'optimized':optimized.name,'trace':mode+'-trace.wasm','traceSites':sites,'bytes':file.stat().st_size,'optimizedBytes':optimized.stat().st_size})
        report={'rows':rows,'generationSeconds':time.perf_counter()-start,'directory':str(out/'wasm'),'scope':'Fixed lookup generator. Constant linear-memory address schedule is a Wasm-level property, not a physical constant-time proof. Source table must not change between init and run.'}
        (out/'results.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps({'binaries':len(rows)*3,'seconds':report['generationSeconds'],'R1_unmodified_matches_existing':certificate(0)['matchesXnnpackR1']}))
    finally:(out/'sha256.json').write_text(json.dumps({str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest() for f in out.rglob('*') if f.is_file() and f.name!='sha256.json'},indent=2),encoding='utf8')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);a=ap.parse_args();main(a.output.resolve())
