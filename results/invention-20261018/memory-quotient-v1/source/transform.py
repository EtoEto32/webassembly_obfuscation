"""Restricted immutable-memory consumer projection on actual Wasm binaries."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'research/observation-synthesis'))
import importlib.util
spec=importlib.util.spec_from_file_location('quotient_wat',ROOT/'research/observation-synthesis/transform.py')
W=importlib.util.module_from_spec(spec);spec.loader.exec_module(W)
TOOLS=Path(os.environ.get('WASM_TOOLS_ROOT',ROOT/'.tools'))
SIZE=65536


def decode_string(token):
    if not token.startswith('"') or not token.endswith('"'):raise ValueError('Not a data string')
    s=token[1:-1];out=bytearray();i=0
    escapes={'t':9,'n':10,'r':13,'"':34,"'":39,'\\':92}
    while i<len(s):
        if s[i]!='\\':out.extend(s[i].encode('utf-8'));i+=1;continue
        if i+2<len(s) and re.fullmatch('[0-9a-fA-F]{2}',s[i+1:i+3]):
            out.append(int(s[i+1:i+3],16));i+=3
        elif i+1<len(s) and s[i+1] in escapes:out.append(escapes[s[i+1]]);i+=2
        else:raise ValueError('Unsupported WAT escape')
    return bytes(out)


def inspect(src):
    W.tool('wasm-validate',[src]);m=W.parse(W.tool('wasm2wat',[src,'--fold-exprs']))
    if any(x[0] not in ['type','func','memory','export','data'] for x in m[1:]):
        raise ValueError('Unsupported section')
    funcs=[x for x in m[1:] if x[0]=='func'];mems=[x for x in m[1:] if x[0]=='memory']
    exports=[x for x in m[1:] if x[0]=='export']
    if len(funcs)!=1 or len(mems)!=1 or mems[0] not in [['memory','1'],['memory','1','1']]:
        raise ValueError('Need one function and one private fixed-size memory')
    if len(exports)!=1 or exports[0][2]!=['func','0']:raise ValueError('Need sole function export')
    f=funcs[0]
    if [x for x in f[1:] if isinstance(x,list) and x[0]=='param']!=[['param','i32']]:raise ValueError('Signature')
    if [x for x in f[1:] if isinstance(x,list) and x[0]=='result']!=[['result','i32']]:raise ValueError('Signature')
    body=[x for x in f[1:] if isinstance(x,list) and x[0] not in ['type','param','result']]
    if len(body)!=1 or body[0][0]!='i32.xor' or len(body[0])!=3:raise ValueError('Need two-load XOR')
    offsets=[];address=None
    for load in body[0][1:]:
        if load[0]!='i32.load8_u' or not isinstance(load[-1],list):raise ValueError('Need load8_u')
        off=0
        for t in load[1:-1]:
            if not isinstance(t,str):raise ValueError('Memarg')
            if t.startswith('offset='):off=int(t.split('=')[1],0)
            elif t=='align=1':pass
            else:raise ValueError('Memarg')
        if off<0 or off>=SIZE:raise ValueError('Offset outside profile')
        if address is not None and address!=load[-1]:raise ValueError('Address mismatch')
        address=load[-1];offsets.append(off)
    if address==['local.get','0']:shift=0
    elif len(address)==3 and address[:2]==['i32.shl',['local.get','0']] and address[2][0]=='i32.const':
        shift=int(address[2][1],0)&31
        if shift>15:raise ValueError('Shift outside profile')
    else:raise ValueError('Address outside profile')
    memory=bytearray(SIZE)
    for d in (x for x in m[1:] if x[0]=='data'):
        if len(d)<3 or not isinstance(d[1],list) or d[1][0]!='i32.const':raise ValueError('Active constant data only')
        offset=int(d[1][1],0)&0xffffffff;data=b''.join(decode_string(t) for t in d[2:])
        if offset+len(data)>SIZE:raise ValueError('Instantiating data would trap')
        memory[offset:offset+len(data)]=data
    return {'memory':memory,'shift':shift,'offsets':offsets,'export':exports[0][1]}


def data_token(data):return '"'+''.join('\\%02x'%b for b in data.rstrip(b'\0'))+'"'


def source_module(data,shift,offsets=(0,1),export='"run"'):
    address=['local.get','0'] if shift==0 else ['i32.shl',['local.get','0'],['i32.const',str(shift)]]
    loads=[['i32.load8_u','offset='+str(o),address] for o in offsets]
    return ['module',['memory','1','1'],['data',['i32.const','0'],data_token(data)],
            ['func',['export',export],['param','i32'],['result','i32'],['i32.xor',*loads]]]


def assemble(module,out):
    out=Path(out)
    if out.exists() or out.with_suffix('.wat').exists():raise ValueError('Refuse overwrite')
    out.with_suffix('.wat').write_text(W.emit(module),encoding='utf-8')
    W.tool('wat2wasm',[out.with_suffix('.wat'),'-o',out]);W.tool('wasm-validate',[out])


def transform(src,out):
    t=time.perf_counter_ns();p=inspect(src);s=p['shift'];a,b=p['offsets'];limit=SIZE-1-max(a,b)
    table=bytes(p['memory'][i+a]^p['memory'][i+b] for i in range(0,limit+1,1<<s))
    base=['local.get','1'];index=base if s==0 else ['i32.shr_u',base,['i32.const',str(s)]]
    address=['local.get','0'] if s==0 else ['i32.shl',['local.get','0'],['i32.const',str(s)]]
    module=['module',['memory','1','1'],['data',['i32.const','0'],data_token(table)],
        ['func',['export',p['export']],['param','i32'],['result','i32'],['local','i32'],
            ['local.set','1',address],
            ['if',['result','i32'],['i32.le_u',base,['i32.const',str(limit)]],
                ['then',['i32.load8_u',index]],
                ['else',['i32.load8_u',['i32.const',str(SIZE)]]]]]]
    assemble(module,out)
    return {'shift':s,'offsets':[a,b],'table_entries':len(table),
            'input_bytes':Path(src).stat().st_size,'output_bytes':Path(out).stat().st_size,
            'transformation_ns':time.perf_counter_ns()-t,
            'input_sha256':hashlib.sha256(Path(src).read_bytes()).hexdigest(),
            'output_sha256':hashlib.sha256(Path(out).read_bytes()).hexdigest()}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('output',type=Path)
    args=ap.parse_args();r=transform(args.input,args.output)
    Path(str(args.output)+'.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print(json.dumps(r))
