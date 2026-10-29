; benchmark generated from python API
(set-info :status unknown)
(declare-fun right_4294967296 () Int)
(declare-fun left_4294967296 () Int)
(assert
 (let (($x28 (>= right_4294967296 256)))
 (let (($x67 (>= left_4294967296 256)))
 (and $x67 $x28))))
(assert
 (and (distinct true and) true))
(check-sat)
