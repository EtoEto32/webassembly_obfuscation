(declare-rel Bad ())
(declare-rel State (Bool Bool Bool Bool Int Int Int Int Int Int Int Int))
(declare-var A Int)
(declare-var B Int)
(declare-var C Int)
(declare-var D Int)
(declare-var E Int)
(declare-var F Int)
(declare-var G Int)
(declare-var H Int)
(declare-var I Bool)
(declare-var J Bool)
(declare-var K Bool)
(declare-var L Bool)
(declare-var M Int)
(declare-var N Int)
(declare-var O Int)
(declare-var P Int)
(declare-var Q Int)
(declare-var R Int)
(declare-var S Int)
(declare-var T Int)
(declare-var U Int)
(declare-var V Int)
(declare-var W Bool)
(declare-var X Bool)
(declare-var Y Bool)
(declare-var Z Bool)
(rule (State false false true false 256 258 256 256 256 258 256 256))
(rule (! (=> (and (State L K J I H G F E D C B A) (not true)) Bad) :named observe_0))
(rule (! (let ((a!1 (State L K J I H G F E D C B A)))
  (=> (and a!1 true true) a!1)) :named step_0))
(rule (! (=> (and (State L K J I H G F E D C B A) (not true)) Bad) :named observe_1))
(rule (! (let ((a!1 (State L K J I H G F E D C B A)))
  (=> (and a!1 true true) a!1)) :named step_1))
(rule (! (let ((a!1 (and (State L K J I H G F E D C B A) (not (= (and L K) (and J I))))))
  (=> a!1 Bad)) :named observe_2))
(rule (! (let ((a!1 (store (store (store ((as const (Array Int Int)) 0) 4294967297 H)
                         4294967298
                         G)
                  8589934593
                  E))
      (a!2 (store (store (store ((as const (Array Int Int)) 0) 4294967297 H)
                         4294967298
                         G)
                  8589934592
                  F))
      (a!8 (store (store (store ((as const (Array Int Int)) 0) 4294967297 D)
                         4294967298
                         C)
                  8589934593
                  A))
      (a!9 (store (store (store ((as const (Array Int Int)) 0) 4294967297 D)
                         4294967298
                         C)
                  8589934592
                  B)))
(let ((a!3 (ite L (store a!1 8589934592 257) (store a!2 8589934593 E)))
      (a!10 (ite J (store a!8 8589934592 257) (store a!9 8589934593 A))))
(let ((a!4 (store (store (ite (and L K) (store a!3 8589934593 258) a!3)
                         4294967297
                         258)
                  4294967298
                  258))
      (a!11 (store (store (ite (and J I) (store a!10 8589934593 258) a!10)
                          4294967297
                          258)
                   4294967298
                   258)))
(let ((a!5 (ite (and L K)
                (select (ite (and L K) a!4 a!3) 4294967298)
                (select a!3 4294967298)))
      (a!6 (ite (and L K)
                (select (ite (and L K) a!4 a!3) 8589934592)
                (select a!3 8589934592)))
      (a!7 (ite (and L K)
                (select (ite (and L K) a!4 a!3) 8589934593)
                (select a!3 8589934593)))
      (a!12 (ite (and J I)
                 (select (ite (and J I) a!11 a!10) 4294967298)
                 (select a!10 4294967298)))
      (a!13 (ite (and J I)
                 (select (ite (and J I) a!11 a!10) 8589934592)
                 (select a!10 8589934592)))
      (a!14 (ite (and J I)
                 (select (ite (and J I) a!11 a!10) 8589934593)
                 (select a!10 8589934593))))
  (=> (and (State L K J I H G F E D C B A)
           (= (and L K) (and J I))
           (or (and L K) (and J I)))
      (State false
             K
             false
             I
             (ite (and L K) 258 (select a!3 4294967297))
             a!5
             a!6
             a!7
             (ite (and J I) 258 (select a!10 4294967297))
             a!12
             a!13
             a!14)))))) :named step_2))
(rule (! (=> (and (State L K J I H G F E D C B A) (not true)) Bad) :named observe_3))
(rule (! (let ((a!1 (State L K J I H G F E D C B A)))
  (=> (and a!1 true false) a!1)) :named step_3))
(rule (! (=> (and (State L K J I H G F E D C B A) (not true)) Bad) :named observe_4))
(rule (! (let ((a!1 (State L K J I H G F E D C B A)))
  (=> (and a!1 true false) a!1)) :named step_4))
(rule (! (=> (and (State L K J I N M H G F E D C) (>= B 256) (>= A 256))
    (State L K J I B A H G B A D C)) :named common_public_assignment))

(query Bad)
