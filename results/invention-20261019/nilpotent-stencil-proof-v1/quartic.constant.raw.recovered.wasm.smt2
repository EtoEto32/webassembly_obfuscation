; benchmark generated from python API
(set-info :status unknown)
(declare-fun y () (_ BitVec 32))
(declare-fun x () (_ BitVec 32))
(assert
 (let ((?x7 (bvmul x x)))
(let ((?x32 (bvmul ?x7 ?x7)))
(let ((?x33 (bvadd ?x32 y)))
(and (distinct ?x33 ?x33) true)))))
(check-sat)
