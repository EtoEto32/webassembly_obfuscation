; benchmark generated from python API
(set-info :status unknown)
(declare-fun right_4294967296 () Int)
(declare-fun left_4294967296 () Int)
(assert
 (let (($x120 (>= right_4294967296 256)))
 (let (($x156 (>= left_4294967296 256)))
 (and $x156 $x120))))
(assert
 (let (($x19 (and (= 258 (select (store ((as const (Array Int Int)) 0) 4294967296 left_4294967296) 4294967296)))))
(let (($x11 (= left_4294967296 258)))
(and (distinct $x11 $x19) true))))
(check-sat)
