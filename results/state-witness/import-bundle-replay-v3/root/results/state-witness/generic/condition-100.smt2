; benchmark generated from python API
(set-info :status unknown)
(declare-fun right_0 () Int)
(declare-fun left_0 () Int)
(assert
 (and (and (>= left_0 0) (<= left_0 255)) (and (>= right_0 0) (<= right_0 255))))
(assert
 (let (($x164 (= left_0 65)))
(let (($x26 (and (= 65 (select (store ((as const (Array Int Int)) 0) 0 left_0) 0)))))
(and (distinct $x26 $x164) true))))
(check-sat)
