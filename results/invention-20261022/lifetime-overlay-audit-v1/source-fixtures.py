"""Three synthetic kernels. Parameters/depths are not independent applications."""
def module(code):
    return ('(module (memory 1 1) (func (export "run") (param $x i32) (param $y i32) '
            '(result i32) (local $a i32) (local $v i64) '+code+'))')


def get(t,a):return f'({t}.load (i32.const {a}))'
def put(t,a,v):return f'({t}.store (i32.const {a}) {v})'
def pair(lo,hi):return f'(i64.or (i64.extend_i32_u {lo}) (i64.shl (i64.extend_i32_u {hi}) (i64.const 32)))'
def fold(v):return f'(i32.xor (i32.wrap_i64 {v}) (i32.wrap_i64 (i64.shr_u {v} (i64.const 32))))'


def serial():
    xs=['(local.set $a (i32.xor (local.get $x) (local.get $y)))']
    for k in range(6):
        a=64*k;b=a+16
        xs += [put('i32',a,f'(i32.add (local.get $a) (i32.const {17+2*k}))'),
               put('i64',b,pair(f'(i32.mul (local.get $a) (i32.const {3+2*k}))','(local.get $y)')),
               f'(local.set $a (i32.rotl (i32.xor {get("i32",a)} {fold(get("i64",b))}) (i32.const {k+1})))']
    return module(' '.join(xs+['(local.get $a)']))


def branch():
    xs=[put('i32',0,'(i32.add (local.get $x) (local.get $y))'),
        '(if (i32.and (local.get $x) (i32.const 1)) (then '+put('i64',16,pair('(local.get $x)','(local.get $y)'))+
        ') (else '+put('i64',16,pair('(local.get $y)','(local.get $x)'))+'))',
        f'(local.set $a (i32.xor {get("i32",0)} {fold(get("i64",16))}))',
        '(if (i32.and (local.get $y) (i32.const 2)) (then '+
        put('i32',32,'(i32.mul (local.get $a) (i32.const 1664525))')+
        f' (local.set $a {get("i32",32)})) (else '+
        put('i64',48,f'(i64.mul {pair("(local.get $a)","(local.get $x)")} (i64.const 4294967311))')+
        f' (local.set $a {fold(get("i64",48))})))',
        put('i64',64,pair('(local.get $a)','(local.get $y)')),
        fold(f'(i64.rotl {get("i64",64)} (i64.const 13))')]
    return module(' '.join(xs))


def diamond(depth=16):
    xs=[put('i64',0,pair('(local.get $x)','(local.get $y)'))]
    for k in range(depth):
        a=32+32*k;b=a+16
        xs += [f'(if (i32.and (local.get $x) (i32.const {1<<k})) (then '+
               put('i32',a,f'(i32.add {fold(get("i64",0))} (i32.const {k*31+7}))')+
               ' '+put('i64',0,f'(i64.xor (i64.rotl {get("i64",0)} (i64.const {k+1})) (i64.extend_i32_u {get("i32",a)}))')+
               ') (else '+put('i64',b,f'(i64.add {get("i64",0)} (i64.const {4294967311+k}))')+
               ' '+put('i64',0,f'(i64.mul {get("i64",b)} (i64.const {3+2*k}))')+'))']
    return module(' '.join(xs+[fold(get('i64',0))]))


FIXTURES={'serial':serial,'branch':branch,'diamond':diamond}
