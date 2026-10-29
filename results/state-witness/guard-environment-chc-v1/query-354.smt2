(declare-rel State (Bool Bool Bool Bool Int Int Int Int Int Int Int Int Int Int Int Int))
(declare-rel Bad ())
(declare-var A Int)
(declare-var B Int)
(declare-var C Int)
(declare-var D Int)
(declare-var E Int)
(declare-var F Int)
(declare-var G Int)
(declare-var H Int)
(declare-var I Int)
(declare-var J Int)
(declare-var K Int)
(declare-var L Int)
(declare-var M Bool)
(declare-var N Bool)
(declare-var O Bool)
(declare-var P Bool)
(declare-var Q Int)
(declare-var R Int)
(declare-var S Int)
(declare-var T Int)
(declare-var U Int)
(declare-var V Int)
(declare-var W Int)
(declare-var X Int)
(declare-var Y Int)
(declare-var Z Int)
(declare-var A1 Int)
(declare-var B1 Int)
(declare-var C1 Int)
(declare-var D1 Int)
(declare-var E1 Int)
(declare-var F1 Bool)
(declare-var G1 Bool)
(declare-var H1 Bool)
(declare-var I1 Bool)
(rule (State false false true false 257 258 258 257 258 256 257 258 258 257 258 256))
(rule (! (let ((a!1 (and (State P O N M L K J I H G F E D C B A)
                (not (and (= L F) (= K E) (= J D) (= I C) (= H B) (= G A))))))
  (=> a!1 Bad)) :named observe_0))
(rule (! (let ((a!1 (State P O N M L K J I H G F E D C B A)))
  (=> (and a!1 (= L F) (= K E) (= J D) (= I C) (= H B) (= G A) true) a!1)) :named step_0))
(rule (! (let ((a!1 (and (State P O N M L K J I H G F E D C B A)
                (not (and (= L F) (= K E) (= J D) (= I C) (= H B) (= G A))))))
  (=> a!1 Bad)) :named observe_1))
(rule (! (let ((a!1 (State P O N M L K J I H G F E D C B A)))
  (=> (and a!1 (= L F) (= K E) (= J D) (= I C) (= H B) (= G A) true) a!1)) :named step_1))
(rule (! (let ((a!1 (store (store (store ((as const (Array Int Int)) 0) 4294967296 L)
                         4294967298
                         K)
                  4294967299
                  J))
      (a!3 (store (store (store ((as const (Array Int Int)) 0) 4294967296 F)
                         4294967298
                         E)
                  4294967299
                  D)))
(let ((a!2 (ite P
                (store (store (store a!1 8589934593 H) 8589934594 G)
                       8589934592
                       257)
                (store (store (store a!1 8589934592 I) 8589934593 H)
                       8589934594
                       G)))
      (a!4 (ite N
                (store (store (store a!3 8589934593 B) 8589934594 A)
                       8589934592
                       257)
                (store (store (store a!3 8589934592 C) 8589934593 B)
                       8589934594
                       A))))
(let ((a!5 (= (select (ite (and P O) (store a!2 8589934593 258) a!2) 4294967296)
              (select (ite (and N M) (store a!4 8589934593 258) a!4) 4294967296)))
      (a!6 (= (select (ite (and P O) (store a!2 8589934593 258) a!2) 4294967298)
              (select (ite (and N M) (store a!4 8589934593 258) a!4) 4294967298)))
      (a!7 (= (select (ite (and P O) (store a!2 8589934593 258) a!2) 4294967299)
              (select (ite (and N M) (store a!4 8589934593 258) a!4) 4294967299)))
      (a!8 (= (select (ite (and P O) (store a!2 8589934593 258) a!2) 8589934592)
              (select (ite (and N M) (store a!4 8589934593 258) a!4) 8589934592)))
      (a!9 (= (select (ite (and P O) (store a!2 8589934593 258) a!2) 8589934593)
              (select (ite (and N M) (store a!4 8589934593 258) a!4) 8589934593)))
      (a!10 (= (select (ite (and P O) (store a!2 8589934593 258) a!2)
                       8589934594)
               (select (ite (and N M) (store a!4 8589934593 258) a!4)
                       8589934594))))
  (=> (and (State P O N M L K J I H G F E D C B A)
           (not (and a!5 a!6 a!7 a!8 a!9 a!10)))
      Bad)))) :named observe_2))
