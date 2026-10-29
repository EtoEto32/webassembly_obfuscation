import hashlib,itertools,json,math,platform,random,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'artifacts'
if OUT.exists():raise SystemExit('Refuse overwrite artifacts')
OUT.mkdir();protocol=json.loads((ROOT/'protocol.json').read_text())
def write(name,value):(OUT/name).write_text(json.dumps(value,indent=2))
def primes(count):
    result=[];n=2
    while len(result)<count:
        if all(n%p for p in result if p*p<=n):result.append(n)
        n+=1
    return result
def encode(x,atoms):return math.prod(a for i,a in enumerate(atoms) if (x>>i)&1)
def decode(v,atoms,p):
    q=math.gcd(v,p);x=0
    for i,a in enumerate(atoms):
        g=math.gcd(q,a)
        if g==a:x|=1<<i;q//=a
        elif g!=1:raise ValueError('Partial atom')
    assert q==1
    return x
rows=[]
for width in protocol['widths']:
    rng=random.Random(protocol['seed']+width)
    ps=primes(2*width);rng.shuffle(ps)
    atoms=[ps[2*i]*ps[2*i+1] for i in range(width)];p=math.prod(atoms)
    assert all(math.gcd(a,b)==1 for i,a in enumerate(atoms) for b in atoms[i+1:])
    def mask(v):return v*(p*rng.randrange(1,1<<32)+1)
    obs=[]
    for j in range((width-1).bit_length()):
        x=sum(1<<i for i in range(width) if (i>>j)&1)
        obs.append({'input':x,'value':str(mask(encode(x,atoms)))})
    stem=f'w{width}';write(stem+'.public.json',{'width':width,'universe':str(p),'observations':obs})
    write(stem+'.private.json',{'atoms':list(map(str,atoms)),'seed':protocol['seed']+width})
    subprocess.run([sys.executable,str(ROOT/'recover.py'),str(OUT/(stem+'.public.json')),str(OUT/(stem+'.recovered.json'))],check=True,timeout=20)
    attack=json.loads((OUT/(stem+'.recovered.json')).read_text());learned=list(map(int,attack['atoms']))
    assert learned==atoms
    if width==4:cases=list(itertools.product(range(16),repeat=2))
    else:
        boundaries=[0,1,2,31,0x7fffffff,0x80000000,0xfffffffe,0xffffffff]
        cases=list(itertools.product(boundaries,repeat=2))+[(rng.getrandbits(32),rng.getrandbits(32)) for _ in range(256)]
    outcomes=[]
    for x,y in cases:
        a,b=mask(encode(x,atoms)),mask(encode(y,atoms))
        assert decode(a,learned,p)==x and decode(b,learned,p)==y
        u,v=math.gcd(a,p),math.gcd(b,p);g=math.gcd(u,v)
        encoded={'and':g,'or':u*v//g,'xor':u*v//(g*g),'not':p//u}
        expected={'and':x&y,'or':x|y,'xor':x^y,'not':x^((1<<width)-1)}
        masked={name:mask(value) for name,value in encoded.items()}
        actual={name:decode(value,learned,p) for name,value in masked.items()}
        assert actual==expected
        # Verify representation itself, not only a recovered scalar.
        assert all(encoded[name]==encode(expected[name],atoms) for name in encoded)
        outcomes.append({'x':x,'y':y,'inputs':list(map(str,[a,b])),'encoded_outputs':{k:str(v) for k,v in masked.items()},'expected':expected,'recovered':actual})
    write(stem+'.checks.json',outcomes)
    # Partial composite atom is outside the representation invariant.
    try:decode(ps[0],learned,p)
    except ValueError:invalid_detected=True
    else:raise AssertionError('Invalid carrier accepted')
    rows.append({'width':width,'cases':len(cases),'output_checks':4*len(cases),'input_recovery_checks':2*len(cases),'queries':attack['queries'],'splitting_gcds':attack['splitting_gcds'],'atoms_recovered':len(learned),'universe_bits':p.bit_length(),'partial_atom_rejected':invalid_detected,'errors':0})
    write(stem+'.sample.json',outcomes[1])
negative={'atoms':[6,10],'before':'1 AND 2 = 0','encoded_operands':[6,10],'after_gcd':math.gcd(6,10),'required_encoded_zero':1}
assert negative['after_gcd']!=negative['required_encoded_zero']
write('noncoprime-counterexample.json',negative)
result={'python':platform.python_version(),'rows':rows,'negative':negative,'scripts':{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in ['protocol.json','check.py','recover.py']},'decision':'reject elementary divisor carrier and coprime nuisance masking'}
write('results.json',result)
print(json.dumps({'cases':sum(r['cases'] for r in rows),'outputs':sum(r['output_checks'] for r in rows),'recovered_atoms':sum(r['atoms_recovered'] for r in rows),'rows':rows}))
