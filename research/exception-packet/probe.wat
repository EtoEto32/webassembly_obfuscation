(module
 (tag $t) (tag $f)
 (func $capture (param $c i32) (result exnref)
  (block $caught (result exnref)
   (try_table (catch_all_ref $caught)
    (if (local.get $c) (then (throw $t)) (else (throw $f))))
   (unreachable)))
 (func $force (param $p exnref) (param $a i32) (param $b i32) (result i32)
  (block $false
   (block $true
    (try_table (catch $t $true) (catch $f $false)
     (throw_ref (local.get $p)))
    (unreachable))
   (return (local.get $a)))
  (local.get $b))
 (func (export "run") (param i32 i32 i32) (result i32)
  (call $force (call $capture (local.get 2)) (local.get 0) (local.get 1))))
