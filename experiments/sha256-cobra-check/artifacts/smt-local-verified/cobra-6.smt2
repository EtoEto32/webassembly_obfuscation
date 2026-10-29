(set-logic QF_BV)
(declare-fun v0 () (_ BitVec 32))
(assert (not (= (bvadd #x00000000 (bvshl v0 (bvand #x00000002 #x0000001f))) (bvmul #x00000004 v0))))
(check-sat)
