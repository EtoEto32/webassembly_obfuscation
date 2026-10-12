"""Tensor representation prototype and independent word-level validation."""
import hashlib, itertools, json, platform, random, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'artifacts'
if OUT.exists():raise SystemExit('Refuse overwrite artifacts')
OUT.mkdir();P=1<<32
protocol=json.loads((ROOT/'protocol.json').read_text())
def write(name,v): (OUT/name).write_text(json.dumps(v,indent=2))
def matrix(rng):
    while True:
        a,b,c,d=[rng.getrandbits(32) for _ in range(4)]
        determinant=(a*d-b*c)%P
        if determinant&1:
            q=pow(determinant,-1,P)
            return [[a,b],[c,d]],[[d*q%P,-b*q%P],[-c*q%P,a*q%P]]
def tensor_eval(t,a,b):
    # Explicit independent contraction rather than recover.py's index loop.
    products=[a[0]*b[0],a[0]*b[1],a[1]*b[0],a[1]*b[1]]
    return [sum(v*x for v,x in zip(row,products))%P for row in t]
def build(width,seed,plain=False):
    rng=random.Random(seed);nodes=[];bases={};inverses={};private=[]
    def alloc():
        name=f'n{rng.getrandbits(96):024x}'
        assert name not in bases
        m,inv=([[1,0],[0,1]],[[1,0],[0,1]]) if plain else matrix(rng)
        bases[name]=m;inverses[name]=inv;return name
    inputs=[]
    for _ in range(width*2):
        n=alloc();inputs.append({'id':n,'columns':[[bases[n][0][b],bases[n][1][b]] for b in range(2)]})
    zero=alloc();constants=[{'id':zero,'value':[bases[zero][0][0],bases[zero][1][0]]}]
    def gate(op,a,b):
        n=alloc();truth={'xor':[0,1,1,0],'and':[0,0,0,1],'or':[0,1,1,1]}[op]
        ia,ib=inverses[a],inverses[b];m=bases[n]
        t=[[sum(m[r][truth[2*x+y]]*ia[x][i]*ib[y][j] for x in range(2) for y in range(2))%P for i in range(2) for j in range(2)] for r in range(2)]
        for x,y in itertools.product(range(2),repeat=2):
            actual=tensor_eval(t,[bases[a][r][x] for r in range(2)],[bases[b][r][y] for r in range(2)])
            assert actual==[m[r][truth[2*x+y]] for r in range(2)]
        nodes.append({'id':n,'parents':[a,b],'tensor':t});private.append({'id':n,'op':op,'parents':[a,b]});return n
    def add(a,b):
        carry=zero;result=[]
        for x,y in zip(a,b):
            xy=gate('xor',x,y);result.append(gate('xor',xy,carry))
            carry=gate('or',gate('and',x,y),gate('and',xy,carry))
        return result
    def rotate(a,n):return [a[(i-n)%width] for i in range(width)]
    x=[a['id'] for a in inputs[:width]];y=[a['id'] for a in inputs[width:]]
    s=add(x,y)
    left=[gate('xor',a,gate('and',b,c)) for a,b,c in zip(rotate(s,7),x,y)]
    right=[gate('xor',a,b) for a,b in zip(x,rotate(y,13))]
    result=add(left,right)
    outputs=[{'id':n,'decoder':inverses[n][1]} for n in result]
    rng.shuffle(nodes)
    assert len(nodes)<=protocol['limits']['maximum_nodes']
    return {'modulus':P,'inputs':inputs,'constants':constants,'nodes':nodes,'outputs':outputs},{'width':width,'seed':seed,'bases':bases,'nodes':private,'outputs':result}
def execute_recovered(p,x,y,width):
    vals={n:(x>>i)&1 for i,n in enumerate(p['inputs'][:width])}
    vals.update({n:(y>>i)&1 for i,n in enumerate(p['inputs'][width:])});vals.update(p['constants'])
    for n in p['nodes']:
        a,b=n['parents'];vals[n['id']]=n['table'][vals[a]][vals[b]]
    return sum(o['table'][vals[o['id']]]<<i for i,o in enumerate(p['outputs']))
