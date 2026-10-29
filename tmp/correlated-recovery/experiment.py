import hashlib
import itertools
import json
import platform
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parent
SOURCE=Path(sys.argv[1])

def coefficients(s,w):
    a,b,c,d=s
    mask=(1<<w)-1
    return [v&mask for v in (a+c,b+d,a*c,b*d,a*d+c*b)]

def step(s,u,w):
    mask=(1<<w)-1
    left,right=s[:2],s[2:]
    choose=((left[0]+right[0])^(left[1]+right[1]))&1
    offset=u if choose else u+1
    out=[]
    for x,y in (left,right):
        out.extend(((x+y*y+offset)&mask,(y+x*x)&mask))
    return out

def orbit(s):
    return min(tuple(s),tuple(s[2:]+s[:2]))

if (ROOT/'observations.json').exists():
    raise SystemExit('Fresh directory required.')
saved=json.loads((SOURCE/'results.json').read_text())
blob=(SOURCE/'inputs32.json').read_bytes()
assert hashlib.sha256(blob).hexdigest()==saved['inputs_sha256']
observations=[]
private=[]
seen=set()
for s in itertools.product(range(8),repeat=4):
    c=coefficients(s,3)
    if tuple(c) in seen: continue
    seen.add(tuple(c))
    rid=f'small-{len(seen)-1}'
    observations.append(dict(id=rid,width=3,coeff=c))
    private.append(dict(id=rid,width=3,state=list(s),future_input=0))
for i,(s,u) in enumerate(json.loads(blob)):
    for j in range(4): s=step(s,(u+j)&0xffffffff,32)
    rid=f'large-{i}'
    observations.append(dict(id=rid,width=32,coeff=coefficients(s,32)))
    private.append(dict(id=rid,width=32,state=s,future_input=(u+4)&0xffffffff))
(ROOT/'observations.json').write_text(json.dumps(observations)+'\n')
(ROOT/'verifier-only.json').write_text(json.dumps(private)+'\n')
subprocess.run([sys.executable,str(ROOT/'observer.py'),str(ROOT/'observations.json'),str(ROOT/'recovered.jsonl')],check=True,timeout=180)
recovered=[json.loads(line) for line in (ROOT/'recovered.jsonl').read_text().splitlines()]
assert len(recovered)==len(observations)
summary={3:dict(success=0,budget=0,original_orbit=0,alternative_orbit=0,calls=0,future_checks=0),
        32:dict(success=0,budget=0,original_orbit=0,alternative_orbit=0,calls=0,future_checks=0)}
for ob,pr,rec in zip(observations,private,recovered):
    assert ob['id']==pr['id']==rec['id']
    st=summary[ob['width']]
    st['calls']+=rec['calls']
    if rec['status']=='budget': st['budget']+=1; continue
    assert rec['status']=='success'
    st['success']+=1
    r=rec['recovered']
    assert coefficients(r,ob['width'])==ob['coeff']
    st['original_orbit' if orbit(r)==orbit(pr['state']) else 'alternative_orbit']+=1
    s=pr['state']
    for j in range(8):
        u=(pr['future_input']+j)&((1<<ob['width'])-1)
        r=step(r,u,ob['width']); s=step(s,u,ob['width'])
        assert coefficients(r,ob['width'])==coefficients(s,ob['width'])
        st['future_checks']+=1
result=dict(python=platform.python_version(),source_inputs_sha256=saved['inputs_sha256'],
    observation_sha256=hashlib.sha256((ROOT/'observations.json').read_bytes()).hexdigest(),
    limit=100000,summary=summary,mismatches=0,
    scope='Known coefficient representation; separate observer process, not filesystem isolation or unknown-Wasm identification.')
(ROOT/'results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
