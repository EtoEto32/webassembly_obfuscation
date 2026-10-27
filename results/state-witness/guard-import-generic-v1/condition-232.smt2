; benchmark generated from python API
(set-info :status unknown)
(declare-fun right_4294967296 () Int)
(declare-fun left_4294967296 () Int)
(assert
 (let (($x29 (>= right_4294967296 256)))
 (let (($x186 (>= left_4294967296 256)))
 (and $x186 $x29))))
(assert
 (let (($x192 (= left_4294967296 258)))
(let (($x151 (and (= 258 (select (store ((as const (Array Int Int)) 0) 4294967296 left_4294967296) 4294967296)))))
(and (distinct $x151 $x192) true))))
(check-sat)
