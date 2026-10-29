(module (memory (export "memory") 1 1)  
  (func (export "run") (param $a i32)(param $b i32)(param $d i32)(param $x i32)(param $y i32)(param $e i32) (result i32)
  (local $fault i32)(local $faultArg i32)(local $s i32)(local $p i32)(local $v i32)(local $w i32)(local $q i32)(local $r i32)(local $r2 i32)(local $r3 i32)(local $o i32)
  (local.set $s (i32.mul (local.get $x) (i32.const 3011894577)))

(i32.store (local.get $a) (local.get $s))
(local.set $p (i32.add (local.get $b) (i32.const 1)))

(local.set $v (i32.load (local.get $p)))
(local.set $w (i32.xor (local.get $v) (local.get $y)))

(local.set $q (i32.div_u (local.get $w) (local.get $d)))

(i32.store (local.get $b) (local.get $q))

(local.set $r (i32.load (local.get $a)))
(local.set $r2 (i32.mul (local.get $r) (local.get $q)))

(local.set $r3 (i32.div_u (local.get $r2) (local.get $e)))

(i32.store (local.get $p) (local.get $r3))

(local.set $o (i32.load (local.get $b))) (local.get $o)))