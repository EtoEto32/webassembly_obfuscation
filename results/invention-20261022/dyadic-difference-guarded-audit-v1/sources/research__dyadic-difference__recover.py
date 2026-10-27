"""Binary-only discrete integration; no division by even units modulo 2**32."""
import argparse,math,tempfile,time
from pathlib import Path
import prototype as p


def integrate(delta,initial):
    # Newton coefficient k! b_k = Delta^(k-1) delta(0).
    values=[p.evaluate(delta,i) for i in range(len(delta))]
    result=[initial];basis=[1];steps=[]
    for k in range(1,len(delta)+1):
        number=values[0];fact=math.factorial(k);power=(fact&-fact).bit_length()-1
        if power>=32:raise ValueError('factorial precision exhausted')
        if number % (1<<power):raise ValueError('no integral polynomial antiderivative')
        modulus=1<<(32-power);odd=fact>>power
        coeff=((number>>power)*pow(odd,-1,modulus))%modulus
        basis=p.mul(basis,[-(k-1),1]);result=p.add(result,p.mul([coeff],basis))
        steps.append(dict(k=k,forward_difference=number,factorial_v2=power,coefficient=coeff,modulus=modulus))
        values=[(values[i+1]-values[i])&p.MASK for i in range(len(values)-1)]
    return result,steps


def inspect(src):
    m=p.q.read(src)
    if any(e[0] not in ('type','func','table','elem','export') for e in m[1:]):raise ValueError('closed pure module')
    fs=[e for e in m[1:] if e[0]=='func'];tables=[e for e in m[1:] if e[0]=='table'];els=[e for e in m[1:] if e[0]=='elem']
    if tables!=[['table','32','32','funcref']] or len(els)!=1 or els[0][1:3]!=[['i32.const','0'],'func'] or len(els[0][3:])!=32:raise ValueError('fixed 32-entry table')
    indices=list(map(int,els[0][3:]));exports=[e for e in m[1:] if e[0]=='export']
    if len(exports)!=1 or exports[0][1]!='"run"' or exports[0][2][0]!='func':raise ValueError('single run')
    runidx=int(exports[0][2][1]);run=fs[runidx]
    if runidx in indices or set(indices+[runidx])!=set(range(len(fs))):raise ValueError('unexpected function')
    consts={int(e[2][1],0)&p.MASK for e in p.q.walk(run) if e[0] in ('local.set','local.tee') and len(e)==3 and e[2][0]=='i32.const' and int(e[2][1],0) not in (0,1,32)}
    if len(consts)!=1:raise ValueError('one nontrivial initial accumulator')
    return m,fs,indices,runidx,next(iter(consts))


def verify_driver(m,fs,indices,runidx,initial):
    hs=[p.q.w.emit(['func',*[e for e in fs[i][1:] if e[0]!='type']]) for i in indices]
    with tempfile.TemporaryDirectory(dir=p.ROOT/'tmp',prefix='difference-driver-') as td:
        raw=Path(td)/'raw.wasm';opt=Path(td)/'O3.wasm';p.q.compile(p.assemble(hs,initial),raw)
        ref=p.q.read(raw)
        if ref==m:return 'raw-canonical'
        p.q.tool('wasm-opt',[raw,'-O3','-o',opt]);ref=p.q.read(opt)
        # Optimizing already optimized helpers can change their syntax again.
        rfs=[e for e in ref[1:] if e[0]=='func'];ridx=int(next(e[2][1] for e in ref[1:] if e[0]=='export'))
        if len(rfs)==len(fs) and ridx==runidx and rfs[ridx]==fs[runidx] and [e for e in ref[1:] if e[0] in ('type','table','elem','export')]==[e for e in m[1:] if e[0] in ('type','table','elem','export')]:return 'O3-canonical'
        raise ValueError('driver outside canonical form')


def recover(src,dst):
    start=time.perf_counter();m,fs,indices,runidx,initial=inspect(src);read=time.perf_counter()
    polys=[p.polynomial(fs[i]) for i in indices]
    if not 1<=len(polys[0])<=12:raise ValueError('difference degree limit')
    driver=verify_driver(m,fs,indices,runidx,initial);parsed=time.perf_counter()
    a,steps=integrate(polys[0],initial)
    # Coefficient identity is sufficient but stronger than function identity.
    # Ambiguous factorial divisions may yield a null-polynomial difference.
    def zero_function(poly):
        vals=[p.evaluate(poly,x) for x in range(len(poly))]
        witnesses=[]
        while vals:
            witnesses.append(vals[0]);vals=[(vals[i+1]-vals[i])&p.MASK for i in range(len(vals)-1)]
        return all(x==0 for x in witnesses),witnesses
    certificates=[]
    for i,poly in enumerate(polys):
        residual=p.add(p.difference(a,1<<i),poly,-1)
        okay,newton=zero_function(residual)
        if not okay:raise ValueError('inconsistent step '+str(i))
        certificates.append(dict(step=i,formal_coefficients_zero=residual==[0],newton_differences=newton))
    certified=time.perf_counter();p.q.compile(p.source(a),dst);end=time.perf_counter()
    return dict(driver=driver,degree=len(a)-1,coefficients=a,integration=steps,certificates=certificates,
                original_code_or_coefficients_used=False,original_api_queries=0,
                read_ms=(read-start)*1000,parse_verify_ms=(parsed-read)*1000,integration_certificate_ms=(certified-parsed)*1000,
                emit_ms=(end-certified)*1000,total_ms=(end-start)*1000)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source');ap.add_argument('output');a=ap.parse_args();p.q.save(str(a.output)+'.json',recover(a.source,a.output))
