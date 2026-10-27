"""Independent SymPy coefficient checks and optional SMT; never call generator core.

Recovery witnesses come from measured samples, not from source-expression search.
Metadata binds symbolic observations to post-Binaryen binaries and their probes.
"""
import argparse, hashlib, json, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'.tools/nonbijective-residual-cas'))
sys.path.insert(0,str(ROOT/'.tools/encoding-synthesis-python'))
import sympy as sp
import z3
V=sp.symbols('v0 v1 v2')
XOR=sp.Function('xor');AND=sp.Function('and');OR=sp.Function('or')
MASK=(1<<32)-1

def lift(t):
    if isinstance(t,int): return sp.Integer(t)
    if isinstance(t,str): return V[int(t[1:])]
    op=t[0];a,b=lift(t[1]),lift(t[2])
    if op=='add':
        # Proven word identity; commutative operands canonicalized by SymPy.
        for u,v in ((a,b),(b,a)):
            if u.func==XOR and sp.expand(v-2*AND(*u.args))==0: return sum(u.args)
        return a+b
    if op=='sub': return a-b
    if op=='mul': return a*b
    if op=='shl' and b.is_Integer: return a*(1<<(int(b)&31))
    if op in ('xor','and','or'):
        if a==b: return sp.Integer(0) if op=='xor' else a
        return {'xor':XOR,'and':AND,'or':OR}[op](*sorted((a,b),key=sp.default_sort_key))
    raise ValueError('unsupported '+op)

def coeff(expr):
    # Independent implementation, exponent triples rather than generator tuples.
    p=sp.Poly(sp.expand(expr),*V)
    return [(list(m),int(c)&MASK) for m,c in p.terms() if int(c)&MASK]

def bv(t):
    if isinstance(t,int): return z3.BitVecVal(t,32)
    if isinstance(t,str): return z3.BitVec(t,32)
    a,b=bv(t[1]),bv(t[2]);op=t[0]
    return {'add':lambda:a+b,'sub':lambda:a-b,'mul':lambda:a*b,
            'xor':lambda:a^b,'and':lambda:a&b,'or':lambda:a|b,
            'shl':lambda:a<<(b&31)}[op]()

def check(a,b):
    t=time.perf_counter()
    try:
        equal=coeff(lift(a))==coeff(lift(b))
        if equal:return {'status':'proved','method':'independent_modular_coefficients','seconds':time.perf_counter()-t}
    except (ValueError,sp.PolynomialError,TypeError): pass
    s=z3.Solver();s.set(timeout=3000);s.add(bv(a)!=bv(b));r=s.check()
    return {'status':{'unsat':'proved','sat':'counterexample','unknown':'unknown'}[str(r)],
            'method':'z3_bitvectors','seconds':time.perf_counter()-t,
            'reason':s.reason_unknown() if r==z3.unknown else (str(s.model()) if r==z3.sat else None)}

def resolve(t,meta):
    if t[0]=='input':return 'v'+str(t[1])
    if t[0]=='const':return t[1]
    if t[0]=='event':return next(e['expression'] for e in meta['events'] if e['id']==t[1])
    if t[0]=='output':return meta['output_expression']
    return [t[0],resolve(t[1],meta),resolve(t[2],meta)]

def run(d):
    out=d/'symbolic.json'
    if out.exists():raise ValueError('Refuse overwrite')
    read=lambda p:json.loads((d/p).read_text(encoding='utf-8'))
    plan,manifest=read('plan.json'),read('manifest.json');attacks={x['id']:x for x in read('attacks.json')['results']}
    sha=lambda p:hashlib.sha256((d/p).read_bytes()).hexdigest()
    assert sha('plan.json')==manifest['planSHA256']
    rows=[]
    for a in manifest['artifacts']:
        meta=read(a['probe']+'.json');assert sha(a['file'])==a['sha256']==meta['inputSHA256']
        assert sha(a['probe'])==meta['probeSHA256']
        row={'id':a['id'],'output':check(meta['output_expression'],plan['programs'][a['program']])}
        attack=attacks[a['id']]
        row['recovery']=check(resolve(attack['term'],meta),plan['targets'][a['program']]) if attack['status']=='sample_validated' else {'status':attack['status']}
        start=time.perf_counter()
        try:
            c=coeff(lift(meta['output_expression']))
            # This normalizer reads the artifact and does not inspect its target.
            root=sum(sp.Integer(n if n<2**31 else n-2**32)*sp.prod(v**e for v,e in zip(V,m)) for m,n in c)
            factored=sp.factor(root)
            row['canonical']={'status':'normalized','coefficients':c,'factored_expression':str(factored),
                'factorization_verified':coeff(factored)==c,'seconds':time.perf_counter()-start}
        except (ValueError,sp.PolynomialError,TypeError) as e:
            row['canonical']={'status':'unsupported','reason':str(e),'seconds':time.perf_counter()-start}
        rows.append(row)
    # Negative controls catch constant-true equivalence checkers and trace mixups.
    controls=[check(['add','v0',1],'v0'),check(['mul','v0',2],'v0'),check(['xor','v0','v1'],['add','v0','v1'])]
    assert all(x['status']=='counterexample' for x in controls)
    result={'sympy':sp.__version__,'z3':z3.get_version_string(),'rows':rows,'negative_controls':controls,
       'limitations':['Polynomial equality is a sufficient condition, not complete equivalence over a finite ring.',
       'A proved local expression does not prove the whole Wasm module, interpreter, or instrumentation correct.',
       'Equal canonical output representation is not recovery of exact source control flow or data structures.']}
    out.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({'output_proved':sum(r['output']['status']=='proved' for r in rows),
      'recovery_proved':sum(r['recovery']['status']=='proved' for r in rows),'normalized':sum(r['canonical']['status']=='normalized' for r in rows)}))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('directory',type=Path);run(ap.parse_args().directory)
