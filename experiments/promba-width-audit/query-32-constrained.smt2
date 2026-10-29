(set-logic QF_BV)
(declare-const x (_ BitVec 32))
(assert (not (= (bvadd (bvmul (bvmul (bvmul (bvmul (bvmul (bvmul (bvmul (bvmul (bvmul (bvsub (bvand x (_ bv1 32)) (_ bv0 32)) (bvsub (bvand x (_ bv1 32)) (_ bv1 32))) (bvsub (bvand x (_ bv1 32)) (_ bv2 32))) (bvsub (bvand x (_ bv1 32)) (_ bv3 32))) (bvsub (bvand x (_ bv1 32)) (_ bv4 32))) (bvsub (bvand x (_ bv1 32)) (_ bv5 32))) (bvsub (bvand x (_ bv1 32)) (_ bv6 32))) (bvsub (bvand x (_ bv1 32)) (_ bv7 32))) (bvsub (bvand x (_ bv1 32)) (_ bv8 32))) (bvsub (bvand x (_ bv1 32)) (_ bv9 32))) (bvand x (_ bv1 32))) (bvand x (_ bv1 32)))))
(check-sat)