def execute_public(public,recovered,x,y,width):
    vals={}
    for i,n in enumerate(public['inputs']):vals[n['id']]=n['columns'][((x if i<width else y)>>(i%width))&1]
    for n in public['constants']:vals[n['id']]=n['value']
    nodes={n['id']:n for n in public['nodes']}
    for order in recovered['nodes']:
        n=nodes[order['id']];a,b=n['parents'];vals[n['id']]=tensor_eval(n['tensor'],vals[a],vals[b])
    bits=[sum(a*b for a,b in zip(o['decoder'],vals[o['id']]))%P for o in public['outputs']]
    assert set(bits)<={0,1}
    return sum(b<<i for i,b in enumerate(bits))
def reference(x,y,w):
    mask=(1<<w)-1
    def rol(z,n):n%=w;return ((z<<n)|(z>>(w-n)))&mask
    return ((rol((x+y)&mask,7)^(x&y))+(x^rol(y,13)))&mask
rows=[]
for width in protocol['widths']:
 for seed in protocol['seeds']:
    public,private=build(width,seed);stem=f'w{width}-s{seed}'
    write(stem+'.public.json',public);write(stem+'.private.json',private)
    subprocess.run([sys.executable,str(ROOT/'recover.py'),str(OUT/(stem+'.public.json')),str(OUT/(stem+'.recovered.json'))],check=True,timeout=30)
    recovered=json.loads((OUT/(stem+'.recovered.json')).read_text());assert recovered['status']=='reconstructed'
    if width==3:cases=list(itertools.product(range(8),repeat=2))
    else:
        boundaries=[0,1,2,31,0x7fffffff,0x80000000,0xfffffffe,0xffffffff]
        rr=random.Random(seed^0x54454e53)
        cases=list(itertools.product(boundaries,repeat=2))+[(rr.getrandbits(32),rr.getrandbits(32)) for _ in range(256)]
    outcomes=[]
    for x,y in cases:
        expected=reference(x,y,width);actual=execute_public(public,recovered,x,y,width);compact=execute_recovered(recovered,x,y,width)
        assert actual==expected==compact
        outcomes.append([x,y,expected,actual,compact])
    # Exhaustive local support certificate, with a separately written evaluator.
    lookup={n['id']:n for n in public['nodes']};certificate=0
    for n in recovered['nodes']:
        a,b=n['parents'];sa=recovered['support'][a];sb=recovered['support'][b]
        for i,u in enumerate(sa):
            for j,v in enumerate(sb):
                assert tensor_eval(lookup[n['id']]['tensor'],u,v)==recovered['support'][n['id']][n['table'][i][j]];certificate+=1
    write(stem+'.checks.json',outcomes)
    rows.append({'name':stem,'width':width,'seed':seed,'nodes':len(public['nodes']),'local_compiler_rows':4*len(public['nodes']),'support_rows':certificate,'cases':len(cases),'errors':0,'max_support':max(map(len,recovered['support'].values())),'attack_seconds':recovered['seconds']})
# Positive control: one-hot version uses identical construction with identity matrices.
public,_=build(3,271,plain=True);write('plain.public.json',public)
subprocess.run([sys.executable,str(ROOT/'recover.py'),str(OUT/'plain.public.json'),str(OUT/'plain.recovered.json')],check=True,timeout=30)
plain=json.loads((OUT/'plain.recovered.json').read_text());assert plain['status']=='reconstructed'
for x,y in itertools.product(range(8),repeat=2):assert execute_recovered(plain,x,y,3)==reference(x,y,3)
# Negative control: four unique outputs from four one-hot input pairs.
negative={'modulus':P,'inputs':[{'id':n,'columns':[[1,0],[0,1]]} for n in ['x','y']],'constants':[],'nodes':[{'id':'z','parents':['x','y'],'tensor':[[0,1,2,3],[4,5,6,7]]}],'outputs':[]}
write('negative.public.json',negative)
subprocess.run([sys.executable,str(ROOT/'recover.py'),str(OUT/'negative.public.json'),str(OUT/'negative.recovered.json')],check=True,timeout=30)
negative_result=json.loads((OUT/'negative.recovered.json').read_text());assert negative_result['status']=='outside-two-state-model'
write('results.json',{'python':platform.python_version(),'rows':rows,'positive_control_cases':64,'negative_control':negative_result,'decision':'reject this tensor-basis-only construction','scripts':{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in ['protocol.json','recover.py','experiment.py']}})
print(json.dumps({'cases':sum(r['cases'] for r in rows),'nodes':sum(r['nodes'] for r in rows),'local_rows':sum(r['support_rows'] for r in rows),'errors':0,'negative':negative_result['status']}))
