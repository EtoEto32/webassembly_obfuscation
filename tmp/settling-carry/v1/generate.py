"""Prototype compiler for pure integer DAGs with bounded settling updates.
Not an arbitrary-Wasm transformer; novelty/effectiveness remain unestablished.
"""
from pathlib import Path
import hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parent
TOOLS=Path(sys.argv[1]).resolve()
PROGRAMS={
 'mixed':[ ['add','x','y'],['mul',0,'x'],['add',1,'y'],['rotl','x',7],['xor',2,3] ],
 'cross':[ ['add','x','y'],['mul','x','y'],['add',0,1],['rotl',2,5],['add',3,'y'] ],
 'select':[ ['add','x','y'],['rotl','x',3],['mul',0,1],['add',2,'y'],['lt',2,3],['select',0,3,4] ]
}
def parents(node):
    return node[1:2] if node[0]=='rotl' else node[1:]
def bound(nodes,width,carry):
    times=[]
    for node in nodes:
        cost=width if node[0]=='add' and carry else 1
        times.append(max([times[p] if isinstance(p,int) else 0 for p in parents(node)],default=0)+cost)
    return max(times)
def get(arg):
    return f'(local.get ${"s"+str(arg) if isinstance(arg,int) else arg})'
def expr(node):
    op=node[0]
    if op=='select': return f'(select {get(node[1])} {get(node[2])} {get(node[3])})'
    if op=='rotl': return f'(i32.rotl {get(node[1])} (i32.const {node[2]}))'
    wasmop={'add':'add','mul':'mul','xor':'xor','lt':'lt_u'}[op]
    return f'(i32.{wasmop} {get(node[1])} {get(node[2])})'
def update(i,node,mode):
    if mode!='carry' or node[0]!='add': return f'(local.set $s{i} {expr(node)})'
    a,b=get(node[1]),get(node[2]); c=f'(local.get $c{i})'
    # Read old carry for BOTH result and next carry. Target DAG has no self edge.
    return f'''(local.set $s{i} (i32.xor (i32.xor {a} {b}) {c}))
    (local.set $c{i} (i32.shl (i32.or (i32.and {a} {b}) (i32.and (i32.xor {a} {b}) {c})) (i32.const 1)))'''
def module(nodes,mode):
    n=len(nodes)
    out=['(module (func (export "run") (param $x i32) (param $y i32) (param $u i32) (result i32)',
         '(local $round i32) (local $j i32) (local $i i32)',
         ' '.join(f'(local $s{i} i32) (local $c{i} i32)' for i in range(n))]
    if mode=='normal':
        out += [update(i,node,mode) for i,node in enumerate(nodes)]
    else:
        for i in range(n):
            # Public input-dependent, deliberately unsettled initial state.
            out += [f'(local.set $s{i} (i32.xor (local.get $u) (i32.const {i*13+7})))',
                    f'(local.set $c{i} (i32.xor (local.get $u) (i32.const {i*19+11})))']
        out += ['(loop $sweeps',
          f'(local.set $i (i32.rem_u (i32.xor (local.get $u) (local.get $s0)) (i32.const {n})))',
          '(local.set $j (i32.const 0)) (loop $visit']
        for i,node in enumerate(nodes):
            out += [f'(if (i32.eq (local.get $i) (i32.const {i})) (then {update(i,node,mode)}))']
        out += [f'(local.set $i (i32.rem_u (i32.add (local.get $i) (i32.const 1)) (i32.const {n})))',
          '(local.set $j (i32.add (local.get $j) (i32.const 1)))',
          f'(br_if $visit (i32.lt_u (local.get $j) (i32.const {n}))))',
          '(local.set $round (i32.add (local.get $round) (i32.const 1)))',
          f'(br_if $sweeps (i32.lt_u (local.get $round) (i32.const {bound(nodes,32,mode=="carry")}))))']
    out += [f'(local.get $s{n-1}) ))']
    return '\n'.join(out)
manifest={'programs':PROGRAMS,'bounds':{},'binaries':[],'commands':[]}
for name,nodes in PROGRAMS.items():
    manifest['bounds'][name]={m:bound(nodes,32,m=='carry') for m in ('scheduled','carry')}
    for mode in ('normal','scheduled','carry'):
        stem=f'{name}.{mode}'
        wat=ROOT/f'{stem}.wat'; raw=ROOT/f'{stem}.wasm'; opt=ROOT/f'{stem}.O2.wasm'
        wat.write_text(module(nodes,mode),encoding='utf-8')
        for cmd in ([str(TOOLS/'wabt-1.0.42/bin/wat2wasm.exe'),str(wat),'-o',str(raw)],
                    [str(TOOLS/'binaryen-version_133/bin/wasm-opt.exe'),str(raw),'-O2','-o',str(opt)]):
            subprocess.run(cmd,check=True,capture_output=True,text=True)
            manifest['commands'].append(cmd)
        for p in (raw,opt):
            b=p.read_bytes(); manifest['binaries'].append({'file':p.name,'program':name,'mode':mode,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
(ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(json.dumps(manifest['bounds']))
