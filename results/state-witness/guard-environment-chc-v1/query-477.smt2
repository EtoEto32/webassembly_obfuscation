(declare-rel Bad ())
(declare-rel State (Bool Bool Bool Bool Bool Bool Bool Bool Int Int Int Int Int Int Int Int Int Int Int Int Int Int Int Int))
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
(declare-var M Int)
(declare-var N Int)
(declare-var O Int)
(declare-var P Int)
(declare-var Q Bool)
(declare-var R Bool)
(declare-var S Bool)
(declare-var T Bool)
(declare-var U Bool)
(declare-var V Bool)
(declare-var W Bool)
(declare-var X Bool)
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
(declare-var J1 Int)
(declare-var K1 Int)
(declare-var L1 Int)
(declare-var M1 Int)
(declare-var N1 Int)
(declare-var O1 Int)
(declare-var P1 Int)
(declare-var Q1 Int)
(declare-var R1 Int)
(declare-var S1 Int)
(declare-var T1 Int)
(declare-var U1 Bool)
(declare-var V1 Bool)
(declare-var W1 Bool)
(declare-var X1 Bool)
(declare-var Y1 Bool)
(declare-var Z1 Bool)
(declare-var A2 Bool)
(declare-var B2 Bool)
(rule (State true
       false
       false
       false
       true
       true
       true
       false
       152
       191
       181
       69
       32
       256
       258
       256
       152
       191
       181
       69
       32
       256
       258
       256))
(rule (! (let ((a!1 (and (State X W V U T S R Q P O N M L K J I H G F E D C B A)
                (not (and (= P H) (= O G) (= N F) (= M E) (= L D) (= K C))))))
  (=> a!1 Bad)) :named observe_0))
