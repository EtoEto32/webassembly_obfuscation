(set-logic QF_BV)
(declare-fun v0 () (_ BitVec 32))
(assert (not (= (bvadd v0 #x00000001) (bvneg (bvnot v0)))))
(check-sat)
