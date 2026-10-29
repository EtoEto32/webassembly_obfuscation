(module
  (type (;0;) (func (param i32)))
  (type (;1;) (func (result i32)))
  (func (;0;) (type 0) (param i32)
    i32.const 0
    local.get 0
    i32.const 1
    i32.add
    local.get 0
    i32.xor
    i32.store
    i32.const 4
    local.get 0
    i32.const 2
    i32.add
    local.get 0
    i32.xor
    i32.store
    i32.const 8
    local.get 0
    i32.const 4
    i32.add
    local.get 0
    i32.xor
    i32.store
    i32.const 12
    local.get 0
    i32.const 8
    i32.add
    local.get 0
    i32.xor
    i32.store
    i32.const 16
    local.get 0
    i32.const 16
    i32.add
    local.get 0
    i32.xor
    i32.store
    i32.const 20
    local.get 0
    i32.const 32
    i32.add
    local.get 0
    i32.xor
    i32.store
    i32.const 24
    local.get 0
    i32.const -64
    i32.sub
    local.get 0
    i32.xor
    i32.store
    i32.const 28
    local.get 0
    i32.const 128
    i32.add
    local.get 0
    i32.xor
    i32.store
    i32.const 32
    local.get 0
    i32.const 256
    i32.add
    local.get 0
    i32.xor
    i32.store
    i32.const 36
    local.get 0
    i32.const 512
    i32.add
    local.get 0
    i32.xor
    i32.store
    i32.const 40
    local.get 0
    i32.const 1024
    i32.add
    local.get 0
    i32.xor
    i32.store
    i32.const 44
    local.get 0
    i32.const 2048
    i32.add
    local.get 0
    i32.xor
    i32.store
    i32.const 48
    local.get 0
    i32.const 4096
    i32.add
    local.get 0
    i32.xor
    i32.store
    i32.const 52
    local.get 0
    i32.const -8192
    i32.sub
    local.get 0
    i32.xor
    i32.store
    i32.const 56
    local.get 0
    i32.const 16384
    i32.add
    local.get 0
    i32.xor
    i32.store
    i32.const 60
    local.get 0
    i32.const 32768
    i32.add
    local.get 0
    i32.xor
    i32.store
    i32.const 64
    local.get 0
    i32.const 65536
    i32.add
    local.get 0
    i32.xor
    i32.store
    i32.const 68
    local.get 0
    i32.const 131072
    i32.add
    local.get 0
    i32.xor
    i32.store
    i32.const 72
    local.get 0
    i32.const 262144
    i32.add
    local.get 0
    i32.xor
    i32.store
    i32.const 76
    local.get 0
    i32.const 524288
    i32.add
    local.get 0
    i32.xor
    i32.store
    i32.const 80
    local.get 0
    i32.const -1048576
    i32.sub
    local.get 0
    i32.xor
    i32.store
    i32.const 84
    local.get 0
    i32.const 2097152
    i32.add
    local.get 0
    i32.xor
    i32.store
    i32.const 88
    local.get 0
    i32.const 4194304
    i32.add
    local.get 0
    i32.xor
    i32.store
    i32.const 92
    local.get 0
    i32.const 8388608
    i32.add
    local.get 0
    i32.xor
    i32.store
    i32.const 96
    local.get 0
    i32.const 16777216
    i32.add
    local.get 0
    i32.xor
    i32.store
    i32.const 100
    local.get 0
    i32.const 33554432
    i32.add
    local.get 0
    i32.xor
    i32.store
    i32.const 104
    local.get 0
    i32.const 67108864
    i32.add
    local.get 0
    i32.xor
    i32.store
    i32.const 108
    local.get 0
    i32.const -134217728
    i32.sub
    local.get 0
    i32.xor
    i32.store
    i32.const 112
    local.get 0
    i32.const 268435456
    i32.add
    local.get 0
    i32.xor
    i32.store
    i32.const 116
    local.get 0
    i32.const 536870912
    i32.add
    local.get 0
    i32.xor
    i32.store
    i32.const 120
    local.get 0
    i32.const 1073741824
    i32.add
    local.get 0
    i32.xor
    i32.store
    i32.const 124
    local.get 0
    i32.const -2147483648
    i32.sub
    local.get 0
    i32.xor
    i32.store
    i32.const 128
    local.get 0
    i32.const 31
    i32.shr_u
    i32.store)
  (func (;1;) (type 1) (result i32)
    i32.const 0
    i32.load
    i32.const 1
    i32.shr_u
    i32.const 1
    i32.and
    i32.const 128
    i32.load
    i32.const 31
    i32.shl
    i32.or
    i32.const 4
    i32.load
    i32.const 2
    i32.shr_u
    i32.const 1
    i32.and
    i32.const 1
    i32.shl
    i32.or
    i32.const 8
    i32.load
    i32.const 3
    i32.shr_u
    i32.const 1
    i32.and
    i32.const 2
    i32.shl
    i32.or
    i32.const 12
    i32.load
    i32.const 4
    i32.shr_u
    i32.const 1
    i32.and
    i32.const 3
    i32.shl
    i32.or
    i32.const 16
    i32.load
    i32.const 5
    i32.shr_u
    i32.const 1
    i32.and
    i32.const 4
    i32.shl
    i32.or
    i32.const 20
    i32.load
    i32.const 6
    i32.shr_u
    i32.const 1
    i32.and
    i32.const 5
    i32.shl
    i32.or
    i32.const 24
    i32.load
    i32.const 7
    i32.shr_u
    i32.const 1
    i32.and
    i32.const 6
    i32.shl
    i32.or
    i32.const 28
    i32.load
    i32.const 8
    i32.shr_u
    i32.const 1
    i32.and
    i32.const 7
    i32.shl
    i32.or
    i32.const 32
    i32.load
    i32.const 9
    i32.shr_u
    i32.const 1
    i32.and
    i32.const 8
    i32.shl
    i32.or
    i32.const 36
    i32.load
    i32.const 10
    i32.shr_u
    i32.const 1
    i32.and
    i32.const 9
    i32.shl
    i32.or
    i32.const 40
    i32.load
    i32.const 11
    i32.shr_u
    i32.const 1
    i32.and
    i32.const 10
    i32.shl
    i32.or
    i32.const 44
    i32.load
    i32.const 12
    i32.shr_u
    i32.const 1
    i32.and
    i32.const 11
    i32.shl
    i32.or
    i32.const 48
    i32.load
    i32.const 13
    i32.shr_u
    i32.const 1
    i32.and
    i32.const 12
    i32.shl
    i32.or
    i32.const 52
    i32.load
    i32.const 14
    i32.shr_u
    i32.const 1
    i32.and
    i32.const 13
    i32.shl
    i32.or
    i32.const 56
    i32.load
    i32.const 15
    i32.shr_u
    i32.const 1
    i32.and
    i32.const 14
    i32.shl
    i32.or
    i32.const 60
    i32.load
    i32.const 16
    i32.shr_u
    i32.const 1
    i32.and
    i32.const 15
    i32.shl
    i32.or
    i32.const 64
    i32.load
    i32.const 17
    i32.shr_u
    i32.const 1
    i32.and
    i32.const 16
    i32.shl
    i32.or
    i32.const 68
    i32.load
    i32.const 18
    i32.shr_u
    i32.const 1
    i32.and
    i32.const 17
    i32.shl
    i32.or
    i32.const 72
    i32.load
    i32.const 19
    i32.shr_u
    i32.const 1
    i32.and
    i32.const 18
    i32.shl
    i32.or
    i32.const 76
    i32.load
    i32.const 20
    i32.shr_u
    i32.const 1
    i32.and
    i32.const 19
    i32.shl
    i32.or
    i32.const 80
    i32.load
    i32.const 21
    i32.shr_u
    i32.const 1
    i32.and
    i32.const 20
    i32.shl
    i32.or
    i32.const 84
    i32.load
    i32.const 22
    i32.shr_u
    i32.const 1
    i32.and
    i32.const 21
    i32.shl
    i32.or
    i32.const 88
    i32.load
    i32.const 23
    i32.shr_u
    i32.const 1
    i32.and
    i32.const 22
    i32.shl
    i32.or
    i32.const 92
    i32.load
    i32.const 24
    i32.shr_u
    i32.const 1
    i32.and
    i32.const 23
    i32.shl
    i32.or
    i32.const 96
    i32.load
    i32.const 25
    i32.shr_u
    i32.const 1
    i32.and
    i32.const 24
    i32.shl
    i32.or
    i32.const 100
    i32.load
    i32.const 26
    i32.shr_u
    i32.const 1
    i32.and
    i32.const 25
    i32.shl
    i32.or
    i32.const 104
    i32.load
    i32.const 27
    i32.shr_u
    i32.const 1
    i32.and
    i32.const 26
    i32.shl
    i32.or
    i32.const 108
    i32.load
    i32.const 28
    i32.shr_u
    i32.const 1
    i32.and
    i32.const 27
    i32.shl
    i32.or
    i32.const 112
    i32.load
    i32.const 29
    i32.shr_u
    i32.const 1
    i32.and
    i32.const 28
    i32.shl
    i32.or
    i32.const 116
    i32.load
    i32.const 30
    i32.shr_u
    i32.const 1
    i32.and
    i32.const 29
    i32.shl
    i32.or
    i32.const 120
    i32.load
    i32.const 31
    i32.shr_u
    i32.const 30
    i32.shl
    i32.or)
  (memory (;0;) 1)
  (export "memory" (memory 0))
  (export "encode" (func 0))
  (export "recover" (func 1)))
