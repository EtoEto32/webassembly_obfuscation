(module
  (type (;0;) (func))
  (type (;1;) (func (result i32)))
  (type (;2;) (func))
  (import "host" "should_migrate" (func (;0;) (type 1)))
  (import "host" "restore_memory" (func (;1;) (type 2)))
  (func (;2;) (type 0)
    (local i32)
    (block  ;; label = @1
      (call 1)
      (local.set 0
        (i32.load 1
          (i32.const 0))))
    (block  ;; label = @1
      (block  ;; label = @2
        (br_if 0 (;@2;)
          (i32.eq
            (local.get 0)
            (i32.const 1)))
        (br_if 0 (;@2;)
          (i32.eq
            (local.get 0)
            (i32.const 0)))
        (br 1 (;@1;)))
      (data.drop 0)
      (block  ;; label = @2
        (i32.store 1
          (i32.const 0)
          (i32.const 1)))
      (block  ;; label = @2
        (br_if 0 (;@2;)
          (i32.eq
            (call 0)
            (i32.const 0)))
        (unreachable)))
    (block  ;; label = @1
      (br_if 0 (;@1;)
        (i32.eq
          (local.get 0)
          (i32.const 0))))
    (loop  ;; label = @1
      (br_if 0 (;@1;)
        (i32.const 0))))
  (func (;3;) (type 0)
    (memory.init 0
      (i32.const 7)
      (i32.const 0)
      (i32.const 1))
    (memory.init 1
      (i32.const 0)
      (i32.const 2)
      (i32.const 1)))
  (memory (;0;) 1 1)
  (memory (;1;) 1)
  (memory (;2;) 2)
  (export "memory" (memory 0))
  (export "retire" (func 2))
  (export "mask" (func 3))
  (export "checkpoint_memory" (memory 1))
  (data (;0;) "\11")
  (data (;1;) "B")
  (data (;2;) (i32.const 7) "\11"))
