"""Negative controls for the recovery certificate and trap-state snapshot."""
import copy,json,subprocess,sys
from pathlib import Path
import recover as r
q=r.q
src,out=map(Path,sys.argv[1:]);out.mkdir(parents=True,exist_ok=False)
original=q.read(src/'original-raw.wasm');info=r.analyze(original);records=[]
for name in ('odd-mixer','one-iteration','uncertified-state'):
    m=copy.deepcopy(original);loop=next(x for x in q.walk(m) if x[0]=='loop')
    if name=='odd-mixer':
        changed=0
        for store in loop[1+info['n']:1+2*info['n']]:
            factors=[x for x in q.walk(store) if x[0]=='i32.mul' and x[1]==['i32.const','2']]
            assert len(factors)==1;factors[0][1][1]='1';changed+=1
        assert changed==info['n']
    else:loop[-1][2][-1]=['i32.const','1' if name=='one-iteration' else str(info['bound'])]
    dst=out/(name+'.wasm');q.compile(q.w.emit(m),dst)
    try:r.analyze(q.read(dst))
    except r.Unsupported as e:reason=str(e)
    else:raise AssertionError('unsafe recovery accepted '+name)
    records.append(dict(name=name,rejected=True,reason=reason,sha256=q.digest(dst)))
full=q.read(src/'hash-original-raw.wasm')
index=int(next(x[2][1] for x in full[1:] if x[:2]==['export','"hash"']))
f=[x for x in full[1:] if x[0]=='func'][index]
start=next(i for i,x in enumerate(f[1:],1) if isinstance(x,list) and x[0] not in ('type','param','result','local'))
f.insert(start,['i32.store',['i32.const','0'],['i32.const','0']])
dst=out/'write-before-trap.wasm';q.compile(q.w.emit(full),dst)
q.save(out/'rejections.json',records)
subprocess.run(['node',str(Path(__file__).with_name('controls.cjs')),str(src),str(out)],check=True,timeout=30)
print(json.dumps(records))
