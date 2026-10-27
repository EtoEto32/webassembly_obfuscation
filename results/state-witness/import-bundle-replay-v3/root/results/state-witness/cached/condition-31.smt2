; benchmark generated from python API
(set-info :status unknown)
(declare-fun right_0 () Int)
(declare-fun left_0 () Int)
(assert
 (and (and (>= left_0 0) (<= left_0 255)) (and (>= right_0 0) (<= right_0 255))))
(assert
 (and (distinct false false) true))
(check-sat)
