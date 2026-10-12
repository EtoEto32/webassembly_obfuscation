import pathlib,json,random,hashlib
R=pathlib.Path(__file__).resolve().parent
MOD=1<<32; MASK=MOD-1

def source(x,y,n):
    history=[[x,y]]
    for _ in range(n):
        xx=(x*x+3*y)%MOD
        bits=f'{y:032b}'
        yy=int(bits[5:]+bits[:5],2)^xx
        x,y=xx,yy
        history.append([x,y])
    return history

def transformed(x,y,n):
    if not n: return [],[x,y]
    p=(x*x+3*y)&MASK
    cuts=[[p,y]]
    for _ in range(n-1):
        y=(((y<<5)|(y>>27))&MASK)^p
        p=(p*p+3*y)&MASK
        cuts.append([p,y])
    out=[p,(((y<<5)|(y>>27))&MASK)^p]
    return cuts,out

def recover(inputs,cuts,out):
    # No access to source() or its trace.
    x,y,n=inputs
    if n==0: return [[x,y]]
    return [[x,y]]+[[cuts[i-1][0],cuts[i][1]] for i in range(1,n)]+[out]

boundary=[0,1,2,15,(1<<31)-1,1<<31,MASK]
inputs=[[x,y,n] for x in boundary for y in boundary for n in [0,1,2,3,16,32]]
rng=random.Random(1729)
inputs += [[rng.getrandbits(32),rng.getrandbits(32),rng.randrange(33)] for _ in range(1024)]
rows=[]; errors=[]; recovered=0
for idx,inp in enumerate(inputs):
    expected=source(*inp)
    cuts,out=transformed(*inp)
    rebuilt=recover(inp,cuts,out)
    if expected[-1]!=out or expected!=rebuilt: errors.append(idx)
    recovered+=len(expected)
    rows.append({'input':inp,'cuts':cuts,'output':out,'source_states':expected,'recovered_states':rebuilt})
payload=json.dumps(rows,separators=(',',':'))
(R/'observations.json').write_text(payload)
summary={'cases':len(inputs),'source_states_checked':recovered,'failed_cases':errors,'observations_sha256':hashlib.sha256(payload.encode()).hexdigest(),'seed':1729,'status':'reject_simple_temporal_cut' if not errors else 'investigate_mismatch'}
(R/'results.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary))
