(set-logic QF_BV)
(declare-fun v0 () (_ BitVec 32))
(assert (not (= (bvadd v0 #x00000400) (bvadd v0 #x00000400))))
(check-sat)
