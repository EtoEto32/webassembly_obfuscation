(module (memory (export "memory") 1 1)  
  (func (export "run") (param $a i32)(param $b i32)(param $d i32)(param $x i32)(param $y i32)(param $e i32) (result i32)
  (local $fault i32)(local $faultArg i32)(local $q i32)(local $v i32)(local $q2 i32)(local $o i32)
  
(local.set $q (i32.div_u (local.get $x) (local.get $d)))

(i32.store (local.get $a) (local.get $q))

(local.set $v (i32.load (local.get $b)))

(local.set $q2 (i32.div_u (local.get $v) (local.get $e)))

(i32.store (local.get $b) (local.get $q2))

(local.set $o (i32.load (local.get $a))) (local.get $o)))