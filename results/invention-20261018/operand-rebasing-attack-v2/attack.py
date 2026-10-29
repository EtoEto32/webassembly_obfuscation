"""Public-table inverse compilation; no original expression or kernel labels used.

Grammar: four leaves, each input exactly once, five binary operators, all trees.
Failure means grammar exhaustion, NOT resistance. Confirmation uses product automata.
"""
import importlib.util, itertools, json, random, re, struct, sys, time
from pathlib import Path
spec=importlib.util.spec_from_file_location('compiler',Path(__file__).with_name('compile.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
OPS=('add','sub','xor','and','or')
def expressions(leaves):
    if len(leaves)==1:
        yield ['local.get',str(leaves[0])];return
    for k in range(1,len(leaves)):
        for a in expressions(leaves[:k]):
            for b in expressions(leaves[k:]):
                for op in OPS:yield ['i32.'+op,a,b]
def evaluate(n,x):
    if n[0]=='local.get':return x[int(n[1])]
    a,b=evaluate(n[1],x),evaluate(n[2],x)
    return {'i32.add':a+b,'i32.sub':a-b,'i32.xor':a^b,'i32.and':a&b,'i32.or':a|b}[n[0]]&0xffffffff
def nodes(n):
    if isinstance(n,list):
        yield n
        for x in n:yield from nodes(x)
def extract(path):
    tree=c.read(path);segment=c.items(tree,'data')[0][-1][1:-1]
    # WABT emits printable ASCII directly, other bytes as two hex digits.
    blob=bytearray();i=0
    while i<len(segment):
        if segment[i]=='\\':
            if re.fullmatch('[0-9a-fA-F]{2}',segment[i+1:i+3]):blob.append(int(segment[i+1:i+3],16));i+=3
            else:blob.append(ord(segment[i+1]));i+=2
        else:blob.append(ord(segment[i]));i+=1
    table=list(struct.unpack('<'+'I'*(len(blob)//4),blob))
    starts=[n for n in nodes(tree) if n[0]=='local.set' and n[1]=='5' and n[2][0]=='i32.const']
    assert len(starts)==1
    return table,int(starts[0][2][1])
def oracle(table,start,x):
    state=start;out=0
    for bit in range(32):
        symbol=sum(((v>>bit)&1)<<j for j,v in enumerate(x))
        entry=table[16*state+symbol];out|=(entry&1)<<bit;state=entry>>1
    return (x[0]+out)&0xffffffff
def equivalent(a,sa,b,sb):
    seen={(sa,sb)};front=[(sa,sb)];edges=0
    while front:
        x,y=front.pop()
        for symbol in range(16):
            u,v=a[16*x+symbol],b[16*y+symbol];edges+=1
            if (u&1)!=(v&1):return False,len(seen),edges
            pair=(u>>1,v>>1)
            if pair not in seen:seen.add(pair);front.append(pair)
    return True,len(seen),edges
def main(src,out):
    out.mkdir();rng=random.Random(20261018)
    inputs=[tuple(rng.getrandbits(32) for _ in range(4)) for _ in range(16)]
    # The only input is transformed binary bytes. Names are opaque identifiers.
    files=sorted(src.glob('*-fused.wasm'));targets=[]
    for p in files:
        t,s=extract(p);targets.append((p,t,s,tuple(oracle(t,s,x) for x in inputs)))
    matches={p.name:[] for p,*_ in targets};count=0;t0=time.perf_counter()
    for perm in itertools.permutations(range(4)):
        for expr in expressions(perm):
            count+=1;first=evaluate(expr,inputs[0])
            for p,table,start,signature in targets:
                if first!=signature[0] or any(evaluate(expr,x)!=v for x,v in zip(inputs[1:],signature[1:])):continue
                candidate,initial,_=c.machine(expr)
                ok,states,edges=equivalent(table,start,candidate,initial)
                if ok:matches[p.name].append({'expression':expr,'productStates':states,'edges':edges,'candidate':count,'elapsedSeconds':time.perf_counter()-t0})
    controls=[]
    for p,table,start,_ in targets:
        changed=table.copy();changed[start*16]^=1
        controls.append({'file':p.name,'identityAccepted':equivalent(table,start,table,start)[0],
                         'changedInitialOutputRejected':not equivalent(table,start,changed,start)[0]})
    assert all(x['identityAccepted'] and x['changedInitialOutputRejected'] for x in controls)
    result={'grammar':'Each of four inputs occurs once; all binary trees; add/sub/xor/and/or; exactly three operators.',
      'candidates':count,'seconds':time.perf_counter()-t0,'inputs':inputs,
      'targets':[{'file':p.name,'sha256':c.sha(p),'status':'recovered' if matches[p.name] else 'grammar_exhausted','matches':matches[p.name], 'oracleOutputs':list(sig)} for p,t,s,sig in targets],
      'controls':controls,
      'confirmation':'Exhaustive reachable product-automaton equivalence for all bit strings, not only sampled words.',
      'limitation':'Raw emitter profile only. Grammar exhaustion is not timeout, unsupported binary, or security.'}
    (out/'attack.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    (out/'attack.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps({k:v for k,v in result.items() if k not in ('targets','inputs')}));print([(r['file'],r['status'],len(r['matches'])) for r in result['targets']])
if __name__=='__main__':main(*map(Path,sys.argv[1:3]))
