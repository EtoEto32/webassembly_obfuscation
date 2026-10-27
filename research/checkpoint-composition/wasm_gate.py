"""Check coefficient recovery on raw and optimized actual Wasm examples.

This is a preselection rejection gate, not a general loop transformation CLI.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
from probe import compose, mul, recover

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'research/observation-synthesis'))
from transform import parse, emit, tool
BIN=Path(os.environ.get('WASM_TOOLS_ROOT',ROOT/'.tools'))/'binaryen-version_133/bin'
M=1<<32


def plus(a,b,sign=1):
    out=[0]*max(len(a),len(b))
    for i,x in enumerate(a):out[i]=(out[i]+x)%M
    for i,x in enumerate(b):out[i]=(out[i]+sign*x)%M
    return out


def extract(src):
    module=parse(tool('wasm2wat',[src,'--fold-exprs']))
    fs=[x for x in module[1:] if x[0]=='func']
    if len(fs)!=1:raise ValueError('Expected sole polynomial function')
    env={'0':[0,1]}
    def ev(e):
        op=e[0]
        if op=='local.get':return env[e[1]]
        if op=='i32.const':return [int(e[1],0)%M]
        if op in ['local.set','local.tee']:
            v=ev(e[2]);env[e[1]]=v;return v
        if op=='i32.add':return plus(ev(e[1]),ev(e[2]))
        if op=='i32.sub':return plus(ev(e[1]),ev(e[2]),-1)
        if op=='i32.mul':return mul(ev(e[1]),ev(e[2]),M)
        if op=='i32.shl' and e[2][0]=='i32.const':return mul(ev(e[1]),[1<<(int(e[2][1],0)&31)],M)
        raise ValueError('Unsupported polynomial extraction: '+op)
    result=None
    for e in fs[0][1:]:
        if isinstance(e,list) and e[0] not in ['type','param','result','local']:result=ev(e)
    while len(result)>1 and result[-1]==0:result.pop()
    return result


def horner(p,arg):
    result=['i32.const',str(p[-1])]
    for c in reversed(p[:-1]):result=['i32.add',['i32.mul',result,arg],['i32.const',str(c)]]
    return result


def assemble(expr,wp,bp):
    wp.write_text(emit(['module',['func',['export','"run"'],['param','i32'],['result','i32'],expr]]),encoding='utf-8')
    tool('wat2wasm',[wp,'-o',bp]);tool('wasm-validate',[bp])


def run(out):
    out.mkdir(parents=True,exist_ok=False);(out/'source').mkdir()
    for name in ['wasm_gate.py','probe.py']:shutil.copy2(Path(__file__).with_name(name),out/'source'/name)
    rng=random.Random(180026);sources=[(0,0,1),(1,1,1),(0xffffffff,0x80000000,0x9e3779b1)]
    sources += [(rng.getrandbits(32),rng.getrandbits(32),rng.getrandbits(32)|1) for _ in range(3)]
    rows=[];analyses=[]
    for i,p in enumerate(sources):
        x=['local.get','0'];q=compose(p,p,M)
        expressions={'original':horner(p,horner(p,x)),'composed':horner(q,x)}
        for mode,e in expressions.items():assemble(e,out/f'{i}-{mode}.wat',out/f'{i}-{mode}.wasm')
        for opt in ['raw','O2','O3']:
            paths={}
            for mode in expressions:
                bp=out/f'{i}-{mode}.wasm'
                if opt!='raw':
                    dst=out/f'{i}-{mode}-{opt}.wasm'
                    subprocess.run([str(BIN/'wasm-opt.exe'),str(bp),'-'+opt,'-o',str(dst)],capture_output=True,check=True,timeout=30)
                    bp=dst;tool('wasm-validate',[bp])
                paths[mode]=bp
            # Analyze only the composed binary. Original coefficients are scoring metadata.
            coefficients=extract(paths['composed']);learned=recover(coefficients,32)
            assert learned['status']=='recovered' and tuple(p) in learned['roots']
            candidate=learned['roots'][0];bp=out/f'{i}-recovered-{opt}.wasm'
            assemble(horner(candidate,horner(candidate,x)),bp.with_suffix('.wat'),bp);paths['recovered']=bp
            analyses.append({'fixture':i,'optimization':opt,'coefficients':coefficients,**learned,
                'source_in_roots':tuple(p) in learned['roots'],'selected_equals_source':tuple(candidate)==tuple(p)})
            for mode,bp in paths.items():rows.append({'fixture':i,'mode':mode,'optimization':opt,
                'wasm':bp.name,'bytes':bp.stat().st_size,'sha256':hashlib.sha256(bp.read_bytes()).hexdigest(),'source':p})
    manifest={'rows':rows,'analyses':analyses};(out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    js='''const fs=require('fs'),path=require('path');
const dir=process.argv[1],m=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json')));
let s=0x162918;const next=()=>{s^=s<<13;s^=s>>>17;s^=s<<5;return s>>>0;};
const inputs=[0,1,2,3,0x7fffffff,0x80000000,0xfffffffe,0xffffffff,...Array.from({length:256},next)];
let total=0,bad=0;const rows=[];
for(const row of m.rows){const b=fs.readFileSync(path.join(dir,row.wasm));if(!WebAssembly.validate(b))throw Error('validate');
 const f=new WebAssembly.Instance(new WebAssembly.Module(b)).exports.run;
 const [c,d,a]=row.source.map(BigInt);const ref=x=>BigInt.asUintN(32,a*x*x+d*x+c);let mismatch=0;
 for(const x of inputs){total++;if(BigInt(f(x)>>>0)!==ref(ref(BigInt(x))))mismatch++;}bad+=mismatch;
 rows.push({wasm:row.wasm,inputs:inputs.length,mismatch});}
const r={node:process.version,v8:process.versions.v8,conditions:rows.length,executions:total,mismatches:bad,rows};
fs.writeFileSync(path.join(dir,'checks.json'),JSON.stringify(r,null,2));console.log(JSON.stringify({conditions:r.conditions,executions:total,mismatches:bad}));if(bad)process.exitCode=1;'''
    (out/'source/check.cjs').write_text(js,encoding='utf-8')
    subprocess.run([shutil.which('node'),'-e',js,str(out)],check=True,timeout=30)
    print(json.dumps({'recovered_conditions':len(analyses),'source_exactly_selected':sum(x['selected_equals_source'] for x in analyses)}))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);a=ap.parse_args();run(a.output)
