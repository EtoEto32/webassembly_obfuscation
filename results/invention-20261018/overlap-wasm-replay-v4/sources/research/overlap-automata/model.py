"""Source-certified monotone NFA merging; conjectural obfuscation candidate."""
from collections import deque
from dataclasses import dataclass
import random
import time


def bits(x):
    while x:
        b=x & -x;yield b.bit_length()-1;x^=b


def union(xs):
    v=0
    for x in xs:v|=x
    return v


@dataclass
class DFA:
    trans: list
    final: int
    start: int=0
    @property
    def n(self):return len(self.trans)
    def accepts(self,word):
        q=self.start
        for a in word:q=self.trans[q][a]
        return (self.final>>q)&1


@dataclass
class NFA:
    trans: list
    initial: int
    final: int
    @property
    def n(self):return len(self.trans)
    def step(self,s,a):return union(self.trans[q][a] for q in bits(s))
    def accepts(self,word):
        s=self.initial
        for a in word:s=self.step(s,a)
        return int(bool(s & self.final))


def universal(k):
    if k<3 or k%2!=1:raise ValueError('Odd k >= 3 required')
    rows=[[1,1]];final=0;cache={}
    def suffix(pattern):
        nonlocal final
        if pattern in cache:return cache[pattern]
        i=len(rows);cache[pattern]=i;rows.append([0,0])
        if not pattern:final|=1<<i
        else:
            child=suffix(pattern[1:])
            for a in range(2):
                if pattern[0] in (-1,a):rows[i][a]|=1<<child
        return i
    for i in range(k):
        for value in range(2):
            pattern=[-1]*k;pattern[i]=pattern[(i+1)%k]=value
            tail=suffix(tuple(pattern[1:]))
            for a in range(2):
                if pattern[0] in (-1,a):rows[0][a]|=1<<tail
    initial=1
    # Separate all-accepting chain handles words shorter than k.
    prev=None
    for _ in range(k):
        i=len(rows);rows.append([0 if prev is None else 1<<prev]*2);final|=1<<i;prev=i
    initial|=1<<prev
    return NFA(rows,initial,final)


def lift(d,u):
    trans=[]
    for q in range(d.n):
        for r in range(u.n):
            trans.append([union(1<<(d.trans[q][a]*u.n+s) for s in bits(u.trans[r][a])) for a in range(2)])
    return NFA(trans,u.initial<<(d.start*u.n),union(u.final<<(q*u.n) for q in bits(d.final)))


def remap(n,classes):
    nr=max(classes)+1;rows=[[0,0] for _ in range(nr)]
    for i,row in enumerate(n.trans):
        for a in range(2):rows[classes[i]][a]|=union(1<<classes[j] for j in bits(row[a]))
    return NFA(rows,union(1<<classes[i] for i in bits(n.initial)),union(1<<classes[i] for i in bits(n.final)))


def merge(n,a,b):
    if a>b:a,b=b,a
    return remap(n,[a if i==b else i if i<b else i-1 for i in range(n.n)])


def trim(n):
    reach=n.initial;prev=-1
    while reach!=prev:prev=reach;reach|=n.step(reach,0)|n.step(reach,1)
    rev=reverse(n);live=n.final;prev=-1
    while live!=prev:prev=live;live|=rev.step(live,0)|rev.step(live,1)
    keep=list(bits(reach&live))
    if not keep:return NFA([[0,0]],1,0)
    ids={old:new for new,old in enumerate(keep)}
    def mapped(mask):return union(1<<ids[i] for i in bits(mask) if i in ids)
    return NFA([[mapped(x) for x in n.trans[i]] for i in keep],mapped(n.initial),mapped(n.final))


def certificate(d,n):
    """Check L(N) subset L(D), with a concrete counterexample on failure.
    State merging separately guarantees the reverse inclusion from the prior N.
    """
    initial=[(d.start,r) for r in bits(n.initial)];prev={x:None for x in initial};todo=deque(initial)
    contexts=[0]*n.n
    while todo:
        q,r=todo.popleft();contexts[r]|=1<<q
        if (n.final>>r)&1 and not (d.final>>q)&1:
            word=[];v=(q,r)
            while prev[v] is not None:v,a=prev[v];word.append(a)
            return dict(valid=False,word=word[::-1],pairs=len(prev))
        for a in range(2):
            q1=d.trans[q][a]
            for r1 in bits(n.trans[r][a]):
                v=(q1,r1)
                if v not in prev:prev[v]=((q,r),a);todo.append(v)
    return dict(valid=True,contexts=contexts,pairs=len(prev),
                overlap=sum(max(0,len(list(bits(x)))-1) for x in contexts),
                multi=sum(len(list(bits(x)))>1 for x in contexts))