(rule (! (let ((a!1 (State X W V U T S R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 (= P H) (= O G) (= N F) (= M E) (= L D) (= K C) true) a!1)) :named step_0))
(rule (! (let ((a!1 (and (State X W V U T S R Q P O N M L K J I H G F E D C B A)
                (not (and (= P H) (= O G) (= N F) (= M E) (= L D) (= K C))))))
  (=> a!1 Bad)) :named observe_1))
(rule (! (let ((a!1 (State X W V U T S R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 (= P H) (= O G) (= N F) (= M E) (= L D) (= K C) true) a!1)) :named step_1))
(rule (! (let ((a!1 (store (store (store ((as const (Array Int Int)) 0) 0 P) 1 O) 2 N))
      (a!6 (store (store (store ((as const (Array Int Int)) 0) 0 H) 1 G) 2 F)))
(let ((a!2 (store (store (store a!1 3 M) 4 L) 4294967298 K))
      (a!7 (store (store (store a!6 3 E) 4 D) 4294967298 C)))
(let ((a!3 (ite V
                (store (store a!2 8589934593 I) 8589934592 257)
                (store (store a!2 8589934592 J) 8589934593 I)))
      (a!8 (ite R
                (store (store a!7 8589934593 A) 8589934592 257)
                (store (store a!7 8589934592 B) 8589934593 A))))
(let ((a!4 (ite (and V U)
                (store (ite (and V U) (store a!3 8589934593 258) a!3) 2 255)
                a!3))
      (a!9 (ite (and R Q)
                (store (ite (and R Q) (store a!8 8589934593 258) a!8) 2 255)
                a!8)))
(let ((a!5 (ite (and V U)
                (select (ite (and V U) (store a!4 4294967298 257) a!3) 0)
                (select a!3 0)))
      (a!10 (ite (and R Q)
                 (select (ite (and R Q) (store a!9 4294967298 257) a!8) 0)
                 (select a!8 0)))
      (a!11 (store (store (ite (and V U) (store a!4 4294967298 257) a!3) 3 0)
                   4
                   0))
      (a!12 (store (store (ite (and R Q) (store a!9 4294967298 257) a!8) 3 0)
                   4
                   0)))
(let ((a!13 (= (select (ite (and V U) a!11 a!3) 1)
               (select (ite (and R Q) a!12 a!8) 1)))
      (a!14 (= (select (ite (and V U) a!11 a!3) 2)
               (select (ite (and R Q) a!12 a!8) 2)))
      (a!15 (= (select (ite (and V U) a!11 a!3) 3)
               (select (ite (and R Q) a!12 a!8) 3)))
      (a!16 (= (select (ite (and V U) a!11 a!3) 4)
               (select (ite (and R Q) a!12 a!8) 4)))
      (a!17 (= (select (ite (and V U) a!11 a!3) 4294967298)
               (select (ite (and R Q) a!12 a!8) 4294967298))))
(let ((a!18 (and (State X W V U T S R Q P O N M L K J I H G F E D C B A)
                 (not (and (= a!5 a!10) a!13 a!14 a!15 a!16 a!17)))))
  (=> a!18 Bad)))))))) :named observe_2))
(rule (! (let ((a!1 (store (store (store ((as const (Array Int Int)) 0) 0 P) 1 O) 2 N))
      (a!6 (store (store (store ((as const (Array Int Int)) 0) 0 H) 1 G) 2 F)))
(let ((a!2 (store (store (store a!1 3 M) 4 L) 4294967298 K))
      (a!7 (store (store (store a!6 3 E) 4 D) 4294967298 C)))
(let ((a!3 (ite V
                (store (store a!2 8589934593 I) 8589934592 257)
                (store (store a!2 8589934592 J) 8589934593 I)))
      (a!8 (ite R
                (store (store a!7 8589934593 A) 8589934592 257)
                (store (store a!7 8589934592 B) 8589934593 A))))
(let ((a!4 (ite (and V U)
                (store (ite (and V U) (store a!3 8589934593 258) a!3) 2 255)
                a!3))
      (a!9 (ite (and R Q)
                (store (ite (and R Q) (store a!8 8589934593 258) a!8) 2 255)
                a!8)))
(let ((a!5 (ite (and V U)
                (select (ite (and V U) (store a!4 4294967298 257) a!3) 0)
                (select a!3 0)))
      (a!10 (ite (and R Q)
                 (select (ite (and R Q) (store a!9 4294967298 257) a!8) 0)
                 (select a!8 0)))
      (a!11 (store (store (ite (and V U) (store a!4 4294967298 257) a!3) 3 0)
                   4
                   0))
      (a!12 (store (store (ite (and R Q) (store a!9 4294967298 257) a!8) 3 0)
                   4
                   0))
      (a!18 (ite (and V U)
                 (select (ite (and V U) (store a!4 4294967298 257) a!3) 1)
                 (select a!3 1)))
      (a!19 (ite (and V U)
                 (select (ite (and V U) (store a!4 4294967298 257) a!3) 2)
                 (select a!3 2)))
      (a!20 (ite (and V U)
                 (select (ite (and V U) (store a!4 4294967298 257) a!3)
                         4294967298)
                 (select a!3 4294967298)))
      (a!21 (ite (and V U)
                 (select (ite (and V U) (store a!4 4294967298 257) a!3)
                         8589934592)
                 (select a!3 8589934592)))
      (a!22 (ite (and V U)
                 (select (ite (and V U) (store a!4 4294967298 257) a!3)
                         8589934593)
                 (select a!3 8589934593)))
      (a!23 (ite (and R Q)
                 (select (ite (and R Q) (store a!9 4294967298 257) a!8) 1)
                 (select a!8 1)))
      (a!24 (ite (and R Q)
                 (select (ite (and R Q) (store a!9 4294967298 257) a!8) 2)
                 (select a!8 2)))
      (a!25 (ite (and R Q)
                 (select (ite (and R Q) (store a!9 4294967298 257) a!8)
                         4294967298)
                 (select a!8 4294967298)))
      (a!26 (ite (and R Q)
                 (select (ite (and R Q) (store a!9 4294967298 257) a!8)
                         8589934592)
                 (select a!8 8589934592)))
      (a!27 (ite (and R Q)
                 (select (ite (and R Q) (store a!9 4294967298 257) a!8)
                         8589934593)
                 (select a!8 8589934593))))
(let ((a!13 (= (select (ite (and V U) a!11 a!3) 1)
               (select (ite (and R Q) a!12 a!8) 1)))
      (a!14 (= (select (ite (and V U) a!11 a!3) 2)
               (select (ite (and R Q) a!12 a!8) 2)))
      (a!15 (= (select (ite (and V U) a!11 a!3) 3)
               (select (ite (and R Q) a!12 a!8) 3)))
      (a!16 (= (select (ite (and V U) a!11 a!3) 4)
               (select (ite (and R Q) a!12 a!8) 4)))
      (a!17 (= (select (ite (and V U) a!11 a!3) 4294967298)
               (select (ite (and R Q) a!12 a!8) 4294967298))))
  (=> (and (State X W V U T S R Q P O N M L K J I H G F E D C B A)
           (= a!5 a!10)
           a!13
           a!14
           a!15
           a!16
           a!17
           false)
      (State X
             W
             false
             U
             T
             S
             false
             Q
             a!5
             a!18
             a!19
             (ite (and V U) 0 (select a!3 3))
             (ite (and V U) 0 (select a!3 4))
             a!20
             a!21
             a!22
             a!10
             a!23
             a!24
             (ite (and R Q) 0 (select a!8 3))
             (ite (and R Q) 0 (select a!8 4))
             a!25
             a!26
             a!27)))))))) :named step_2))
(rule (! (let ((a!1 (and (State X W V U T S R Q P O N M L K J I H G F E D C B A)
                (not (and (= P H) (= O G) (= N F) (= M E) (= L D) (= K C))))))
  (=> a!1 Bad)) :named observe_3))
(rule (! (let ((a!1 (State X W V U T S R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 (= P H) (= O G) (= N F) (= M E) (= L D) (= K C) false) a!1)) :named step_3))
(rule (! (let ((a!1 (and (State X W V U T S R Q P O N M L K J I H G F E D C B A)
                (not (and (= P H) (= O G) (= N F) (= M E) (= L D) (= K C))))))
  (=> a!1 Bad)) :named observe_4))
(rule (! (=> (and (State X W V U T S R Q P O N M L K J I H G F E D C B A)
         (= P H)
         (= O G)
         (= N F)
         (= M E)
         (= L D)
         (= K C)
         false)
    (State X W V false T S R false P O N M L K 256 256 H G F E D C 256 256)) :named step_4))
(rule (! (let ((a!1 (and (State X W V U T S R Q P O N M L K J I H G F E D C B A)
                (not (and (= P H) (= O G) (= N F) (= M E) (= L D) (= K C))))))
  (=> a!1 Bad)) :named observe_5))
(rule (! (let ((a!1 (State X W V U T S R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 (= P H) (= O G) (= N F) (= M E) (= L D) (= K C) true) a!1)) :named step_5))
(rule (! (=> (and (State X W V U T S R Q D1 C1 B1 A1 Z Y P O N M L K J I H G)
         (>= F 0)
         (<= F 255)
         (>= E 0)
         (<= E 255)
         (>= D 0)
         (<= D 255)
         (>= C 0)
         (<= C 255)
         (>= B 0)
         (<= B 255)
         (>= A 256))
    (State X W V U T S R Q F E D C B A P O F E D C B A H G)) :named common_public_assignment))

(query Bad)
