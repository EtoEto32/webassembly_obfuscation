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
(declare-var E1 Bool)
(declare-var F1 Bool)
(declare-var G1 Bool)
(declare-var H1 Bool)
(rule (State false false true false 258 258 257 258 258 256 258 258 257 258 258 256))
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
(rule (! (let ((a!1 (store (store (store ((as const (Array Int Int)) 0) 4294967298 L)
                         4294967299
                         K)
                  8589934593
                  I))
      (a!2 (store (store (store ((as const (Array Int Int)) 0) 4294967298 L)
                         4294967299
                         K)
                  8589934592
                  J))
      (a!4 (store (store (store ((as const (Array Int Int)) 0) 4294967298 F)
                         4294967299
                         E)
                  8589934593
                  C))
      (a!5 (store (store (store ((as const (Array Int Int)) 0) 4294967298 F)
                         4294967299
                         E)
                  8589934592
                  D)))
(let ((a!3 (ite P
                (store (store (store a!1 8589934594 H) 8589934595 G)
                       8589934592
                       257)
                (store (store (store a!2 8589934593 I) 8589934594 H)
                       8589934595
                       G)))
      (a!6 (ite N
                (store (store (store a!4 8589934594 B) 8589934595 A)
                       8589934592
                       257)
                (store (store (store a!5 8589934593 C) 8589934594 B)
                       8589934595
                       A))))
(let ((a!7 (= (select (ite (and P O) (store a!3 8589934593 258) a!3) 4294967298)
              (select (ite (and N M) (store a!6 8589934593 258) a!6) 4294967298)))
      (a!8 (= (select (ite (and P O) (store a!3 8589934593 258) a!3) 4294967299)
              (select (ite (and N M) (store a!6 8589934593 258) a!6) 4294967299)))
      (a!9 (= (select (ite (and P O) (store a!3 8589934593 258) a!3) 8589934592)
              (select (ite (and N M) (store a!6 8589934593 258) a!6) 8589934592)))
      (a!10 (= (select (ite (and P O) (store a!3 8589934593 258) a!3)
                       8589934593)
               (select (ite (and N M) (store a!6 8589934593 258) a!6)
                       8589934593)))
      (a!11 (= (select (ite (and P O) (store a!3 8589934593 258) a!3)
                       8589934594)
               (select (ite (and N M) (store a!6 8589934593 258) a!6)
                       8589934594)))
      (a!12 (= (select (ite (and P O) (store a!3 8589934593 258) a!3)
                       8589934595)
               (select (ite (and N M) (store a!6 8589934593 258) a!6)
                       8589934595))))
  (=> (and (State P O N M L K J I H G F E D C B A)
           (not (and a!7 a!8 a!9 a!10 a!11 a!12)))
      Bad)))) :named observe_2))
(rule (! (let ((a!1 (store (store (store ((as const (Array Int Int)) 0) 4294967298 L)
                         4294967299
                         K)
                  8589934593
                  I))
      (a!2 (store (store (store ((as const (Array Int Int)) 0) 4294967298 L)
                         4294967299
                         K)
                  8589934592
                  J))
      (a!5 (store (store (store ((as const (Array Int Int)) 0) 4294967298 F)
                         4294967299
                         E)
                  8589934593
                  C))
      (a!6 (store (store (store ((as const (Array Int Int)) 0) 4294967298 F)
                         4294967299
                         E)
                  8589934592
                  D)))
(let ((a!3 (ite P
                (store (store (store a!1 8589934594 H) 8589934595 G)
                       8589934592
                       257)
                (store (store (store a!2 8589934593 I) 8589934594 H)
                       8589934595
                       G)))
      (a!7 (ite N
                (store (store (store a!5 8589934594 B) 8589934595 A)
                       8589934592
                       257)
                (store (store (store a!6 8589934593 C) 8589934594 B)
                       8589934595
                       A))))
(let ((a!4 (select (ite (and P O) (store a!3 8589934593 258) a!3) 4294967298))
      (a!8 (select (ite (and N M) (store a!7 8589934593 258) a!7) 4294967298))
      (a!9 (select (ite (and P O) (store a!3 8589934593 258) a!3) 4294967299))
      (a!10 (select (ite (and N M) (store a!7 8589934593 258) a!7) 4294967299))
      (a!11 (select (ite (and P O) (store a!3 8589934593 258) a!3) 8589934592))
      (a!12 (select (ite (and N M) (store a!7 8589934593 258) a!7) 8589934592))
      (a!13 (select (ite (and P O) (store a!3 8589934593 258) a!3) 8589934593))
      (a!14 (select (ite (and N M) (store a!7 8589934593 258) a!7) 8589934593))
      (a!15 (select (ite (and P O) (store a!3 8589934593 258) a!3) 8589934594))
      (a!16 (select (ite (and N M) (store a!7 8589934593 258) a!7) 8589934594))
      (a!17 (select (ite (and P O) (store a!3 8589934593 258) a!3) 8589934595))
      (a!18 (select (ite (and N M) (store a!7 8589934593 258) a!7) 8589934595)))
  (=> (and (State P O N M L K J I H G F E D C B A)
           (= a!4 a!8)
           (= a!9 a!10)
           (= a!11 a!12)
           (= a!13 a!14)
           (= a!15 a!16)
           (= a!17 a!18)
           false)
      (State false
             O
             false
             M
             a!4
             a!9
             a!11
             a!13
             a!15
             a!17
             a!8
             a!10
             a!12
             a!14
             a!16
             a!18))))) :named step_2))
(rule (! (let ((a!1 (and (State P O N M L K J I H G F E D C B A)
                (not (and (= L F) (= K E) (= J D) (= G A))))))
  (=> a!1 Bad)) :named observe_3))
(rule (! (=> (and (State P O N M L K J I H G F E D C B A)
         (= L F)
         (= K E)
         (= J D)
         (= G A)
         false)
    (State P false N false L K J 258 258 G F E D 258 258 A)) :named step_3))
(rule (! (let ((a!1 (and (State P O N M L K J I H G F E D C B A)
                (not (and (= L F) (= K E) (= J D) (= I C) (= H B) (= G A))))))
  (=> a!1 Bad)) :named observe_4))
(rule (! (let ((a!1 (State P O N M L K J I H G F E D C B A)))
  (=> (and a!1 (= L F) (= K E) (= J D) (= I C) (= H B) (= G A) false) a!1)) :named step_4))
(rule (! (=> (and (State P O N M R Q L K J I H G F E D C) (>= B 256) (>= A 256))
    (State P O N M B A L K J I B A F E D C)) :named common_public_assignment))

(query Bad)
