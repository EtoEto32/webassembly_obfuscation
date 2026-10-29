; benchmark generated from python API
(set-info :status unknown)
(declare-fun y () (_ BitVec 32))
(declare-fun x () (_ BitVec 32))
(assert
 (let ((?x31 (bvmul y y)))
(let ((?x17 (bvmul x y)))
(let ((?x18 (bvadd x y)))
(let ((?x19 (bvmul ?x18 ?x17)))
(let ((?x34 (bvsub ?x19 ?x31)))
(and (distinct ?x34 ?x34) true)))))))
(check-sat)
