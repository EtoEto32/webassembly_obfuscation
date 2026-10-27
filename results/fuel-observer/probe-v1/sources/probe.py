"""Finite fixtures and a direct interpreter independent of the cost-envelope analysis."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import random
import shutil
import subprocess
import transform as t

HERE=Path(__file__).resolve().parent


def work(n):
    return [['local.set','2',['i32.add',['i32.mul',['i32.xor',['local.get','2'],['i32.const','13']],['i32.const','1664525']],['i32.const','1013904223']]] for _ in range(n)]


def mark(i,v):return ['call','0',['i32.const',str(i)],['i32.const',str(v)]]
def branch(bit,a,b):return ['if',['i32.and',['local.get','0'],['i32.const',str(bit)]],['then',*a],['else',*b]]


def fixture(kind):
    if kind=='early-split':body=[branch(1,work(9)+[mark(100,1)]+work(1),work(1)+[mark(100,0)]+work(1))]
    elif kind=='hidden-tail':body=[branch(1,work(6),work(1)),mark(100,0),branch(2,work(1),work(8))]
    elif kind=='two-release':body=[branch(1,work(8)+[mark(100,1),branch(2,work(1),work(8)),mark(101,1)]+work(8),work(1)+[mark(100,0),branch(2,work(8),work(1)),mark(101,0)]+work(1))]
    elif kind=='uneven-word':body=[branch(1,[mark(100,1)]+work(8)+[mark(102,7)]+work(1),work(1)+[mark(100,0)]+work(2))]
    elif kind=='compensate':body=[branch(1,work(9)+[mark(100,0)]+work(1),work(1)+[mark(100,0)]+work(9))]
    elif kind=='correlated':body=[branch(1,work(9),work(1)),mark(100,0),branch(1,work(1),work(9))]
    elif kind=='no-event':body=[branch(1,work(9),work(1))]
    else:raise ValueError(kind)
    return ['module',['type',['func',['param','i32','i32']]],['import','"env"','"mark"',['func',['type','0']]],
      ['func',['param','i32','i32'],['result','i32'],['local','i32'],['local.set','2',['local.get','1']],*body,['local.get','2']],['export','"run"',['func','1']]]


def interpret(tree,secret,x):
    local=[secret&0xffffffff,x&0xffffffff,0];spent=0;events=[]
    def ev(node):
        nonlocal spent
        op=node[0];spent+=1
        if op=='i32.const':return int(node[1])&0xffffffff
        if op=='local.get':return local[int(node[1])]
        if op=='local.set':local[int(node[1])]=ev(node[2]);return
        if op=='if':
            condition=ev(node[1]);arm=node[2] if condition else node[3]
            for child in arm[1:]:ev(child)
            return
        if op=='call':
            label=[ev(node[2]),ev(node[3])];events.append({'label':label,'cost':spent});return
        if op=='i32.eqz':return int(ev(node[1])==0)
        a,b=ev(node[1]),ev(node[2])
        if op=='i32.add':return (a+b)&0xffffffff
        if op=='i32.mul':return (a*b)&0xffffffff
        if op=='i32.xor':return a^b
        if op=='i32.and':return a&b
        raise ValueError(op)
    f=next(y for y in tree[1:] if y[0]=='func');value=None
    for node in f[1:]:
        if node[0] not in ('type','param','result','local'):value=ev(node)
    return {'value':value,'events':events,'total':spent}


def main(out):
    out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
    for p in HERE.iterdir():
        if p.suffix in ('.py','.cjs','.md'):shutil.copy2(p,out/'sources'/p.name)
    shutil.copy2(t.ROOT/'research/connectivity-elimination/prototype.py',out/'sources/wat-helper.py')
    rng=random.Random(2026102412);xs=[0,1,0x7fffffff,0x80000000,0xffffffff]+[rng.getrandbits(32) for _ in range(27)]
    kinds=('early-split','hidden-tail','two-release','uneven-word','compensate','correlated','no-event');records=[]
    try:
        for kind in kinds:
            folder=out/kind;folder.mkdir();tree=fixture(kind);src=folder/'original.wasm';(folder/'original.wat').write_text(t.w.emit(tree),encoding='utf8');t.w.tool('wat2wasm',[folder/'original.wat','-o',src])
            report=t.transform(src,folder/'target.wasm');t.w.tool('wasm-opt',[folder/'target.wasm','-O3','-o',folder/'target-O3.wasm']);t.w.tool('wasm-validate',[folder/'target-O3.wasm'])
            oracle=[{'secret':s,'x':x,**interpret(tree,s,x)} for s in range(16) for x in xs]
            (folder/'oracle.json').write_text(json.dumps(oracle,indent=2),encoding='utf8')
            records.append({'kind':kind,'paths':report['pathCount'],'nodes':len(report['nodes']),'whole':report['whole'],'sourceBytes':report['sourceBytes'],'targetBytes':report['targetBytes'],'optimizedBytes':(folder/'target-O3.wasm').stat().st_size,'transformSeconds':report['seconds']})
        (out/'manifest.json').write_text(json.dumps({'seed':2026102412,'python':platform.python_version(),'platform':platform.platform(),'records':records},indent=2),encoding='utf8')
        cmd=['node',str(HERE/'run.cjs'),str(out)];r=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
        (out/'run.json').write_text(json.dumps({'command':cmd,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr},indent=2),encoding='utf8')
        if r.returncode:raise RuntimeError(r.stderr)
        print(r.stdout)
    finally:
        (out/'sha256.json').write_text(json.dumps({str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file() and p.name!='sha256.json'},indent=2),encoding='utf8')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);main(p.parse_args().output.resolve())
