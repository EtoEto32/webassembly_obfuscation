"""Small deterministic generator; outputs are observed as i32 bits, never JS NaNs."""
def c(x): return f'(i32.const {x&0xffffffff})'
def get(i): return f'(local.get {i})'
def vec(values): return '(v128.const i32x4 '+' '.join(hex(x&0xffffffff) for x in values)+')'
def splat(i): return f'(i32x4.splat {get(i)})'
def nan_expr():
    bits=f'(i32.or (i32.and {get(0)} {c(0x003fffff)}) {c(0x7fc00000)})'
    return f'(f32.add (f32.reinterpret_i32 {bits}) (f32.const 0))'
def module(locals_,body,count):
    return '(module (func (export "run") (param i32 i32) (result '+' '.join(['i32']*count)+') (local '+' '.join(locals_)+') '+' '.join(body)+'))'
def extracts(i): return [f'(i32x4.extract_lane {k} {get(i)})' for k in range(4)]
def fixtures():
    out=[]
    for seed in range(3):
        a=vec([0x12345678^(seed*0x01010101),0xaabbccdd,0x547698ba,0x11223344]);b=vec([0x87654321,0xddccbbaa,0xabcdef12,0x55667788])
        for bits in (8,32,64):
            op=f'i{bits}x{128//bits}.relaxed_laneselect';mask=splat(1)
            body=[f'(local.set 2 ({op} {a} {b} {mask}))',f'(local.set 3 ({op} {a} {b} (v128.not {mask})))',*extracts(2),*extracts(3)]
            out.append(dict(name=f'lane{bits}-{seed}',kind='laneselect',wat=module(['v128','v128'],body,8)))
        indices=vec([0x13121110,0x17161514,0x1b1a1918,0x1f1e1d1c])
        body=[f'(local.set 2 (i8x16.relaxed_swizzle {a} {indices}))',f'(local.set 3 (i8x16.relaxed_swizzle {b} (v128.xor {indices} {splat(1)})))',*extracts(2),*extracts(3)]
        out.append(dict(name=f'swizzle-{seed}',kind='swizzle',wat=module(['v128','v128'],body,8)))
    ne=nan_expr();rb=lambda i:f'(i32.reinterpret_f32 {get(i)})'
    out.append(dict(name='nan-share',kind='nan',wat=module(['f32'],[f'(local.set 2 {ne})',rb(2),rb(2)],2)))
    out.append(dict(name='nan-independent',kind='nan',wat=module(['f32','f32'],[f'(local.set 2 {ne})',f'(local.set 3 {ne})',rb(2),rb(3)],2)))
    out.append(dict(name='nan-neg-copy',kind='nan',wat=module(['f32'],[f'(local.set 2 {ne})',rb(2),f'(i32.reinterpret_f32 (f32.neg {get(2)}))'],2)))
    body=[f'(local.set 2 {ne})',f'(local.set 3 (i8x16.relaxed_swizzle (i32x4.splat {rb(2)}) {vec([0x13121110]*4)}))',rb(2),rb(2),*extracts(3)]
    out.append(dict(name='mixed-share-swizzle',kind='mixed',wat=module(['f32','v128'],body,6)))
    return out
