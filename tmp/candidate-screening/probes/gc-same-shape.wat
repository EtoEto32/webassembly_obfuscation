(module
  (type $a (struct (field i32)))
  (type $b (struct (field i32)))
  (func (export "run") (result i32)
    (ref.test (ref $b) (struct.new $a (i32.const 7)))))