(rule (! (let ((a!1 (store (store (store ((as const (Array Int Int)) 0) 4294967296 L)
                         4294967298
                         K)
                  4294967299
                  J))
      (a!4 (store (store (store ((as const (Array Int Int)) 0) 4294967296 F)
                         4294967298
                         E)
                  4294967299
                  D)))
(let ((a!2 (ite P
                (store (store (store a!1 8589934593 H) 8589934594 G)
                       8589934592
                       257)
                (store (store (store a!1 8589934592 I) 8589934593 H)
                       8589934594
                       G)))
      (a!5 (ite N
                (store (store (store a!4 8589934593 B) 8589934594 A)
                       8589934592
                       257)
                (store (store (store a!4 8589934592 C) 8589934593 B)
                       8589934594
                       A))))
(let ((a!3 (select (ite (and P O) (store a!2 8589934593 258) a!2) 4294967296))
      (a!6 (select (ite (and N M) (store a!5 8589934593 258) a!5) 4294967296))
      (a!7 (select (ite (and P O) (store a!2 8589934593 258) a!2) 4294967298))
      (a!8 (select (ite (and N M) (store a!5 8589934593 258) a!5) 4294967298))
      (a!9 (select (ite (and P O) (store a!2 8589934593 258) a!2) 4294967299))
      (a!10 (select (ite (and N M) (store a!5 8589934593 258) a!5) 4294967299))
      (a!11 (select (ite (and P O) (store a!2 8589934593 258) a!2) 8589934592))
      (a!12 (select (ite (and N M) (store a!5 8589934593 258) a!5) 8589934592))
      (a!13 (select (ite (and P O) (store a!2 8589934593 258) a!2) 8589934593))
      (a!14 (select (ite (and N M) (store a!5 8589934593 258) a!5) 8589934593))
      (a!15 (select (ite (and P O) (store a!2 8589934593 258) a!2) 8589934594))
      (a!16 (select (ite (and N M) (store a!5 8589934593 258) a!5) 8589934594)))
  (=> (and (State P O N M L K J I H G F E D C B A)
           (= a!3 a!6)
           (= a!7 a!8)
           (= a!9 a!10)
           (= a!11 a!12)
           (= a!13 a!14)
           (= a!15 a!16)
           true)
      (State false
             O
             false
             M
             a!3
             a!7
             a!9
             a!11
             a!13
             a!15
             a!6
             a!8
             a!10
             a!12
             a!14
             a!16))))) :named step_2))
(rule (! (let ((a!1 (and (State P O N M L K J I H G F E D C B A)
                (not (and (= L F) (= K E) (= J D) (= I C) (= H B) (= G A))))))
  (=> a!1 Bad)) :named observe_3))
(rule (! (=> (and (State P O N M L K J I H G F E D C B A)
         (= L F)
         (= K E)
         (= J D)
         (= I C)
         (= H B)
         (= G A)
         true)
    (State P false N false L K J I H G F E D C B A)) :named step_3))
(rule (! (let ((a!1 (and (State P O N M L K J I H G F E D C B A)
                (not (and (= L F) (= K E) (= J D) (= I C) (= H B) (= G A))))))
  (=> a!1 Bad)) :named observe_4))
(rule (! (let ((a!1 (State P O N M L K J I H G F E D C B A)))
  (=> (and a!1 (= L F) (= K E) (= J D) (= I C) (= H B) (= G A) true) a!1)) :named step_4))
(rule (! (=> (and (State P O N M S R Q L K J I H G F E D)
         (>= C 256)
         (>= B 256)
         (>= A 256))
    (State P O N M C B A L K J C B A F E D)) :named common_public_assignment))

(query Bad)
