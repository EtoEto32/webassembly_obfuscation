"""34 public queries under the known one-variable polynomial-function promise."""
import argparse,json,subprocess,time
from pathlib import Path
import prototype as p
import recover as r


def recover(src,dst):
    start=time.perf_counter()
    run=subprocess.run(['node',str(Path(__file__).with_name('query.cjs')),str(src)],capture_output=True,text=True,timeout=30)
    if run.returncode:raise RuntimeError(run.stderr)
    query=json.loads(run.stdout);sampled=time.perf_counter();ys=[v['y'] for v in query['samples']]
    delta=[(ys[i+1]-ys[i])&p.MASK for i in range(33)]
    # Integrate accepts polynomial coefficients, so the known Newton samples
    # are converted here directly instead of reinterpreted as coefficients.
    import math
    result=[ys[0]];basis=[1];steps=[];values=delta
    for k in range(1,34):
        d=values[0];f=math.factorial(k);v=(f&-f).bit_length()-1;mod=1<<(32-v)
        if d%(1<<v):raise ValueError('samples violate integral polynomial promise')
        b=((d>>v)*pow(f>>v,-1,mod))%mod
        basis=p.mul(basis,[-(k-1),1]);result=p.add(result,p.mul([b],basis))
        steps.append(dict(k=k,forward_difference=d,factorial_v2=v,coefficient=b,modulus=mod))
        values=[(values[i+1]-values[i])&p.MASK for i in range(len(values)-1)]
    for x,y in zip(range(34),ys):assert p.evaluate(result,x)==y
    integrated=time.perf_counter();p.q.compile(p.source(result),dst);end=time.perf_counter()
    return dict(query=query,coefficients=result,degree=len(result)-1,integration=steps,
                input_used='Wasm public run API only; no source, coefficients, helper analysis or manifest',
                guarantee='conditional on the known integer-polynomial-function promise; finite samples do not establish the promise',
                sample_ms=(sampled-start)*1000,integration_ms=(integrated-sampled)*1000,emit_ms=(end-integrated)*1000,total_ms=(end-start)*1000)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source');ap.add_argument('output');a=ap.parse_args();p.q.save(str(a.output)+'.json',recover(a.source,a.output))
