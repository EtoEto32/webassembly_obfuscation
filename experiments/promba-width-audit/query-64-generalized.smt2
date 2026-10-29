(set-logic QF_BV)
(declare-const x (_ BitVec 64))
(assert (not (= (bvadd (bvmul (bvmul (bvmul (bvmul (bvmul (bvmul (bvmul (bvmul (bvmul (bvsub x (_ bv0 64)) (bvsub x (_ bv1 64))) (bvsub x (_ bv2 64))) (bvsub x (_ bv3 64))) (bvsub x (_ bv4 64))) (bvsub x (_ bv5 64))) (bvsub x (_ bv6 64))) (bvsub x (_ bv7 64))) (bvsub x (_ bv8 64))) (bvsub x (_ bv9 64))) x) x)))
(check-sat)