def choose_merges(d,n,rounds,seed,mode='overlap',pairs_per_round=128):
    rng=random.Random(seed);history=[];checks=0;t=time.perf_counter();n=trim(n)
    for _ in range(rounds):
        pairs=[(i,j) for i in range(n.n) for j in range(i+1,n.n)];rng.shuffle(pairs)
        choices=[]
        for i,j in pairs[:pairs_per_round]:
            candidate=trim(merge(n,i,j));c=certificate(d,candidate);checks+=1
            if c['valid']:
                choices.append((c['overlap'],c['multi'],candidate,c,(i,j)))
                if mode=='random':break
        if not choices:break
        best=max(choices,key=lambda x:x[:2]) if mode=='overlap' else choices[0]
        _,_,n,c,pair=best;history.append(dict(pair=pair,states=n.n,overlap=c['overlap'],multi=c['multi'],certificate_pairs=c['pairs']))
    return n,dict(mode=mode,rounds=len(history),checks=checks,history=history,ms=(time.perf_counter()-t)*1000)


def determinize(n,limit=100000):
    t=time.perf_counter();states=[n.initial];ids={n.initial:0};rows=[];final=0
    for i,s in enumerate(states):
        if s & n.final:final|=1<<i
        row=[]
        for a in range(2):
            z=n.step(s,a)
            if z not in ids:
                if len(states)>=limit:return None,dict(status='state_limit',states=len(states),ms=(time.perf_counter()-t)*1000)
                ids[z]=len(states);states.append(z)
            row.append(ids[z])
        rows.append(row)
    return DFA(rows,final),dict(status='success',states=len(states),ms=(time.perf_counter()-t)*1000)


def minimize(d):
    group=[(d.final>>i)&1 for i in range(d.n)]
    while True:
        keys=[((d.final>>i)&1,*(group[j] for j in d.trans[i])) for i in range(d.n)]
        ids={};new=[ids.setdefault(x,len(ids)) for x in keys]
        if new==group:break
        group=new
    representatives={c:i for i,c in enumerate(group)}
    result=DFA([[group[j] for j in d.trans[representatives[c]]] for c in range(len(representatives))],
               union(1<<group[i] for i in bits(d.final)),group[d.start])
    return result


def bisimulation(n):
    group=[(n.final>>i)&1 for i in range(n.n)]
    while True:
        keys=[((n.final>>i)&1,*(tuple(sorted({group[j] for j in bits(n.trans[i][a])})) for a in range(2))) for i in range(n.n)]
        ids={};new=[ids.setdefault(x,len(ids)) for x in keys]
        if new==group:return remap(n,group)
        group=new


def simulation(n):
    """Classic direct forward simulation quotient + dominated-edge pruning.

    This is a deliberately small baseline, not Clemente/Mayr's Heavy-k tool.
    """
    n=trim(n)
    while True:
        relation=[set(q for q in range(n.n) if not ((n.final>>p)&1) or (n.final>>q)&1) for p in range(n.n)]
        changed=True
        while changed:
            changed=False
            for p in range(n.n):
                for q in list(relation[p]):
                    if any(not any(s in relation[r] for s in bits(n.trans[q][a]))
                           for a in range(2) for r in bits(n.trans[p][a])):
                        relation[p].remove(q);changed=True
        classes=[];representatives=[]
        for p in range(n.n):
            eq=next((i for i,q in enumerate(representatives) if q in relation[p] and p in relation[q]),None)
            if eq is None:eq=len(representatives);representatives.append(p)
            classes.append(eq)
        # Keep a maximal simulation successor, breaking mutual ties by index.
        rows=[]
        for row in n.trans:
            rows.append([union(1<<p for p in bits(mask) if not any(q!=p and q in relation[p]
                and (p not in relation[q] or q<p) for q in bits(mask))) for mask in row])
        reduced=trim(remap(NFA(rows,n.initial,n.final),classes))
        if reduced==n:return n
        n=reduced


def reverse(n):
    rows=[[0,0] for _ in range(n.n)]
    for i in range(n.n):
        for a in range(2):
            for j in bits(n.trans[i][a]):rows[j][a]|=1<<i
    return NFA(rows,n.final,n.initial)


def from_dfa(d):return NFA([[1<<j for j in row] for row in d.trans],1<<d.start,d.final)


def equivalent(a,b):
    todo=deque([(a.start,b.start)]);seen=set(todo)
    while todo:
        x,y=todo.popleft()
        if ((a.final>>x)^(b.final>>y))&1:return False,len(seen)
        for z in range(2):
            v=a.trans[x][z],b.trans[y][z]
            if v not in seen:seen.add(v);todo.append(v)
    return True,len(seen)


def pattern(word,contains=False):
    prefixes=[tuple(word[:i]) for i in range(len(word)+1)];rows=[]
    for s in prefixes:
        row=[]
        for a in range(2):
            if contains and len(s)==len(word):row.append(len(word));continue
            v=s+(a,);row.append(max(i for i,p in enumerate(prefixes) if i==0 or v[-i:]==p))
        rows.append(row)
    return DFA(rows,1<<len(word))
