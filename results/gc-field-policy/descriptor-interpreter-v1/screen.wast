(module (rec
  (type $T (descriptor $D) (struct (field i32)))
  (type $D (describes $T) (struct)))
 (global $a (ref (exact $D)) (struct.new $D))
 (global $b (ref (exact $D)) (struct.new $D))
 (func (export "get-a") (result anyref) (struct.new_desc $T (i32.const 17) (global.get $a)))
 (func (export "get-b") (result anyref) (struct.new_desc $T (i32.const 29) (global.get $b)))
 (func (export "accept-a") (param $x anyref) (result i32)
  (struct.get $T 0 (ref.cast_desc_eq (ref $T) (local.get $x) (global.get $a)))))
(register "lib")
;; original
(module (rec
  (type $T (descriptor $D) (struct (field i32)))
  (type $D (describes $T) (struct))) (import "lib" "get-a" (func $get-a (result anyref)))
 (import "lib" "get-b" (func $get-b (result anyref)))
 (import "lib" "accept-a" (func $accept-a (param anyref) (result i32))) (func (export "run") (result i32) (call $accept-a (call $get-a))))
(assert_return (invoke "run") (i32.const 17))
;; different-brand
(module (rec
  (type $T (descriptor $D) (struct (field i32)))
  (type $D (describes $T) (struct))) (import "lib" "get-a" (func $get-a (result anyref)))
 (import "lib" "get-b" (func $get-b (result anyref)))
 (import "lib" "accept-a" (func $accept-a (param anyref) (result i32))) (func (export "run") (result i32) (call $accept-a (call $get-b))))
(assert_trap (invoke "run") "cast failure")
;; fresh-descriptor
(module (rec
  (type $T (descriptor $D) (struct (field i32)))
  (type $D (describes $T) (struct))) (import "lib" "get-a" (func $get-a (result anyref)))
 (import "lib" "get-b" (func $get-b (result anyref)))
 (import "lib" "accept-a" (func $accept-a (param anyref) (result i32))) (func (export "run") (result i32) (call $accept-a (struct.new_desc $T (i32.const 77) (struct.new $D)))))
(assert_trap (invoke "run") "cast failure")
;; copied-descriptor
(module (rec
  (type $T (descriptor $D) (struct (field i32)))
  (type $D (describes $T) (struct))) (import "lib" "get-a" (func $get-a (result anyref)))
 (import "lib" "get-b" (func $get-b (result anyref)))
 (import "lib" "accept-a" (func $accept-a (param anyref) (result i32))) (func (export "run") (result i32) (call $accept-a (struct.new_desc $T (i32.const 77) (ref.get_desc $T (ref.cast (ref (exact $T)) (call $get-a)))))))
(assert_return (invoke "run") (i32.const 77))