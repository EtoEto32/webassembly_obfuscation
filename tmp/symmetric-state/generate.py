import pathlib,itertools,json,subprocess,hashlib
ROOT=pathlib.Path(__file__).resolve().parent
TOOLS=pathlib.Path('C:/Users/ettotto/Documents/webassembly_obfuscation/.tools')

def add(a,b):
    out=a.copy()
    for k,v in b.items():
        out[k]=out.get(k,0)+v
        if not out[k]: del out[k]
    return out
def scale(a,c): return {k:v*c for k,v in a.items() if v*c}
def mul(a,b):
    out={}
    for k,v in a.items():
        for l,w in b.items():
            key=tuple(x+y for x,y in zip(k,l)); out[key]=out.get(key,0)+v*w
    return {k:v for k,v in out.items() if v}
def one(d): return {(0,)*d:1}
def var(d,i): return {tuple(int(i==j) for j in range(d)):1}
def power(p,n):
    out=one(len(next(iter(p))))
    for _ in range(n): out=mul(out,p)
    return out
def elementary(xs):
    out=[]; d=len(next(iter(xs[0])))
    for k in range(1,len(xs)+1):
        p={}
        for group in itertools.combinations(xs,k):
            term=one(d)
            for x in group: term=mul(term,x)
            p=add(p,term)
        out.append(p)
    return out
def symmetric_reduce(p,n,es):
    work=p.copy(); reduced={}; d=n+2; steps=0
    while work:
        lead=max(work); coefficient=work[lead]
        if any(lead[i]<lead[i+1] for i in range(n-1)):
            raise ValueError('Not symmetric in source lanes')
        powers=tuple(lead[i]-(lead[i+1] if i+1<n else 0) for i in range(n))+lead[n:]
        term=one(d)
        for e,k in zip(es,powers[:n]): term=mul(term,power(e,k))
        for i in range(n,d): term=mul(term,power(var(d,i),powers[i]))
        work=add(work,scale(term,-coefficient))
        reduced=add(reduced,{powers:coefficient}); steps+=1
        if steps>10000: raise RuntimeError('reduction limit')
    return reduced
def substitute(poly,variables):
    out={}; d=len(next(iter(variables[0])))
    for powers,c in poly.items():
        term=one(d)
        for v,k in zip(variables,powers): term=mul(term,power(v,k))
        out=add(out,scale(term,c))
    return out
def wat(poly,names):
    terms=[]
    for powers,c in sorted(poly.items()):
        factors=[f'(local.get ${name})' for name,k in zip(names,powers) for _ in range(k)]
        c=((c+(1<<31))%(1<<32))-(1<<31)
        if c!=1 or not factors: factors.insert(0,f'(i32.const {c})')
        term=factors[0]
        for f in factors[1:]: term=f'(i32.mul {term} {f})'
        terms.append(term)
    if not terms: return '(i32.const 0)'
    result=terms[0]
    for t in terms[1:]: result=f'(i32.add {result} {t})'
    return result

manifest=[]
for n in [2,3]:
    d=n+2; xs=[var(d,i) for i in range(n)]; c=var(d,n); u=var(d,n+1)
    es=elementary(xs)
    fs=[add(add(mul(x,x),mul(c,x)),u) for x in xs]
    target=elementary(fs)
    reduced=[symmetric_reduce(p,n,es) for p in target]
    for p,q in zip(target,reduced):
        assert substitute(q,es+[c,u])==p,'integer identity failed'
    (ROOT/f'identities-{n}.json').write_text(json.dumps({'arity':n,'variable_order':[f'e{i}' for i in range(n)]+['c','u'],'reduced':[ [{'powers':list(k),'coefficient':v} for k,v in sorted(p.items())] for p in reduced],'expanded_identity_verified':True},indent=2))
    for kind in ['normal','quotient']:
        xnames=[f'x{i}' for i in range(n)]; enames=[f'e{i}' for i in range(n)]
        names=(xnames if kind=='normal' else enames)+['c','u']
        body=['(module','(func (export "run") '+''.join(f'(param ${x} i32)' for x in xnames)+'(param $u i32)(param $n i32)(result '+' '.join(['i32']*n)+')', '(local $c i32)'+''.join(f'(local $t{i} i32)' for i in range(n))]
        if kind=='quotient':
            body.append(''.join(f'(local ${e} i32)' for e in enames))
            body += [f'(local.set ${e} {wat(p,xnames+["c","u"])})' for e,p in zip(enames,es)]
        body += ['(local.set $n (i32.and (local.get $n)(i32.const 31)))','(block $exit (loop $loop','(br_if $exit (i32.eqz (local.get $n)))']
        total=wat(es[0],names) if kind=='normal' else '(local.get $e0)'
        body.append(f'(local.set $c (select (i32.const 3)(i32.const 5)(i32.and {total}(i32.const 1))))')
        polynomials=fs if kind=='normal' else reduced
        body += [f'(local.set $t{i} {wat(p,names)})' for i,p in enumerate(polynomials)]
        body += [f'(local.set ${name} (local.get $t{i}))' for i,name in enumerate(names[:n])]
        body += ['(local.set $n (i32.sub (local.get $n)(i32.const 1)))','(br $loop)))']
        body += [wat(p,names) for p in es] if kind=='normal' else [f'(local.get ${e})' for e in enames]
        body.append('))'); stem=f'{n}-{kind}'
        watpath=ROOT/(stem+'.wat'); watpath.write_text('\n'.join(body))
        raw=ROOT/(stem+'.wasm'); opt=ROOT/(stem+'-O2.wasm')
        subprocess.run([str(TOOLS/'wabt-1.0.42/bin/wat2wasm.exe'),str(watpath),'-o',str(raw)],check=True,capture_output=True)
        subprocess.run([str(TOOLS/'binaryen-version_133/bin/wasm-opt.exe'),str(raw),'-O2','--enable-multivalue','-o',str(opt)],check=True,capture_output=True)
        for path in [raw,opt]: manifest.append({'arity':n,'kind':kind,'file':path.name,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
(ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest))
