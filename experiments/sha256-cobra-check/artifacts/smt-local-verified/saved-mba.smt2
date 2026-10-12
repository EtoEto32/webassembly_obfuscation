; Local 32-bit identity only. No whole-program proof. Not executed in this run.
(set-logic QF_BV)
(set-option :timeout 5000)
(declare-fun x () (_ BitVec 32))
(declare-fun y () (_ BitVec 32))
(assert (not (= (bvadd x y)
  (bvadd (bvxor x y) (bvshl (bvand x y) (_ bv1 32))))))
(check-sat)
