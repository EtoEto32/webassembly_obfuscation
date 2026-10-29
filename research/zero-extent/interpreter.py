"""Independent WABT execution at selected boundary cases, with memory probes."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import prototype as p

def reference(name,args,size):
    a,b,n,v,c=args;mem=bytearray([90])*size;trap=False
    def put(addr,value,width):
        nonlocal trap
        if addr+width>size:trap=True;return False
        for i in range(width):mem[addr+i]=(value>>(8*i))&255
        return True
    def bulk(kind,d,s,n):
        nonlocal trap
        if d+n>size or (kind=='copy' and s+n>size):trap=True;return False
        mem[d:d+n]=mem[s:s+n] if kind=='copy' else bytes([s&255])*n
        return True
    if name=='byte':put(a,v,1) if c else put(b,v^165,1)
    elif name=='wide':
        if v<n:
            if put(a+7,(v*2654435761)&0xffffffff,4):put(b+1,n,2)
        elif put(b+3,v^n,2):put(a,c,1)
    elif name=='nested':
        if c:
            if put(a,v,1):put(b+2,n,4) if v&1 else put(a+11,n,2)
        elif put(a,(v+n)&0xffffffff,4):put(b,v,1)
    elif name=='bulk':
        if c:
            if bulk('copy',a,b,n):put(a+4,v,4)
        elif bulk('fill',b,v,n):put(a,v>>8,1)
    else:raise ValueError(name)
    return trap,(v^n)&0xffffffff,mem

def main():
    ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    manifest=json.loads((a.input/'manifest.json').read_text(encoding='utf-8'));rows=[]
    probes=[0,1,2,4,7,16,24,65524,65525,65526,65527,65528,65529,65530,65531,65532,65533,65534,65535]
    cases=[('zero',0,[0xffffffff,0,0,1,0]),('safe',1,[16,24,16,17,1]),('edge',1,[65534,65534,4,1,1]),('overflow',1,[0xffffffff,0,0,1,1])]
    for item in manifest['files']:
        module,_,_=p.read(a.input/item['path'])
        for label,pages,args in cases:
            m=module[:];m.append(['func',['export','"check"'],['result','i32'],p.op('drop',p.op('memory.grow',p.c(pages))),
                                 p.op('memory.fill',p.c(0),p.c(90),p.c(pages*65536)),p.op('call','0',*[p.c(v) for v in args])])
            for i,addr in enumerate(probes):m.append(['func',['export',f'"byte{i}"'],['result','i32'],p.op('i32.load8_u',p.c(addr))])
            target=out/(Path(item['path']).stem+'.'+label+'.wasm');p.compile_wat(p.w.emit(m),target)
            log=p.w.tool('wasm-interp',[target,'--run-all-exports']);target.with_suffix('.log').write_text(log,encoding='utf-8')
            trap,value,mem=reference(item['model'],args,pages*65536)
            assert ('check() => error:' in log)==trap,(item,label,log)
            if not trap:assert f'check() => i32:{value}' in log,(item,label,log)
            for i,addr in enumerate(probes):
                if addr<len(mem):assert f'byte{i}() => i32:{mem[addr]}\n' in log,(item,label,addr,log)
                else:assert f'byte{i}() => error:' in log,(item,label,addr,log)
            rows.append(dict(path=item['path'],case=label,trap=trap,probes=len(probes)))
    result=dict(engine='WABT',writer_calls=len(rows),probe_calls=len(rows)*len(probes),mismatches=0,rows=rows,
                input=str(a.input),source_hashes={str(Path(__file__).name):hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    (out/'checks.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='rows'}))
if __name__=='__main__':main()
