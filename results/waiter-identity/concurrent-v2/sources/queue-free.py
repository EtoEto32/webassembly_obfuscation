"""Conservative local checker: numeric one-memory guest cannot operate wait queues."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sp=importlib.util.spec_from_file_location('wat',ROOT/'research/connectivity-elimination/prototype.py');w=importlib.util.module_from_spec(sp);sp.loader.exec_module(w)
OPS={'block','loop','if','then','else','br','br_if','return','drop','nop','local.get','local.set','local.tee',
     'i32.const','i32.add','i32.sub','i32.mul','i32.xor','i32.and','i32.or','i32.eqz','i32.eq','i32.ne','i32.lt_u',
     'i32.atomic.load','i32.atomic.store','i32.atomic.rmw.add','i32.load','i32.store','unreachable'}


def check(src):
    data=src.read_bytes()
    if len(data)>65536: raise ValueError('binary size')
    w.tool('wasm-validate',[src,'--enable-threads'])
    m=w.parse(w.tool('wasm2wat',[src,'--fold-exprs','--no-debug-names','--enable-threads']))
    if any(x[0] not in ('type','import','func','export') for x in m[1:]): raise ValueError('module section outside subset')
    imports=[x for x in m[1:] if x[0]=='import']; funcs=[x for x in m[1:] if x[0]=='func']; exports=[x for x in m[1:] if x[0]=='export'];types=[x for x in m[1:] if x[0]=='type']
    if imports!=[['import','"env"','"memory"',['memory','1','4','shared']]]: raise ValueError('exact sole shared-memory import required')
    if len(funcs)!=1 or exports!=[['export','"run"',['func','0']]]: raise ValueError('single numerical entry required')
    if types!=[['type',['func',['param','i32']]]]: raise ValueError('numeric run type required')
    f=funcs[0]; decl=[x for x in f[1:] if x[0] in ('type','param','result','local')]
    if [x for x in decl if x[0]=='param']!=[['param','i32']] or any(x[0]=='result' for x in decl): raise ValueError('entry signature')
    if any(v!='i32' for x in decl if x[0]=='local' for v in x[1:]): raise ValueError('local type')
    counts={};writes=[]
    def visit(x):
        if not isinstance(x,list): return
        if not x or x[0] not in OPS: raise ValueError('unsupported instruction '+str(x[0] if x else None))
        counts[x[0]]=counts.get(x[0],0)+1
        if x[0] in ('i32.store','i32.atomic.store','i32.atomic.rmw.add'):
            operands=[a for a in x[1:] if isinstance(a,list)]; address=operands[0]
            offsets=[a for a in x[1:] if isinstance(a,str) and a.startswith('offset=')]
            offset=int(offsets[0].split('=')[1],0) if offsets else 0
            if address[0]=='i32.const' and len(address)==2:
                start=(int(address[1],0)&0xffffffff)+offset;end=start+4
                if start<65536:writes.append([start,min(end,65536)])
            else:writes.append([0,65536])
        for arg in x[1:]:
            if isinstance(arg,list): visit(arg)
    for x in f[1:]:
        if x not in decl: visit(x)
    stable=next((i for i in range(0,65536,4) if all(i+4<=a or b<=i for a,b in writes)),None)
    return {'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'instructions':counts,'possibleWritesInFirstPage':writes,'stableOffset':stable,'property':'No guest wait/notify or host-call route in the accepted subset. Stable offset excludes all conservatively possible guest writes. This does not attest all external actors or termination.'}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args()
    if a.output.exists():raise ValueError('output exists')
    a.output.write_text(json.dumps(check(a.input),indent=2),encoding='utf8')
