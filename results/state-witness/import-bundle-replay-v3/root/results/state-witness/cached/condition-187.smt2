; benchmark generated from python API
(set-info :status unknown)
(declare-fun right_4294967296 () Int)
(declare-fun left_4294967296 () Int)
(assert
 (let (($x120 (>= right_4294967296 256)))
 (let (($x156 (>= left_4294967296 256)))
 (and $x156 $x120))))
(assert
 (and (distinct true and) true))
(check-sat)
