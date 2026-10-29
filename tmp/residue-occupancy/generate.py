import ast,pathlib,subprocess,json,hashlib
ROOT=pathlib.Path(__file__).resolve().parent
TOOLS=pathlib.Path('C:/Users/ettotto/Documents/webassembly_obfuscation/.tools')
def expr(text):
    def emit(n):
        if isinstance(n,ast.Name):return f'(local.get ${n.id})'
        if isinstance(n,ast.Constant):return f'(i32.const {n.value})'
        if isinstance(n,ast.BinOp):
            if isinstance(n.op,ast.Pow):
                value=emit(n.left)
                for _ in range(n.right.value-1):value=f'(i32.mul {value} {emit(n.left)})'
                return value
            return f'(i32.{ {ast.Add:"add",ast.Sub:"sub",ast.Mult:"mul"}[type(n.op)]} {emit(n.left)} {emit(n.right)})'
        raise ValueError(ast.dump(n))
    return emit(ast.parse(text,mode='eval').body)
def setv(name,value):return f'(local.set ${name} {value})'
def get(name):return f'(local.get ${name})'
def load(base,offset=0):return f'(i32.load offset={offset} {get(base)})'
def store(base,offset,value):return f'(i32.store offset={offset} {get(base)} {value})'
def acc(s,p,q):
    return [setv('v3',f'(i32.add (i32.add (i32.add {get("e3")} (i32.mul {get("e2")} {s})) (i32.mul {get("e1")} {p})) {q})'),setv('v2',f'(i32.add (i32.add {get("e2")} (i32.mul {get("e1")} {s})) {p})'),setv('e1',f'(i32.add {get("e1")} {s})'),setv('e2',get('v2')),setv('e3',get('v3'))]

manifest=[]
for kind in ['normal','quotient']:
    lines=['(module']
    if kind=='quotient':
        lines+=['(memory 1)','(func $push (param $s i32)(param $p i32)(param $q i32)(param $b i32)(param $d i32)(result i32 i32 i32)(local $s2 i32)(local $sp3 i32)',setv('s2',expr('s*s-2*p')),setv('sp3',expr('s*p-3*q')),expr('2*s2+b*s+3*d'),expr('4*(p*p-2*s*q)+2*b*sp3+4*d*s2+b*b*p+2*b*d*s+3*d*d'),expr('8*q*q+4*b*p*q+4*d*(p*p-2*s*q)+2*b*b*s*q+2*b*d*sp3+2*d*d*s2+b*b*b*q+b*b*d*p+b*d*d*s+d*d*d'),')']
    lines += ['(func (export "run") '+''.join(f'(param $x{i} i32)' for i in range(12))+'(param $u i32)(param $n i32)(result i32 i32 i32)']
    locals_=[f't{i}' for i in range(12)]+['g','b','src','dst','ptr','swap','s','p','q','e1','e2','e3','v2','v3']
    lines += [''.join(f'(local ${v} i32)' for v in locals_)]
    lines += [setv(f'x{i}',f'(i32.or (i32.shl {get(f"x{i}")}(i32.const 2))(i32.const {i//3}))') for i in range(12)]
    if kind=='quotient':
        lines += [setv('src','(i32.const 0)'),setv('dst','(i32.const 48)')]
        for r in range(4):
            a,b,c=[f'x{3*r+j}' for j in range(3)]
            lines += [store('src',12*r,expr(f'{a}+{b}+{c}')),store('src',12*r+4,expr(f'{a}*{b}+{a}*{c}+{b}*{c}')),store('src',12*r+8,expr(f'{a}*{b}*{c}'))]
    lines += [setv('n',f'(i32.and {get("n")}(i32.const 31))'),'(block $exit (loop $loop',f'(br_if $exit (i32.eqz {get("n")}))']
    total=expr('+'.join(f'x{i}' for i in range(12))) if kind=='normal' else f'(i32.add (i32.add {load("src",0)} {load("src",12)}) (i32.add {load("src",24)} {load("src",36)}))'
    lines += [setv('g',f'(i32.and (i32.shr_u {total}(i32.const 2))(i32.const 1))'),setv('b',expr('1+2*g'))]
    if kind=='normal':
        for i in range(12):
            x=f'x{i}';value=expr(f'2*{x}*{x}+b*{x}+u')
            lines.append(setv(f't{i}',f'(i32.add {value}(i32.mul (i32.const 2)(i32.and {get(x)}(i32.const 1))))'))
        lines += [setv(f'x{i}',get(f't{i}')) for i in range(12)]
    else:
        for r in range(4):
            lines += [f'(call $push {load("src",12*r)} {load("src",12*r+4)} {load("src",12*r+8)} {get("b")} (i32.add {get("u")}(i32.const {2*(r&1)})))','(local.set $q)','(local.set $p)','(local.set $s)']
            destination=f'(i32.and (i32.add (select (i32.const {-r})(i32.const {r}) {get("g")}) {get("u")})(i32.const 3))'
            lines += [setv('ptr',f'(i32.add {get("dst")}(i32.mul {destination}(i32.const 12)))'),store('ptr',0,get('s')),store('ptr',4,get('p')),store('ptr',8,get('q'))]
        lines += [setv('swap',get('src')),setv('src',get('dst')),setv('dst',get('swap'))]
    lines += [setv('n',expr('n-1')),'(br $loop)))']
    if kind=='normal':
        for i in range(12):lines += acc(get(f'x{i}'),'(i32.const 0)','(i32.const 0)')
    else:
        for r in range(4):lines += acc(load('src',12*r),load('src',12*r+4),load('src',12*r+8))
    lines += [get('e1'),get('e2'),get('e3'),'))']
    wat=ROOT/(kind+'.wat');wat.write_text('\n'.join(lines));raw=ROOT/(kind+'.wasm');opt=ROOT/(kind+'-O2.wasm')
    for command in [[str(TOOLS/'wabt-1.0.42/bin/wat2wasm.exe'),str(wat),'-o',str(raw)],[str(TOOLS/'binaryen-version_133/bin/wasm-opt.exe'),str(raw),'-O2','--enable-multivalue','-o',str(opt)]]:
        result=subprocess.run(command,text=True,capture_output=True)
        if result.returncode:raise RuntimeError(result.stdout+result.stderr)
    for file in [raw,opt]:manifest.append({'file':file.name,'bytes':file.stat().st_size,'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
(ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest))
