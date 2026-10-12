(module
  (type (;0;) (func (param i32 i32 i32 i32 i32) (result i32 i32 i32 i32)))
  (func (;0;) (type 0) (param i32 i32 i32 i32 i32) (result i32 i32 i32 i32)
    (local v128)
    v128.const i32x4 0x00000000 0x00000000 0x00000000 0x00000000
    local.get 0
    i32x4.replace_lane 0
    local.get 1
    i32x4.replace_lane 1
    local.get 2
    i32x4.replace_lane 2
    local.get 3
    i32x4.replace_lane 3
    v128.const i32x4 0x03020100 0x07060504 0x0b0a0908 0x0f0e0d0c
    local.get 4
    i32.const 15
    i32.and
    local.tee 0
    i8x16.splat
    v128.xor
    i8x16.swizzle
    v128.const i32x4 0x03020100 0x07060504 0x0b0a0908 0x0f0e0d0c
    local.get 0
    local.get 4
    i32.const 4
    i32.shr_u
    i32.const 7
    i32.and
    local.tee 1
    i32.const 1
    i32.shl
    i32.xor
    i8x16.splat
    v128.xor
    i8x16.swizzle
    i16x8.extadd_pairwise_i8x16_u
    local.tee 5
    local.get 5
    i16x8.mul
    v128.const i32x4 0x00250025 0x00250025 0x00250025 0x00250025
    i16x8.add
    v128.const i32x4 0x03020100 0x07060504 0x0b0a0908 0x0f0e0d0c
    local.get 1
    i32.const 1
    i32.shl
    local.get 4
    i32.const 7
    i32.shr_u
    i32.const 3
    i32.and
    local.tee 0
    i32.const 2
    i32.shl
    i32.xor
    i8x16.splat
    v128.xor
    i8x16.swizzle
    i32x4.extadd_pairwise_i16x8_u
    v128.const i32x4 0x03020100 0x07060504 0x0b0a0908 0x0f0e0d0c
    local.get 0
    i32.const 2
    i32.shl
    i8x16.splat
    v128.xor
    i8x16.swizzle
    local.tee 5
    i32x4.extract_lane 0
    local.get 5
    i32x4.extract_lane 1
    local.get 5
    i32x4.extract_lane 2
    local.get 5
    i32x4.extract_lane 3)
  (export "run" (func 0)))
