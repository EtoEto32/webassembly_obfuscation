import hashlib
import json
import platform
import random
from pathlib import Path

ROOT=Path(__file__).resolve().parent
MASK=(1<<32)-1


def rotr(x,n):
    return ((x>>n)|(x<<(32-n)))&MASK


def q(a,b,c):
    return ((rotr(a,2)^rotr(a,13)^rotr(a,22))+((a&b)^(a&c)^(b&c)))&MASK


def decode(p):
    return p[:4]+[(p[j]+p[j+4]-q(p[j+1],p[j+2],p[j+3]))&MASK for j in range(4)]


def encode(s):
    p=list(s[:4])
    for j in range(4):
        p.append((s[4+j]-p[j]+q(p[j+1],p[j+2],p[j+3]))&MASK)
    return p


def history_step(p,u):
    # Explicit recurrence, not a call to the original round function.
    e=[(p[j]+p[j+4]-q(p[j+1],p[j+2],p[j+3]))&MASK for j in range(4)]
    sigma=rotr(e[0],6)^rotr(e[0],11)^rotr(e[0],25)
    choice=(e[0]&e[1])^((~e[0])&e[2])
    head=(e[3]+sigma+choice+u+q(p[0],p[1],p[2]))&MASK
    return [head]+p[:7]


def reference(s,u):
    a,b,c,d,e,f,g,h=s
    # Baseline round formulas, using the alternative equivalent Ch/Maj spelling.
    s1=rotr(e,6)^rotr(e,11)^rotr(e,25)
    choice=g^(e&(f^g))
    s0=rotr(a,2)^rotr(a,13)^rotr(a,22)
    maj=(a&b)|(c&(a|b))
    t1=(h+s1+choice+u)&MASK
    t2=(s0+maj)&MASK
    return [(t1+t2)&MASK,a,b,c,(d+t1)&MASK,e,f,g]


def main():
    output=ROOT/'results.json'
    if output.exists(): raise FileExistsError(output)
    rng=random.Random(619731)
    states=[[0]*8,[MASK]*8]
    for j in range(8):
        for value in [1,0x80000000,MASK]:
            s=[0]*8;s[j]=value;states.append(s)
    states += [[rng.getrandbits(32) for _ in range(8)] for _ in range(1024)]
    records=[];checks=0;control=None;stream=hashlib.sha256()
    for i,initial in enumerate(states):
        s=initial[:];p=encode(s)
        assert decode(p)==s
        inputs=[];example=[]
        for step in range(64):
            u=rng.getrandbits(32);inputs.append(u)
            s=reference(s,u);p=history_step(p,u)
            recovered=decode(p)
            assert s==recovered
            assert encode(recovered)==p
            checks+=1
            if control is None:
                wrong=p[:4]+[(p[j]+p[j+4])&MASK for j in range(4)]
                if wrong!=s: control={'case':i,'step':step,'history':p,'expected':s,'wrong':wrong}
            row={'step':step,'u':u,'history':p,'reference':s,'recovered':recovered}
            stream.update(json.dumps(row,sort_keys=True,separators=(',',':')).encode()+b'\n')
            if i==0: example.append(row)
        records.append({'initial':initial,'inputs':inputs,'final_history':p,'final_reference':s})
        if i==0:
            (ROOT/'example-trace.json').write_text(json.dumps(example,indent=2)+'\n')
    assert control is not None
    (ROOT/'inputs-and-finals.json').write_text(json.dumps(records,separators=(',',':'))+'\n')
    report={'python':platform.python_version(),'states':len(states),'rounds':checks,
            'mismatches':0,'rule_aware_recoveries':checks,'negative_control':control,
            'all_trace_rows_sha256':stream.hexdigest(),
            'hashes':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in
                      ['protocol.json','check.py','example-trace.json','inputs-and-finals.json']}}
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__': main()
