"""Coefficient projection, followed by an exact equation/certificate check."""
import argparse,json,time
import prototype as p

def canon(e):
    if len(e)==2:return e
    op=e[0];a,b=canon(e[1]),canon(e[2])
    if op=='rotr' and b[0]=='c':op='rotl';b=p.C((-b[1])%32)
    if op in ('or','xor','and') and repr(a)>repr(b):a,b=b,a
    return (op,a,b)
def add(a,b,k=1):
    r=dict(a)
    for t,v in b.items():
        q=(r.get(t,0)+k*v)&p.MASK
        if q:r[t]=q
        else:r.pop(t,None)
    return r
def mul(a,b):
    r={}
    for u,x in a.items():
        for v,y in b.items():
            k=tuple(sorted(u+v,key=repr));r[k]=(r.get(k,0)+x*y)&p.MASK
    return {k:v for k,v in r.items() if v}
def const(v):return {():v&p.MASK} if v&p.MASK else {}
def poly(e):
    e=canon(e);op=e[0]
    if op=='c':return const(e[1])
    if op in ('add','sub'):return add(poly(e[1]),poly(e[2]),-1 if op=='sub' else 1)
    if op=='mul':return mul(poly(e[1]),poly(e[2]))
    if op=='shl' and e[2][0]=='c':return mul(poly(e[1]),const(1<<(e[2][1]%32)))
    return {(e,):1}
def vars_(e):
    if e[0]=='v':return {e[1]}
    if len(e)==2:return set()
    return vars_(e[1])|vars_(e[2])
def pvars(a):return set().union(*(vars_(e) for t in a for e in t)) if a else set()
def unit(e,i):
    if e[0]!='or' or p.C(1) not in e[1:]:return False
    base=e[2] if e[1]==p.C(1) else e[1]
    if base[0]=='rotl':base=base[1]
    return base[0]=='xor' and p.V(i) in base[1:] and any(x[0]=='c' for x in base[1:])
def coefficient(a,u):
    r={}
    for term,c in a.items():
        count=term.count(u)
        if count>1:raise ValueError('nonlinear diagonal unit')
        if count:
            t=list(term);t.remove(u);r=add(r,{tuple(t):c})
    return r
def congruent(e,states):
    if len(e)==2:return True
    if e[0] in ('rotl','rotr','shr_u','shr_s') and vars_(e[1])&states:return False
    return congruent(e[1],states) and congruent(e[2],states)
def pexpr(a):
    e=p.C(0)
    for term,c in sorted(a.items(),key=lambda x:repr(x[0])):
        q=p.C(c)
        for atom in term:q=p.O('mul',q,atom)
        e=p.O('add',e,q)
    return e
def extract(path):
    begin=time.perf_counter();np,result,eq,rounds=p.bitrecover.expressions(path)
    if np!=3:raise ValueError('three parameters required')
    eq={i:canon(e) for i,e in eq.items()};result=canon(result)
    # Only locals actually referenced by the state equations are recurrent state.
    counter={i for i,e in eq.items() if e==('sub',p.V(i),p.C(1))}
    state=set().union(*(vars_(e) for i,e in eq.items() if i not in counter))-counter
    if not state or not state<=set(eq) or not vars_(result)<=state:raise ValueError('unsupported recurrence state')
    equations={i:poly(eq[i]) for i in state};fs={};units={}
    for i,h in equations.items():
        atoms={a for term in h for a in term};us=[a for a in atoms if unit(a,i)]
        if len(us)==1:
            units[i]=us[0];fs[i]=add(coefficient(h,us[0]),poly(p.V(i)))
        elif not us:
            fs[i]=mul(add(h,poly(p.V(i)),2),const(pow(3,-1,1<<32)))
        else:raise ValueError('ambiguous diagonal')
    order=[];todo=set(state)
    while todo:
        ready=sorted(i for i in todo if not pvars(fs[i])&todo)
        if not ready:raise ValueError('recovered source has cycle')
        i=ready[0];order.append(i);todo.remove(i)
    if rounds is None or rounds<len(state)*32:raise ValueError('insufficient convergence bound')
    for f in fs.values():
        if not congruent(pexpr(f),state):raise ValueError('non-congruent source')
    # Check all terms, not just the useful diagonal coefficient. This reconstructs
    # the actual residual matrix and certifies its pointwise parity condition.
    position={v:i for i,v in enumerate(order)};coeffs=[]
    residual={i:add(fs[i],poly(p.V(i)),-1) for i in state}
    for i,h in equations.items():
        if i not in units:
            if h!=add(mul(fs[i],const(3)),poly(p.V(i)),-2):raise ValueError('constant equation mismatch')
            coeffs.append([i,i,'constant-3']);continue
        remaining=add(h,poly(p.V(i)),-1);rebuild={};diagonal=0
        atoms={a for term in remaining for a in term}
        candidates=[a for a in atoms if a[0] in ('xor','rotl','or') and vars_(a)]
        for a in candidates:
            co=coefficient(remaining,a)
            matches=[(j,k) for j,r in residual.items() for k in (1,2) if co==mul(r,const(k))]
            if len(matches)!=1:continue
            j,k=matches[0]
            if j==i:
                if k!=1 or a!=units[i]:raise ValueError('invalid diagonal parity')
                diagonal+=1
            elif position[j]>position[i] and k%2:raise ValueError('odd backward coefficient')
            rebuild=add(rebuild,mul({(a,):1},co));coeffs.append([i,j,k])
        if diagonal!=1 or rebuild!=remaining:raise ValueError('residual certificate incomplete')
    parsed=time.perf_counter()
    slots={i:3+k for k,i in enumerate(order)}
    wat=['(module (func (export "run") (param i32 i32 i32) (result i32)','(local '+' '.join(['i32']*len(state))+')']
    for i in order:wat.append(f'(local.set {slots[i]} {p.ast_wat(pexpr(fs[i]),slots)})')
    wat.extend([p.ast_wat(result,slots),'))'])
    return '\n'.join(wat),dict(states=len(state),rounds=rounds,coefficients=len(coeffs),diagonal_units=len(units),read_and_recover_ms=(parsed-begin)*1000,status='recovered',source_or_seed_supplied=False)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('input');ap.add_argument('output');a=ap.parse_args();wat,stats=extract(a.input);p.compile_wat(wat,a.output);print(json.dumps(stats))
