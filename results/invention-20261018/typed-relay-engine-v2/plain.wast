(module (func (export "run") (result i32) (i32.add (i32.const 7) (i32.const 11))))
(assert_return (invoke "run") (i32.const 18))
