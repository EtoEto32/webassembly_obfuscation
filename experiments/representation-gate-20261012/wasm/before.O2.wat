(module
  (type (;0;) (func (param i32)))
  (type (;1;) (func (result i32)))
  (func (;0;) (type 0) (param i32)
    i32.const 0
    local.get 0
    i32.store)
  (func (;1;) (type 1) (result i32)
    i32.const 0
    i32.load)
  (memory (;0;) 1)
  (export "memory" (memory 0))
  (export "encode" (func 0))
  (export "recover" (func 1)))
