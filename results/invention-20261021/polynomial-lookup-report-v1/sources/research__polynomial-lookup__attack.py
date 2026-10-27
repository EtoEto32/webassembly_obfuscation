"""Known-format extraction; only binary, family and public attack RNG seed as inputs."""
import json,struct,sys,time
import prototype as p
file,mode=sys.argv[1:3];seed=int(sys.argv[3]) if len(sys.argv)>3 else 271021
if mode=='poly':r=p.recover(file,seed=seed)
else:
    t=time.perf_counter();m=p.q.read(file);t1=time.perf_counter();mem=p.data_memory(m)
    fs=[e for e in m[1:] if e[0]=='func']
    if len(fs)!=1:raise p.q.Unsupported('single array lookup required')
    bounds=[int(e[2][1]) for e in p.q.walk(fs[0]) if e[0] in ('i32.lt_u','i32.ge_u')
            and len(e)==3 and e[1]==['local.get','1'] and e[2][:1]==['i32.const']]
    if len(bounds)!=1 or not 64<=bounds[0]<=4160 or (bounds[0]-64)%8:raise p.q.Unsupported('array bound')
    items=[list(struct.unpack_from('<II',mem,a)) for a in range(64,bounds[0],8)]
    t2=time.perf_counter();r=dict(items=items,read_ms=(t1-t)*1000,factor_and_evaluate_ms=(t2-t1)*1000,analysis_ms=(t2-t)*1000)
print(json.dumps(r))
