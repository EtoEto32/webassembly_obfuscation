(set-logic QF_BV)
(declare-fun v0 () (_ BitVec 32))
(assert (not (= (bvadd #x00000300 (bvshl v0 (bvand #x00000002 #x0000001f))) (bvadd (bvmul #x00000004 v0) #x00000300))))
(check-sat)
