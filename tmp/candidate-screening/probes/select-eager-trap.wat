(module
  (func (export "run") (result i32)
    (select
      (i32.div_u (i32.const 1) (i32.const 0))
      (i32.const 7)
      (i32.const 0))))
