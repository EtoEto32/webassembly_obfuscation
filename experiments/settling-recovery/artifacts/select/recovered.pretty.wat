(module
  (type (;0;) (func (param i32 i32 i32) (result i32)))
  (func (;0;) (type 0) (param i32 i32 i32) (result i32)
    (local i32 i32 i32 i32 i32 i32 i32 i32 i32 i32 i32 i32 i32 i32 i32)
    (local.set 6
      (i32.add
        (local.get 0)
        (local.get 1)))
    (local.set 8
      (i32.rotl
        (local.get 0)
        (i32.const 3)))
    (local.set 10
      (i32.mul
        (local.get 6)
        (local.get 8)))
    (local.set 12
      (i32.add
        (local.get 10)
        (local.get 1)))
    (local.set 14
      (i32.lt_u
        (local.get 10)
        (local.get 12)))
    (local.set 16
      (select
        (local.get 6)
        (local.get 12)
        (local.get 14)))
    (local.get 16))
  (export "run" (func 0)))
