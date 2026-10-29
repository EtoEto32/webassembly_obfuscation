"""Known-profile attack. Reads only target Wasm and public interpreter specifications."""
import argparse, collections, hashlib, json, struct, tempfile, time
from pathlib import Path
import prototype as q
p=q.p

class Reader:
    def __init__(self,b):self.b=b;self.i=0
    def byte(self):v=self.b[self.i];self.i+=1;return v
    def leb(self,signed=False):
        v=0;s=0
        for _ in range(5):
            x=self.byte();v|=(x&127)<<s;s+=7
            if not x&128:return v-(1<<s) if signed and x&64 else v
        raise ValueError('oversized LEB')
    def take(self,n):
        if self.i+n>len(self.b):raise ValueError('truncated bytes')
        v=self.b[self.i:self.i+n];self.i+=n;return v

def sections(b):
    r=Reader(b)
    if r.take(8)!=b'\0asm\1\0\0\0':raise ValueError('Wasm header')
    out=[]
    while r.i<len(b):
        sid=r.byte();n=r.leb();out.append((sid,r.take(n)))
    return out

def fingerprint(b):
    return hashlib.sha256(b''.join(bytes([sid])+struct.pack('<I',len(v))+v for sid,v in sections(b) if sid not in (0,11))).hexdigest()

def profiles():
    # A constant one-node program: no benchmark, source file or seed is consulted.
    allowed={}
    with tempfile.TemporaryDirectory(prefix='frontier-profile-') as d:
        for mode in (True,False):
            data,_=q.graph(p.const(7),1,0);raw=Path(d)/('atomic.wasm' if mode else 'serial.wasm')
            p.compile(q.scheduler(data,mode),raw);opt=raw.with_name(raw.stem+'-O3.wasm');q.optimize(raw,opt)
            for f in (raw,opt):allowed[fingerprint(f.read_bytes())]=dict(atomic=mode,opt='O3' if f==opt else 'raw')
    return allowed

def memory_image(b):
    mem=bytearray(65536)
    for sid,v in sections(b):
        if sid!=11:continue
        r=Reader(v)
        for _ in range(r.leb()):
            flags=r.leb()
            if flags==2:
                if r.leb()!=0:raise ValueError('memory index')
            elif flags!=0:raise ValueError('passive data not in profile')
            if r.byte()!=0x41:raise ValueError('constant data offset required')
            off=r.leb(True)
            if r.byte()!=0x0b:raise ValueError('offset expression')
            z=r.take(r.leb())
            if off<0 or off+len(z)>len(mem):raise ValueError('data out of range')
            mem[off:off+len(z)]=z
        if r.i!=len(v):raise ValueError('trailing data bytes')
    return mem

def decode(b,allowed):
    start=time.perf_counter();profile=allowed.get(fingerprint(b))
    if profile is None:raise ValueError('unsupported runtime profile (code/import/type/export changed)')
    m=memory_image(b);N,n,root,count=struct.unpack_from('<4I',m)
    if not 1<=N<=q.LIMIT or not 1<=n<=16 or root>=N:raise ValueError('invalid header')
    if any(m[16:q.BASE]) or any(m[q.BASE+N*q.STRIDE:]):raise ValueError('noncanonical initial workspace')
    rows=[struct.unpack_from('<8I',m,q.BASE+q.STRIDE*i) for i in range(N)]
    succ=[[] for _ in rows];indeg=[0]*N;deps=[];opcount=0
    for i,(op,a,b,c,v,state,owner,reserved) in enumerate(rows):
        if op>=len(q.OPS)+2 or owner!=0xffffffff or reserved:raise ValueError('record profile')
        if state!=(3 if op<2 else 0):raise ValueError('invalid initial state')
        if op==0:
            if a or b or c:raise ValueError('constant record')
            ds=[]
        elif op==1:
            if a>=n or b or c or v:raise ValueError('argument record')
            ds=[]
        else:
            opcount+=1;arity=q.ARITY[q.OPS[op-2]];ds=[a,b,c][:arity]
            if max(a,b,c)>=N or v:raise ValueError('dependency record')
            if [a,b,c][arity:]!=[a]*(3-arity):raise ValueError('padding dependency')
        deps.append(ds);indeg[i]=len(set(ds))
        for j in set(ds):succ[j].append(i)
    if count!=opcount:raise ValueError('operation count')
    queue=collections.deque(i for i,x in enumerate(indeg) if x==0);values={};order=[]
    while queue:
        i=queue.popleft();op,a,b,c,v,*_=rows[i]
        values[i]=p.const(v) if op==0 else p.node('arg',a) if op==1 else p.expr(q.OPS[op-2],*(values[j] for j in deps[i]))
        order.append(i)
        for j in succ[i]:
            indeg[j]-=1
            if not indeg[j]:queue.append(j)
    if len(order)!=N:raise ValueError('cyclic dependency; scheduler need not terminate')
    return n,values[root],dict(profile=profile,nodes=N,operations=count,visited=N,edges=sum(map(len,deps)),schedule=order,analysis_ms=(time.perf_counter()-start)*1000)

def recover(src,dst,allowed):
    start=time.perf_counter();n,r,info=decode(Path(src).read_bytes(),allowed);text,_=p.wat(n,'"run"',r,'plain');p.compile(text,dst)
    return dict(info,status='recovered',total_ms=(time.perf_counter()-start)*1000,bytes=Path(dst).stat().st_size)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('input');a.add_argument('output');v=a.parse_args()
    print(json.dumps(recover(v.input,v.output,profiles())))
