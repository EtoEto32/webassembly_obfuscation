(set-logic QF_BV)
(declare-fun v0 () (_ BitVec 32))
(assert (not (= (bvadd #x00000400 v0) (bvadd v0 #x00000400))))
(check-sat)
