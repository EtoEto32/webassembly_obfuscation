"""Restricted actual-Wasm to GC alias circuit experiment, not a general obfuscator."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'research/observation-synthesis'))
from transform import parse, emit
TOOLS = Path(os.environ.get('WASM_TOOLS_ROOT', ROOT/'.tools'))
BIN = TOOLS/'binaryen-version_133/bin'
WABT = TOOLS/'wabt-1.0.42/bin'
FEATURES = ['--mvp-features','--enable-reference-types','--enable-gc']


def tool(name, args, wabt=False):
    p = (WABT if wabt else BIN)/(name+'.exe')
    return subprocess.run([str(p), *map(str,args)], capture_output=True, text=True,
                          check=True, timeout=60).stdout


HEAD = '''(type $C (struct (field (mut (ref null $C)))))
(type $P (struct (field (ref $C)) (field (ref $C))))
(func $enc (param $b i32) (result (ref $P)) (local $a (ref null $C))
  (local.set $a (struct.new_default $C))
  (struct.new $P (ref.as_non_null (local.get $a))
    (if (result (ref $C)) (local.get $b)
      (then (ref.as_non_null (local.get $a)))
      (else (struct.new_default $C)))))
(func $nand (param $p (ref $P)) (param $q (ref $P)) (result (ref $P))
  (local $a (ref null $C)) (local $b (ref null $C)) (local $u (ref null $C))
  (local.set $a (struct.new_default $C))
  (local.set $b (struct.new_default $C))
  (struct.set $C 0 (struct.get $P 0 (local.get $q)) (local.get $a))
  (struct.set $C 0 (struct.get $P 1 (local.get $q)) (local.get $b))
  (local.set $u (struct.get $C 0 (struct.get $P 0 (local.get $q))))
  (struct.set $C 0 (struct.get $P 0 (local.get $p)) (local.get $a))
  (struct.set $C 0 (struct.get $P 1 (local.get $p)) (local.get $u))
  (struct.new $P (ref.as_non_null (local.get $a))
    (ref.as_non_null (struct.get $C 0 (struct.get $P 0 (local.get $p))))))
(func $dec (param $p (ref $P)) (result i32)
  (ref.eq (struct.get $P 0 (local.get $p)) (struct.get $P 1 (local.get $p))))'''


class Circuit:
    def __init__(self):
        self.nodes=[]
        self.intern={}
    def node(self,*n):
        if n not in self.intern:
            self.intern[n]=len(self.nodes);self.nodes.append(n)
        return self.intern[n]
    def nand(self,a,b):
        return self.node('nand',*sorted([a,b]))
    def inv(self,a):return self.nand(a,a)
    def land(self,a,b):return self.inv(self.nand(a,b))
    def lor(self,a,b):return self.nand(self.inv(a),self.inv(b))
    def xor(self,a,b):
        t=self.nand(a,b)
        return self.nand(self.nand(a,t),self.nand(b,t))
    def word(self,e):
        op=e[0]
        if op=='local.get':return [self.node('input',int(e[1]),i) for i in range(32)]
        if op=='i32.const':return [self.node('const',(int(e[1],0)>>i)&1) for i in range(32)]
        if op=='i32.rotl' and e[2][0]=='i32.const':
            a=self.word(e[1]);k=int(e[2][1],0)&31
            return [a[(i-k)&31] for i in range(32)]
        if op not in ['i32.and','i32.or','i32.xor','i32.add']:
            raise ValueError('Unsupported expression '+emit(e))
        a,b=self.word(e[1]),self.word(e[2])
        if op=='i32.add':
            carry=self.node('const',0);out=[]
            for x,y in zip(a,b):
                t=self.xor(x,y);out.append(self.xor(t,carry))
                carry=self.lor(self.land(x,y),self.land(t,carry))
            return out
        f={'i32.and':self.land,'i32.or':self.lor,'i32.xor':self.xor}[op]
        return [f(x,y) for x,y in zip(a,b)]


def read_source(src):
    tool('wasm-validate',[src],True)
    m=parse(tool('wasm2wat',[src,'--fold-exprs'],True))
    funcs=[x for x in m[1:] if x[0]=='func']
    if len(funcs)!=1 or any(x[0] not in ('func','type','export') for x in m[1:]):
        raise ValueError('Only one pure function and type/export declarations supported')
    f=funcs[0];params=[];body=[];result=[]
    for x in f[1:]:
        if not isinstance(x,list):raise ValueError('Unexpected named function')
        if x[0]=='param':params.extend(x[1:])
        elif x[0]=='result':result.extend(x[1:])
        elif x[0] not in ('type','export'):body.append(x)
    if any(x!='i32' for x in params) or result!=['i32'] or len(body)!=1:
        raise ValueError('Only i32 parameters and one i32 expression supported')
    exports=[x for x in m[1:] if x[0]=='export']
    if len(exports)!=1 or exports[0]!=['export','"run"',['func','0']]:
        raise ValueError('Expected sole export run, function 0')
    def check(e):
        if e[0]=='local.get' and not 0<=int(e[1])<len(params):raise ValueError('Local index')
        for x in e[1:]:
            if isinstance(x,list):check(x)
    check(body[0]);return len(params),body[0]


def transform(src,out):
    if out.exists() or Path(str(out)+'.json').exists():raise ValueError('Refuse overwrite')
    t=time.perf_counter();n,e=read_source(src);c=Circuit();outputs=c.word(e)
    lines=[]
    for i,nd in enumerate(c.nodes):
        if nd[0]=='input':
            rhs=f'(call $enc (i32.and (i32.shr_u (local.get {nd[1]}) (i32.const {nd[2]})) (i32.const 1)))'
        elif nd[0]=='const':rhs=f'(call $enc (i32.const {nd[1]}))'
        else:rhs=f'(call $nand (ref.as_non_null (local.get $v{nd[1]})) (ref.as_non_null (local.get $v{nd[2]})))'
        lines.append(f'(local.set $v{i} {rhs})')
    final='(i32.const 0)'
    for i,x in enumerate(outputs):
        final=f'(i32.or {final} (i32.shl (call $dec (ref.as_non_null (local.get $v{x}))) (i32.const {i})))'
    text='(module\n'+HEAD+'\n(func $run (export "run") '+('(param i32) '*n)+'(result i32)\n'
    text+='\n'.join(f'(local $v{i} (ref null $P))' for i in range(len(c.nodes)))+'\n'
    text+='\n'.join(lines)+'\n'+final+'))\n'
    out.parent.mkdir(parents=True,exist_ok=True);wp=Path(str(out)+'.wat');wp.write_text(text,encoding='utf-8')
    tool('wasm-as',[wp,*FEATURES,'-o',out])
    # Binaryen validates by default. There is no --validate flag in version 133.
    tool('wasm-opt',[out,*FEATURES,'-o',Path(str(out)+'.validated.wasm')])
    r={'input_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),
       'output_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),
       'parameters':n,'nodes':len(c.nodes),'nand_gates':sum(x[0]=='nand' for x in c.nodes),
       'seconds':time.perf_counter()-t,'bytes':out.stat().st_size,
       'scope':'Pure single-function i32 AND/OR/XOR/ADD and constant ROTL; resource failures excluded.'}
    Path(str(out)+'.json').write_text(json.dumps(r,indent=2),encoding='utf-8');return r


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('input',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();print(json.dumps(transform(a.input,a.output)))
