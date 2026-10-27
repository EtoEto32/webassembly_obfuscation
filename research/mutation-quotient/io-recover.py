import argparse
import json
from pathlib import Path
import subprocess
import time
import prototype as p


def recover(src,dst,n,k):
    start=time.perf_counter();r=subprocess.run(['node',str(p.HERE/'io-probe.cjs'),str(src),str(n)],capture_output=True,text=True,check=True,timeout=20)
    probe=json.loads(r.stdout);a=time.perf_counter();d=p.erased(k);bits=32-d
    b=(probe['scale']+probe['diffs'][0])&p.MASK
    if b&((1<<d)-1):raise ValueError('API outside the promised affine profile')
    anchor=0 if bits==0 else ((b>>d)*pow(((k-1)&p.MASK)>>d,-1,1<<bits))% (1<<bits)
    xs=[anchor]+[(v+anchor)&p.MASK for v in probe['diffs']];analysis=(time.perf_counter()-a)*1000
    p.q.compile(p.render(xs,k),dst)
    return dict(n=n,k=k,erased_bits=d,queries=probe['queries'],reset_calls=probe['reset_calls'],query_ms=probe['query_ms'],analysis_ms=analysis,total_ms=(time.perf_counter()-start)*1000,initial_representative=xs)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('source');a.add_argument('output');a.add_argument('--n',type=int,required=True);a.add_argument('--k',type=int,required=True);v=a.parse_args();print(json.dumps(recover(v.source,v.output,v.n,v.k),indent=2))
