(module (memory (export "memory") 1 1)  
  (func (export "run") (param $a i32)(param $b i32)(param $d i32)(param $x i32)(param $y i32)(param $e i32) (result i32)
  (local $fault i32)(local $faultArg i32)(local $p i32)(local $v i32)(local $q i32)(local $p2 i32)(local $o i32)
  
(i32.store (local.get $a) (local.get $x))

(i32.store (local.get $b) (local.get $y))
(local.set $p (i32.add (local.get $a) (i32.const 1)))

(local.set $v (i32.load (local.get $p)))

(local.set $q (i32.div_u (local.get $v) (local.get $d)))
(local.set $p2 (i32.add (local.get $a) (i32.const 2)))

(i32.store (local.get $p2) (local.get $q))

(local.set $o (i32.load (local.get $b))) (local.get $o)))