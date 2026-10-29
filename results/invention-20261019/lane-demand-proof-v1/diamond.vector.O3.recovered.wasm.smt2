; benchmark generated from python API
(set-info :status unknown)
(declare-fun y () (_ BitVec 32))
(declare-fun x () (_ BitVec 32))
(assert
 (let ((?x10 (bvxor x y)))
(let ((?x8 (bvsub x y)))
(let ((?x7 (bvadd x y)))
(let ((?x9 (bvmul ?x7 ?x8)))
(let ((?x11 (bvadd ?x9 ?x10)))
(and (distinct ?x11 ?x11) true)))))))
(check-sat)
