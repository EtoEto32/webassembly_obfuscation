(module
  (type (;0;) (func (param i32 i32 i32) (result i32)))
  (func (;0;) (type 0) (param i32 i32 i32) (result i32)
    (local i32 i32 i32 i32 i32 i32 i32 i32 i32 i32 i32 i32 i32)
    (local.set 6
      (i32.xor
        (local.get 2)
        (i32.const 7)))
    (local.set 7
      (i32.xor
        (local.get 2)
        (i32.const 11)))
    (local.set 8
      (i32.xor
        (local.get 2)
        (i32.const 20)))
    (local.set 9
      (i32.xor
        (local.get 2)
        (i32.const 30)))
    (local.set 10
      (i32.xor
        (local.get 2)
        (i32.const 33)))
    (local.set 11
      (i32.xor
        (local.get 2)
        (i32.const 49)))
    (local.set 12
      (i32.xor
        (local.get 2)
        (i32.const 46)))
    (local.set 13
      (i32.xor
        (local.get 2)
        (i32.const 68)))
    (local.set 14
      (i32.xor
        (local.get 2)
        (i32.const 59)))
    (local.set 15
      (i32.xor
        (local.get 2)
        (i32.const 87)))
    (loop  ;; label = @1
      (local.set 5
        (i32.rem_u
          (i32.xor
            (local.get 2)
            (local.get 6))
          (i32.const 5)))
      (local.set 4
        (i32.const 0))
      (loop  ;; label = @2
        (if  ;; label = @3
          (i32.eq
            (local.get 5)
            (i32.const 0))
          (then
            (local.set 6
              (i32.xor
                (i32.xor
                  (local.get 0)
                  (local.get 1))
                (local.get 7)))
            (local.set 7
              (i32.shl
                (i32.or
                  (i32.and
                    (local.get 0)
                    (local.get 1))
                  (i32.and
                    (i32.xor
                      (local.get 0)
                      (local.get 1))
                    (local.get 7)))
                (i32.const 2)))))
        (if  ;; label = @3
          (i32.eq
            (local.get 5)
            (i32.const 1))
          (then
            (local.set 8
              (i32.mul
                (local.get 6)
                (local.get 0)))))
        (if  ;; label = @3
          (i32.eq
            (local.get 5)
            (i32.const 2))
          (then
            (local.set 10
              (i32.xor
                (i32.xor
                  (local.get 8)
                  (local.get 1))
                (local.get 11)))
            (local.set 11
              (i32.shl
                (i32.or
                  (i32.and
                    (local.get 8)
                    (local.get 1))
                  (i32.and
                    (i32.xor
                      (local.get 8)
                      (local.get 1))
                    (local.get 11)))
                (i32.const 1)))))
        (if  ;; label = @3
          (i32.eq
            (local.get 5)
            (i32.const 3))
          (then
            (local.set 12
              (i32.rotl
                (local.get 0)
                (i32.const 7)))))
        (if  ;; label = @3
          (i32.eq
            (local.get 5)
            (i32.const 4))
          (then
            (local.set 14
              (i32.xor
                (local.get 10)
                (local.get 12)))))
        (local.set 5
          (i32.rem_u
            (i32.add
              (local.get 5)
              (i32.const 1))
            (i32.const 5)))
        (local.set 4
          (i32.add
            (local.get 4)
            (i32.const 1)))
        (br_if 0 (;@2;)
          (i32.lt_u
            (local.get 4)
            (i32.const 5))))
      (local.set 3
        (i32.add
          (local.get 3)
          (i32.const 1)))
      (br_if 0 (;@1;)
        (i32.lt_u
          (local.get 3)
          (i32.const 68))))
    (local.get 14))
  (export "run" (func 0)))
