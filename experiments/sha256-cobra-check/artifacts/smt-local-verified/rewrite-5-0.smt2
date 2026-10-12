(set-logic QF_BV)
(declare-fun local_9 () (_ BitVec 32))
(assert (not (= (bvadd #x00000000 (bvshl local_9 (bvand #x00000002 #x0000001f))) (bvmul #x00000004 local_9))))
(check-sat)
