(set-logic QF_BV)
(declare-const x (_ BitVec 32))
(assert (not (= (bvadd (bvmul (bvmul (bvmul (bvmul (bvmul (bvmul (bvmul (bvmul (bvmul (bvsub x (_ bv0 32)) (bvsub x (_ bv1 32))) (bvsub x (_ bv2 32))) (bvsub x (_ bv3 32))) (bvsub x (_ bv4 32))) (bvsub x (_ bv5 32))) (bvsub x (_ bv6 32))) (bvsub x (_ bv7 32))) (bvsub x (_ bv8 32))) (bvsub x (_ bv9 32))) x) x)))
(check-sat)
