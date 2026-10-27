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
 (let ((?x17 (store (store ((as const (Array Int Int)) 0) 4294967296 left_4294967296) 8589934592 left_8589934592)))
(let (($x72 (= left_8589934592 258)))
(and (distinct $x72 (and (= 258 (select ?x17 8589934592)))) true))))
(check-sat)
