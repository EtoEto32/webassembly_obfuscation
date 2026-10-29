(declare-rel Bad ())
(declare-rel State (Bool Bool Bool Bool Bool Bool Bool Bool Int Int Int Int Int Int Int Int Int Int Int Int))
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
(declare-var Q Bool)
(declare-var R Bool)
(declare-var S Bool)
(declare-var T Bool)
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
(declare-var F1 Int)
(declare-var G1 Int)
(declare-var H1 Int)
(declare-var I1 Int)
(declare-var J1 Bool)
(declare-var K1 Bool)
(declare-var L1 Bool)
(declare-var M1 Bool)
(declare-var N1 Bool)
(declare-var O1 Bool)
(declare-var P1 Bool)
(declare-var Q1 Bool)
(rule (State false
       true
       false
       false
       false
       true
       true
       false
       95
       0
       250
       257
       258
       256
       95
       0
       250
       257
       258
       256))
(rule (! (let ((a!1 (and (State T S R Q P O N M L K J I H G F E D C B A)
                (not (and (= L F) (= K E) (= J D) (= I C) (= H B) (= G A))))))
  (=> a!1 Bad)) :named observe_0))
(rule (! (let ((a!1 (State T S R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 (= L F) (= K E) (= J D) (= I C) (= H B) (= G A) true) a!1)) :named step_0))
(rule (! (let ((a!1 (and (State T S R Q P O N M L K J I H G F E D C B A)
                (not (and (= L F) (= K E) (= J D) (= I C) (= H B) (= G A))))))
  (=> a!1 Bad)) :named observe_1))
(rule (! (let ((a!1 (State T S R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 (= L F) (= K E) (= J D) (= I C) (= H B) (= G A) true) a!1)) :named step_1))
(rule (! (let ((a!1 (store (store (store ((as const (Array Int Int)) 0) 1 L) 2 K) 3 J))
      (a!3 (store (store (store ((as const (Array Int Int)) 0) 1 F) 2 E) 3 D)))
(let ((a!2 (ite R
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
(let ((a!5 (= (select (ite (and R Q) (store a!2 8589934593 258) a!2) 2)
              (select (ite (and N M) (store a!4 8589934593 258) a!4) 2)))
      (a!6 (= (select (ite (and R Q) (store a!2 8589934593 258) a!2) 3)
              (select (ite (and N M) (store a!4 8589934593 258) a!4) 3)))
      (a!7 (= (select (ite (and R Q) (store a!2 8589934593 258) a!2) 8589934592)
              (select (ite (and N M) (store a!4 8589934593 258) a!4) 8589934592)))
      (a!8 (= (select (ite (and R Q) (store a!2 8589934593 258) a!2) 8589934593)
              (select (ite (and N M) (store a!4 8589934593 258) a!4) 8589934593)))
      (a!9 (= (select (ite (and R Q) (store a!2 8589934593 258) a!2) 8589934594)
              (select (ite (and N M) (store a!4 8589934593 258) a!4) 8589934594))))
(let ((a!10 (not (and (= (select a!2 1) (select a!4 1)) a!5 a!6 a!7 a!8 a!9))))
  (=> (and (State T S R Q P O N M L K J I H G F E D C B A) a!10) Bad))))) :named observe_2))
(rule (! (let ((a!1 (store (store (store ((as const (Array Int Int)) 0) 1 L) 2 K) 3 J))
      (a!3 (store (store (store ((as const (Array Int Int)) 0) 1 F) 2 E) 3 D)))
(let ((a!2 (ite R
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
(let ((a!5 (= (select (ite (and R Q) (store a!2 8589934593 258) a!2) 2)
              (select (ite (and N M) (store a!4 8589934593 258) a!4) 2)))
      (a!6 (= (select (ite (and R Q) (store a!2 8589934593 258) a!2) 3)
              (select (ite (and N M) (store a!4 8589934593 258) a!4) 3)))
      (a!7 (= (select (ite (and R Q) (store a!2 8589934593 258) a!2) 8589934592)
              (select (ite (and N M) (store a!4 8589934593 258) a!4) 8589934592)))
      (a!8 (= (select (ite (and R Q) (store a!2 8589934593 258) a!2) 8589934593)
              (select (ite (and N M) (store a!4 8589934593 258) a!4) 8589934593)))
      (a!9 (= (select (ite (and R Q) (store a!2 8589934593 258) a!2) 8589934594)
              (select (ite (and N M) (store a!4 8589934593 258) a!4) 8589934594))))
  (=> (and (State T S R Q P O N M L K J I H G F E D C B A)
           (= (select a!2 1) (select a!4 1))
           a!5
           a!6
           a!7
           a!8
           a!9
           false)
      (State T
             S
             false
             Q
             P
             O
             false
             M
             (select a!2 1)
             (select a!2 2)
             (select a!2 3)
             (select a!2 8589934592)
             (ite (and R Q) 258 (select a!2 8589934593))
             (select a!2 8589934594)
             (select a!4 1)
             (select a!4 2)
             (select a!4 3)
             (select a!4 8589934592)
             (ite (and N M) 258 (select a!4 8589934593))
             (select a!4 8589934594)))))) :named step_2))
(rule (! (let ((a!1 (and (State T S R Q P O N M L K J I H G F E D C B A)
                (not (and (= L F) (= K E) (= J D) (= I C) (= H B) (= G A))))))
  (=> a!1 Bad)) :named observe_3))
(rule (! (let ((a!1 (State T S R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 (= L F) (= K E) (= J D) (= I C) (= H B) (= G A) false) a!1)) :named step_3))
(rule (! (let ((a!1 (store (store (store ((as const (Array Int Int)) 0) 1 L) 3 J)
                  8589934592
                  I))
      (a!2 (store (store (store ((as const (Array Int Int)) 0) 1 L) 2 K) 3 J))
      (a!4 (store (store (store ((as const (Array Int Int)) 0) 1 F) 3 D)
                  8589934592
                  C))
      (a!5 (store (store (store ((as const (Array Int Int)) 0) 1 F) 2 E) 3 D)))
(let ((a!3 (ite R
                (store (store (store a!1 8589934593 H) 8589934594 G) 2 0)
                (store (store (store a!2 8589934592 I) 8589934593 H)
                       8589934594
                       G)))
      (a!6 (ite N
                (store (store (store a!4 8589934593 B) 8589934594 A) 2 0)
                (store (store (store a!5 8589934592 C) 8589934593 B)
                       8589934594
                       A))))
(let ((a!7 (not (and (= (select a!3 1) (select a!6 1))
                     (= (select a!3 2) (select a!6 2))
                     (= (select a!3 3) (select a!6 3))
                     (= (select a!3 8589934592) (select a!6 8589934592))
                     (= (select a!3 8589934593) (select a!6 8589934593))
                     (= (select a!3 8589934594) (select a!6 8589934594))))))
  (=> (and (State T S R Q P O N M L K J I H G F E D C B A) a!7) Bad)))) :named observe_4))
(rule (! (let ((a!1 (store (store (store ((as const (Array Int Int)) 0) 1 L) 3 J)
                  8589934592
                  I))
      (a!2 (store (store (store ((as const (Array Int Int)) 0) 1 L) 2 K) 3 J))
      (a!4 (store (store (store ((as const (Array Int Int)) 0) 1 F) 3 D)
                  8589934592
                  C))
      (a!5 (store (store (store ((as const (Array Int Int)) 0) 1 F) 2 E) 3 D)))
(let ((a!3 (ite R
                (store (store (store a!1 8589934593 H) 8589934594 G) 2 0)
                (store (store (store a!2 8589934592 I) 8589934593 H)
                       8589934594
                       G)))
      (a!6 (ite N
                (store (store (store a!4 8589934593 B) 8589934594 A) 2 0)
                (store (store (store a!5 8589934592 C) 8589934593 B)
                       8589934594
                       A))))
  (=> (and (State T S R Q P O N M L K J I H G F E D C B A)
           (= (select a!3 1) (select a!6 1))
           (= (select a!3 2) (select a!6 2))
           (= (select a!3 3) (select a!6 3))
           (= (select a!3 8589934592) (select a!6 8589934592))
           (= (select a!3 8589934593) (select a!6 8589934593))
           (= (select a!3 8589934594) (select a!6 8589934594))
           false)
      (State T
             S
             R
             Q
             P
             O
             N
             M
             (select a!3 1)
             (select a!3 2)
             (select a!3 3)
             (select a!3 8589934592)
             (select a!3 8589934593)
             (select a!3 8589934594)
             (select a!6 1)
             (select a!6 2)
             (select a!6 3)
             (select a!6 8589934592)
             (select a!6 8589934593)
             (select a!6 8589934594))))) :named step_4))
(rule (! (let ((a!1 (and (State T S R Q P O N M L K J I H G F E D C B A)
                (not (and (= L F) (= K E) (= J D) (= I C) (= H B) (= G A))))))
  (=> a!1 Bad)) :named observe_5))
(rule (! (let ((a!1 (State T S R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 (= L F) (= K E) (= J D) (= I C) (= H B) (= G A) true) a!1)) :named step_5))
(rule (! (=> (and (State T S R Q P O N M W V U L K J I H G F E D)
         (>= C 0)
         (<= C 255)
         (>= B 0)
         (<= B 255)
         (>= A 0)
         (<= A 255))
    (State T S R Q P O N M C B A L K J C B A F E D)) :named common_public_assignment))

(query Bad)
