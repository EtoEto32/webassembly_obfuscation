import argparse
import hashlib
import json
from pathlib import Path
import random
import statistics
import subprocess
import sys
import time
import transform as T


def engines(directory, manifest):
    dest=directory/'wabt-check';dest.mkdir(exist_ok=False)
    records=[]
    for e in manifest['entries']:
        if e['opt']!='O3':continue
        ast=T.W.parse(T.tool('wasm2wat',[directory/e['file'],'--fold-exprs']))
        fun=next(x[2][1] for x in ast if isinstance(x,list) and x[:2]==['export','"run"'])
        pattern=bytes.fromhex(json.loads((directory/f'l{e["length"]}-truth.json').read_text())['pattern'])
        token='"'+''.join('\\%02x'%x for x in pattern)+'"'
        ast.append(['data',['i32.const','3'],token])
        for name,ptr,length in [('positive',0,len(pattern)+3),('empty',65536,0),('bounds',65536,1)]:
            ast.append(['func',['export','"'+name+'"'],['result','i32'],['call',fun,['i32.const',str(ptr)],['i32.const',str(length)]]])
        out=dest/e['file'];T.assemble(T.W.emit(ast),out)
        log=T.tool('wasm-interp',[out,'--run-all-exports'])
        (dest/(e['file']+'.log')).write_text(log,encoding='utf8')
        if 'positive() => i32:3' not in log or 'empty() => i32:4294967295' not in log or 'bounds() => error: out of bounds memory access' not in log:
            raise AssertionError(log)
        records.append({'file':e['file'],'status':'passed','cases':3})
    (directory/'wabt-checks.json').write_text(json.dumps(records,indent=2),encoding='utf8')


def domain(directory):
    # Explicit finite-domain counterexample if length 256 were accepted.
    assert T.Q < 256**256
    assert pow(T.G,0,T.P)==pow(T.G,T.Q,T.P)
    assert pow(T.G,1<<32,T.P)!=1
    prime=2013265921
    rng=random.Random(4812);cases=0
    for bits in (8,16,24):
        g=pow(31,(prime-1)//(1<<bits),prime)
        assert pow(g,1<<bits,prime)==1 and pow(g,1<<(bits-1),prime)==prime-1
        for secret in [0,1,(1<<bits)-1]+[rng.randrange(1<<bits) for _ in range(100)]:
            h=pow(g,secret,prime);found=0
            for k in range(bits):
                residual=h*pow(g,-found,prime)%prime
                bit=pow(residual,1<<(bits-1-k),prime)
                assert bit in (1,prime-1)
                if bit==prime-1:found+=1<<k
            assert secret==found;cases+=1
    (directory/'domain-checks.json').write_text(json.dumps({
        'length256_collision':'0 and q have equal group images but different 256-byte encodings',
        'word_wrap_counterexample':'g^(2^32) != g^0 although word32(2^32) == word32(0)',
        'smooth_order_log_cases':cases,'smooth_order_bits':[8,16,24],
        'mismatches':0,'note':'Known group-theoretic limitations; not new cryptographic results.'},indent=2),encoding='utf8')


def performance(directory,manifest):
    jobs=[(r,e) for r in range(3) for e in manifest['entries']]
    random.Random(70293).shuffle(jobs)
    results=[]
    for r,e in jobs:
        proc=subprocess.run(['node',str(Path(__file__).with_name('measure.cjs')),str(directory),e['file'],e['method'],str(e['length'])],
                            check=True,capture_output=True,text=True,timeout=60)
        result=json.loads(proc.stdout);result['fresh_process']=r
        result['private_memory_bytes']=e['private_pages']*65536
        result['opt']=e['opt'];result['binary_bytes']=e['bytes'];results.append(result)
    (directory/'performance.json').write_text(json.dumps(results,indent=2),encoding='utf8')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directory',type=Path)
    p.add_argument('--part',choices=['engines','domain','performance'],required=True)
    args=p.parse_args();manifest=json.loads((args.directory/'manifest.json').read_text())
    if args.part=='domain':domain(args.directory)
    else:globals()[args.part](args.directory,manifest)
    print(json.dumps({'part':args.part,'status':'completed'}))
