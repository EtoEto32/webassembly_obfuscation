; benchmark generated from python API
(set-info :status unknown)
(declare-fun right_4294967296 () Int)
(declare-fun left_4294967296 () Int)
(assert
 (let (($x29 (>= right_4294967296 256)))
 (let (($x186 (>= left_4294967296 256)))
 (and $x186 $x29))))
(assert
 (and (distinct false false) true))
(check-sat)
