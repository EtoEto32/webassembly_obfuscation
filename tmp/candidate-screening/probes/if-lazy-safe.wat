(module
  (func (export "run") (result i32)
    (if (result i32) (i32.const 0)
      (then (i32.div_u (i32.const 1) (i32.const 0)))
      (else (i32.const 7)))))
