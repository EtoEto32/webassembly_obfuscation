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
(rule (State false false true false 257 258 258 256 257 258 258 256))
(rule (! (let ((a!1 (and (State L K J I H G F E D C B A) (not (and (= H D) (= G C))))))
  (=> a!1 Bad)) :named observe_0))
(rule (! (let ((a!1 (State L K J I H G F E D C B A)))
  (=> (and a!1 (= H D) (= G C) true) a!1)) :named step_0))
(rule (! (let ((a!1 (and (State L K J I H G F E D C B A) (not (and (= H D) (= G C))))))
  (=> a!1 Bad)) :named observe_1))
(rule (! (let ((a!1 (State L K J I H G F E D C B A)))
  (=> (and a!1 (= H D) (= G C) true) a!1)) :named step_1))
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
      (a!4 (store (store (store ((as const (Array Int Int)) 0) 4294967297 D)
                         4294967298
                         C)
                  8589934593
                  A))
      (a!5 (store (store (store ((as const (Array Int Int)) 0) 4294967297 D)
                         4294967298
                         C)
                  8589934592
                  B)))
(let ((a!3 (ite L (store a!1 8589934592 257) (store a!2 8589934593 E)))
      (a!6 (ite J (store a!4 8589934592 257) (store a!5 8589934593 A))))
(let ((a!7 (store (store (ite (and L K) (store a!3 8589934593 258) a!3)
                         4294967297
                         258)
                  4294967298
                  258))
      (a!9 (store (store (ite (and J I) (store a!6 8589934593 258) a!6)
                         4294967297
                         258)
                  4294967298
                  258)))
(let ((a!8 (ite (and L K)
                (store (ite (and L K) a!7 a!3)
                       4294967297
                       (ite (and L K) 258 (select a!3 8589934593)))
                a!3))
      (a!10 (ite (and J I)
                 (store (ite (and J I) a!9 a!6)
                        4294967297
                        (ite (and J I) 258 (select a!6 8589934593)))
                 a!6)))
(let ((a!11 (and (= (and L K) (and J I))
                 (= (ite (and L K) 258 (select a!3 4294967297))
                    (ite (and J I) 258 (select a!6 4294967297)))
                 (= (select a!8 4294967298) (select a!10 4294967298)))))
  (=> (and (State L K J I H G F E D C B A) (not a!11)) Bad)))))) :named observe_2))
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
      (a!4 (store (store (store ((as const (Array Int Int)) 0) 4294967297 D)
                         4294967298
                         C)
                  8589934593
                  A))
      (a!5 (store (store (store ((as const (Array Int Int)) 0) 4294967297 D)
                         4294967298
                         C)
                  8589934592
                  B)))
(let ((a!3 (ite L (store a!1 8589934592 257) (store a!2 8589934593 E)))
      (a!6 (ite J (store a!4 8589934592 257) (store a!5 8589934593 A))))
(let ((a!7 (store (store (ite (and L K) (store a!3 8589934593 258) a!3)
                         4294967297
                         258)
                  4294967298
                  258))
      (a!9 (store (store (ite (and J I) (store a!6 8589934593 258) a!6)
                         4294967297
                         258)
                  4294967298
                  258)))
(let ((a!8 (ite (and L K)
                (store (ite (and L K) a!7 a!3)
                       4294967297
                       (ite (and L K) 258 (select a!3 8589934593)))
                a!3))
      (a!10 (ite (and J I)
                 (store (ite (and J I) a!9 a!6)
                        4294967297
                        (ite (and J I) 258 (select a!6 8589934593)))
                 a!6))
      (a!12 (ite (and L K)
                 (select (ite (and L K) a!7 a!3) 4294967298)
                 (select a!3 4294967298)))
      (a!13 (ite (and L K)
                 (select (ite (and L K) a!7 a!3) 8589934592)
                 (select a!3 8589934592)))
      (a!14 (ite (and L K)
                 (select (ite (and L K) a!7 a!3) 8589934593)
                 (select a!3 8589934593)))
      (a!15 (ite (and J I)
                 (select (ite (and J I) a!9 a!6) 4294967298)
                 (select a!6 4294967298)))
      (a!16 (ite (and J I)
                 (select (ite (and J I) a!9 a!6) 8589934592)
                 (select a!6 8589934592)))
      (a!17 (ite (and J I)
                 (select (ite (and J I) a!9 a!6) 8589934593)
                 (select a!6 8589934593))))
(let ((a!11 (and (State L K J I H G F E D C B A)
                 (= (and L K) (and J I))
                 (= (ite (and L K) 258 (select a!3 4294967297))
                    (ite (and J I) 258 (select a!6 4294967297)))
                 (= (select a!8 4294967298) (select a!10 4294967298))
                 true)))
  (=> a!11
      (State false
             K
             false
             I
             (ite (and L K) 258 (select a!3 4294967297))
             a!12
             a!13
             a!14
             (ite (and J I) 258 (select a!6 4294967297))
             a!15
             a!16
             a!17))))))) :named step_2))
(rule (! (let ((a!1 (and (State L K J I H G F E D C B A) (not (and (= H D) (= G C))))))
  (=> a!1 Bad)) :named observe_3))
(rule (! (let ((a!1 (State L K J I H G F E D C B A)))
  (=> (and a!1 (= H D) (= G C) true) a!1)) :named step_3))
(rule (! (let ((a!1 (and (State L K J I H G F E D C B A) (not (and (= H D) (= G C))))))
  (=> a!1 Bad)) :named observe_4))
(rule (! (let ((a!1 (State L K J I H G F E D C B A)))
  (=> (and a!1 (= H D) (= G C) true) a!1)) :named step_4))
(rule (! (=> (and (State L K J I N M H G F E D C) (>= B 256) (>= A 256))
    (State L K J I B A H G B A D C)) :named common_public_assignment))

(query Bad)
