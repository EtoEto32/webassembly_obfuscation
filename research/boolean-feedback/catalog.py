"""Exhaustive classification for three Boolean coordinates, fixed order."""
import collections
import hashlib
import json
from pathlib import Path
import struct
import sys
import time
import screen


def main(output):
    out=Path(output).resolve();out.mkdir(parents=True,exist_ok=False);fs=list(screen.triangular(3));valid=[];bounds=collections.Counter();reject=collections.Counter();checks=0;start=time.perf_counter()
    for code in range(1<<21):
        N=[0]+[(code>>(3*i))&7 for i in range(7)]
        bound=0;failed=False
        for fi,(tables,f) in enumerate(fs):
            checks+=1;target=next(s for s in range(8) if f[s]==s);h=[f[s]^N[s^f[s]] for s in range(8)];ok,detail=screen.converges(h,target)
            if not ok:reject[fi]+=1;failed=True;break
            bound=max(bound,detail)
        if not failed:valid.append({'code':code,'N':N,'bound':bound,'prefix':screen.prefix(3,N)});bounds[bound]+=1
        if (code+1)%262144==0:print(json.dumps({'screened':code+1,'valid':len(valid),'elapsed_s':time.perf_counter()-start}),flush=True)
    (out/'valid.json').write_text(json.dumps(valid,indent=2));(out/'valid-codes.u32').write_bytes(struct.pack('<'+'I'*len(valid),*[r['code'] for r in valid]))
    result={'dimension':3,'feedback_maps':1<<21,'triangular_maps':len(fs),'pair_checks':checks,'valid_count':len(valid),'prefix_count':sum(r['prefix'] for r in valid),'bounds':dict(bounds),'first_reject_source_indices':dict(reject),'elapsed_s':time.perf_counter()-start,'valid_codes_sha256':hashlib.sha256((out/'valid-codes.u32').read_bytes()).hexdigest()}
    (out/'summary.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))

if __name__=='__main__':main(sys.argv[1])
