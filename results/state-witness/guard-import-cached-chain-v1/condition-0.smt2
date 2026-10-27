; benchmark generated from python API
(set-info :status unknown)
(declare-fun right_8589934592 () Int)
(declare-fun left_8589934592 () Int)
(declare-fun right_4294967296 () Int)
(declare-fun left_4294967296 () Int)
(assert
 (let (($x21 (>= right_8589934592 256)))
 (let (($x18 (>= left_8589934592 256)))
 (let (($x14 (>= right_4294967296 256)))
 (let (($x11 (>= left_4294967296 256)))
 (and $x11 $x14 $x18 $x21))))))
(assert
 (and (distinct true and) true))
(check-sat)
