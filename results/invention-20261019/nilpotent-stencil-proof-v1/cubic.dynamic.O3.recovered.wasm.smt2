; benchmark generated from python API
(set-info :status unknown)
(declare-fun y () (_ BitVec 32))
(declare-fun x () (_ BitVec 32))
(assert
 (let ((?x10 (bvmul (_ bv5 32) y)))
(let ((?x7 (bvmul x x)))
(let ((?x8 (bvmul ?x7 x)))
(let ((?x11 (bvadd ?x8 ?x10)))
(and (distinct ?x11 ?x11) true))))))
(check-sat)
