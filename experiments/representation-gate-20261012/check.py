"""Three predeclared mathematical gates. Standard library, bounded exhaustive checks."""
import hashlib, json, platform, random
from pathlib import Path
ROOT=Path(__file__).resolve().parent
if (ROOT/'results.json').exists(): raise SystemExit('Refuse overwrite results.json')
protocol=json.loads((ROOT/'protocol.json').read_text())
rng=random.Random(protocol['seed'])
def rol(x,n,w):
    n%=w;m=(1<<w)-1
    return ((x<<n)|(x>>(w-n)))&m
def ror(x,n,w): return rol(x,w-(n%w),w)
def enc_rotation(x,w): return rol(x,x.bit_count(),w)
def dec_rotation(y,w):
    # Different implementation: bit-string slicing and count, only y is supplied.
    s=f'{y:0{w}b}';n=s.count('1')%w
    return int(s[-n:]+s[:-n],2) if n else y
def profile(x,w): return tuple((((x+(1<<j))&((1<<w)-1))^x) for j in range(w))
def recover_profile(d,top,w):
    return (top<<(w-1))|sum(((d[j]>>(j+1))&1)<<j for j in range(w-1))
small=[]
for w in range(2,9):
    image=set();profiles={};collisions=[]
    for x in range(1<<w):
        y=enc_rotation(x,w);image.add(y);assert dec_rotation(y,w)==x
        d=profile(x,w);profiles.setdefault(d,[]).append(x)
        assert d==profile(x^(1<<(w-1)),w)
        assert recover_profile(d,x>>(w-1),w)==x
    assert len(image)==1<<w
    assert len(profiles)==1<<(w-1) and all(len(v)==2 for v in profiles.values())
    # A rotate continuation distinguishes each merged pair; thus no update from d alone exists.
    for d,pair in profiles.items():
        a,b=pair;assert rol(a,1,w)!=rol(b,1,w)
        collisions.append({'x':a,'other':b,'profile':list(d),'continuation':[rol(a,1,w),rol(b,1,w)]})
    small.append({'width':w,'words':1<<w,'rotation_unique':len(image),'profile_classes':len(profiles),'collision_witnesses':collisions,'repair_errors':0})
xs=sorted(set([0,1,2,3,0x7fffffff,0x80000000,0xfffffffe,0xffffffff]+[n for k in range(32) for n in [max(0,(1<<k)-1),1<<k,min(0xffffffff,(1<<k)+1)]]))
xs += [rng.getrandbits(32) for _ in range(protocol['budget']['random_i32'])]
observations=[]
for x in xs:
    y=enc_rotation(x,32);d=profile(x,32);top=x>>31
    assert dec_rotation(y,32)==x
    assert d==profile(x^0x80000000,32)
    recovered=recover_profile(d,top,32);assert recovered==x
    observations.append({'x':x,'rotated':y,'profile':list(d),'anchor':top,'recovered':recovered})
mask=(1<<32)-1
def big_sigma(x):return ror(x,2,32)^ror(x,13,32)^ror(x,22,32)
def one_round(s,k,w):
    a,b,c,d,e,f,g,h=s
    t1=(h+(ror(e,6,32)^ror(e,11,32)^ror(e,25,32))+((e&f)^((~e)&g))+k+w)&mask
    t2=(big_sigma(a)+((a&b)^(a&c)^(b&c)))&mask
    return [(t1+t2)&mask,a,b,c,(d+t1)&mask,e,f,g]
rounds=[]
for _ in range(4096):
    s=[rng.getrandbits(32) for _ in range(8)];k=rng.getrandbits(32);w=rng.getrandbits(32)
    expected=one_round(s,k,w);a,b,c,d,e,f,g,h=s
    # Candidate computes a' plus r=d-T2, avoiding explicit e'=d+T1 at the cut.
    T2=(big_sigma(a)+((a&b)|(c&(a|b))))&mask
    A=(h+(ror(e,6,32)^ror(e,11,32)^ror(e,25,32))+(g^(e&(f^g)))+k+w+T2)&mask
    R=(d-T2)&mask
    physical=[A,a,b,c,R,e,f,g]
    decoded=physical[:];decoded[4]=(physical[0]+physical[4])&mask
    assert decoded==expected
    rounds.append({'input':s,'k':k,'w':w,'physical':physical,'decoded':decoded,'expected':expected})
(ROOT/'i32-observations.json').write_text(json.dumps(observations),encoding='utf-8')
(ROOT/'round-observations.json').write_text(json.dumps(rounds),encoding='utf-8')
result={'python':platform.python_version(),'seed':protocol['seed'],'small':small,'i32_cases':len(xs),'i32_errors':0,'round_cases':len(rounds),'round_errors':0,'decision':'reject all three as adopted new algorithms','scripts':{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in ['check.py','protocol.json']},'observations':{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in ['i32-observations.json','round-observations.json']}}
(ROOT/'results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({'small_words':sum(r['words'] for r in small),'i32':len(xs),'rounds':len(rounds),'errors':0}))
