(set-logic QF_BV)
(declare-const x (_ BitVec 8))
(assert (not (= (bvadd (bvmul (bvmul (bvmul (bvmul (bvmul (bvmul (bvmul (bvmul (bvmul (bvsub x (_ bv0 8)) (bvsub x (_ bv1 8))) (bvsub x (_ bv2 8))) (bvsub x (_ bv3 8))) (bvsub x (_ bv4 8))) (bvsub x (_ bv5 8))) (bvsub x (_ bv6 8))) (bvsub x (_ bv7 8))) (bvsub x (_ bv8 8))) (bvsub x (_ bv9 8))) x) x)))
(check-sat)
