(set-logic QF_BV)
(declare-fun v0 () (_ BitVec 32))
(assert (not (= (bvshl v0 (bvand #x00000020 #x0000001f)) (bvshl v0 #x00000020))))
(check-sat)
