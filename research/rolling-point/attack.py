"""Known-prefix/suffix BSGS; no private bytes or generation seed in recover()."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import time
import transform as T


def decode(token):
    s=token[1:-1]; out=bytearray(); i=0
    escape={'t':9,'n':10,'r':13,'"':34,"'":39,'\\':92}
    while i<len(s):
        if s[i]!='\\':out.extend(s[i].encode('utf8'));i+=1
        elif i+2<len(s) and re.fullmatch('[0-9a-fA-F]{2}',s[i+1:i+3]):
            out.append(int(s[i+1:i+3],16));i+=3
        else:out.append(escape[s[i+1]]);i+=2
    return bytes(out)


def target(src):
    ast=T.W.parse(T.tool('wasm2wat',[src,'--fold-exprs']))
    mem=bytearray(3*65536)
    for d in (x for x in ast[1:] if x[0]=='data'):
        parts=d[1:]
        if parts[0][0]!='memory' or parts[0][1]!='1':
            raise ValueError('Unexpected active data memory')
        if parts[1][0]!='i32.const':raise ValueError('Unexpected offset')
        off=int(parts[1][1])
        blob=b''.join(decode(x) for x in parts[2:])
        mem[off:off+len(blob)]=blob
    return int.from_bytes(mem[512:768],'little') * pow(T.R,-1,T.P) % T.P


def recover(encoded, prefix, suffix, unknown_bytes):
    if unknown_bytes not in (1,2,3):raise ValueError('This experiment caps the unknown interval at 24 bits')
    start=time.perf_counter_ns()
    known=(int.from_bytes(prefix,'big') << (8*(unknown_bytes+len(suffix)))) + int.from_bytes(suffix,'big')
    base=pow(T.G,pow(256,len(suffix),T.Q),T.P)
    wanted=encoded * pow(T.G,-known % T.Q,T.P) % T.P
    count=256**unknown_bytes; m=math.isqrt(count-1)+1
    baby={}; v=1
    for j in range(m):baby.setdefault(v,j);v=v*base%T.P
    step=pow(base,-m,T.P); gamma=wanted
    for i in range(m+1):
        if gamma in baby:
            x=i*m+baby[gamma]
            if x<count:
                result=prefix+x.to_bytes(unknown_bytes,'big')+suffix
                if pow(T.G,int.from_bytes(result,'big'),T.P)!=encoded:raise AssertionError('Recovery check')
                return result, {'unknown_bits':8*unknown_bytes,'baby_steps':m,'giant_steps':i,
                    'group_multiplications_in_walk':m+i,'recovery_ns':time.perf_counter_ns()-start,
                    'runtime_oracle_queries':0,'attack':'BSGS with all other bytes supplied as auxiliary information'}
        gamma=gamma*step%T.P
    return None, {'status':'not_found'}


def run(directory):
    manifest=json.loads((directory/'manifest.json').read_text())
    records=[]
    for e in manifest['entries']:
        if e['method']=='plain':continue
        src=directory/e['file']; encoded=target(src)
        # The harness supplies explicit auxiliary knowledge; hidden bytes remain absent from recover().
        truth=bytes.fromhex(json.loads((directory/f'l{e["length"]}-truth.json').read_text())['pattern'])
        for n in (1,2,3):
            split=len(truth)//2
            recovered,r=recover(encoded,truth[:split],truth[split+n:],n)
            r.update(file=e['file'],exact_pattern=recovered==truth,
                     input_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),
                     prefix_bytes=split,suffix_bytes=len(truth)-split-n)
            if recovered!=truth:raise AssertionError('Attack mismatch')
            records.append(r)
    result={'records':records,'successes':sum(x['exact_pattern'] for x in records),
            'scope':'Does not recover a completely unknown 16/64/128-byte random pattern. Known prefix/suffix required.'}
    (directory/'attacks.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps({'attacks':len(records),'successes':result['successes']}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directory',type=Path);run(p.parse_args().directory)
