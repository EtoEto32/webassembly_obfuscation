(declare-rel State (Bool Bool Bool Bool Bool Bool Bool Bool Int Int Int Int Int Int Int Int Int Int Int Int Int Int))
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
(declare-var M Int)
(declare-var N Int)
(declare-var O Bool)
(declare-var P Bool)
(declare-var Q Bool)
(declare-var R Bool)
(declare-var S Bool)
(declare-var T Bool)
(declare-var U Bool)
(declare-var V Bool)
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
(declare-var J1 Int)
(declare-var K1 Int)
(declare-var L1 Int)
(declare-var M1 Int)
(declare-var N1 Int)
(declare-var O1 Int)
(declare-var P1 Bool)
(declare-var Q1 Bool)
(declare-var R1 Bool)
(declare-var S1 Bool)
(declare-var T1 Bool)
(declare-var U1 Bool)
(declare-var V1 Bool)
(declare-var W1 Bool)
(rule (State false
       false
       false
       true
       true
       false
       true
       true
       65
       38
       258
       257
       256
       256
       256
       65
       38
       258
       257
       256
       256
       256))
(rule (! (let ((a!1 (and (State V U T S R Q P O N M L K J I H G F E D C B A)
                (not (and (= N G) (= M F) (= J C) (= I B) (= H A))))))
  (=> a!1 Bad)) :named observe_0))
(rule (! (let ((a!1 (State V U T S R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 (= N G) (= M F) (= J C) (= I B) (= H A) true) a!1)) :named step_0))
(rule (! (let ((a!1 (and (State V U T S R Q P O N M L K J I H G F E D C B A)
                (not (and (= N G) (= M F) (= J C) (= I B) (= H A))))))
  (=> a!1 Bad)) :named observe_1))
(rule (! (let ((a!1 (State V U T S R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 (= N G) (= M F) (= J C) (= I B) (= H A) true) a!1)) :named step_1))
(rule (! (let ((a!1 (store (store (store ((as const (Array Int Int)) 0) 1 M)
                         4294967297
                         L)
                  4294967298
                  K))
      (a!3 (store (store (store ((as const (Array Int Int)) 0) 0 N) 1 M)
                  4294967297
                  L))
      (a!5 (store (store (store ((as const (Array Int Int)) 0) 1 F)
                         4294967297
                         E)
                  4294967298
                  D))
      (a!7 (store (store (store ((as const (Array Int Int)) 0) 0 G) 1 F)
                  4294967297
                  E)))
(let ((a!2 (store (store (store (store a!1 8589934593 J) 8589934594 I)
                         8589934595
                         H)
                  0
                  65))
      (a!4 (store (store (store (store a!3 4294967298 K) 8589934593 J)
                         8589934594
                         I)
                  8589934595
                  H))
      (a!6 (store (store (store (store a!5 8589934593 C) 8589934594 B)
                         8589934595
                         A)
                  0
                  65))
      (a!8 (store (store (store (store a!7 4294967298 D) 8589934593 C)
                         8589934594
                         B)
                  8589934595
                  A)))
(let ((a!9 (ite (and V U) (store (ite V a!2 a!4) 1 67) (ite V a!2 a!4)))
      (a!10 (ite (and R Q) (store (ite R a!6 a!8) 1 67) (ite R a!6 a!8))))
(let ((a!11 (and (= (select (ite V a!2 a!4) 0) (select (ite R a!6 a!8) 0))
                 (= (select a!9 1) (select a!10 1))
                 (= (select a!9 8589934593) (select a!10 8589934593))
                 (= (select a!9 8589934594) (select a!10 8589934594))
                 (= (select a!9 8589934595) (select a!10 8589934595)))))
  (=> (and (State V U T S R Q P O N M L K J I H G F E D C B A) (not a!11)) Bad))))) :named observe_2))
(rule (! (let ((a!1 (store (store (store ((as const (Array Int Int)) 0) 1 M)
                         4294967297
                         L)
                  4294967298
                  K))
      (a!3 (store (store (store ((as const (Array Int Int)) 0) 0 N) 1 M)
                  4294967297
                  L))
      (a!5 (store (store (store ((as const (Array Int Int)) 0) 1 F)
                         4294967297
                         E)
                  4294967298
                  D))
      (a!7 (store (store (store ((as const (Array Int Int)) 0) 0 G) 1 F)
                  4294967297
                  E)))
(let ((a!2 (store (store (store (store a!1 8589934593 J) 8589934594 I)
                         8589934595
                         H)
                  0
                  65))
      (a!4 (store (store (store (store a!3 4294967298 K) 8589934593 J)
                         8589934594
                         I)
                  8589934595
                  H))
      (a!6 (store (store (store (store a!5 8589934593 C) 8589934594 B)
                         8589934595
                         A)
                  0
                  65))
      (a!8 (store (store (store (store a!7 4294967298 D) 8589934593 C)
                         8589934594
                         B)
                  8589934595
                  A)))
(let ((a!9 (ite (and V U) (store (ite V a!2 a!4) 1 67) (ite V a!2 a!4)))
      (a!10 (ite (and R Q) (store (ite R a!6 a!8) 1 67) (ite R a!6 a!8)))
      (a!12 (State false
                   (and (not (and V U)) U)
                   T
                   S
                   false
                   (and (not (and R Q)) Q)
                   P
                   O
                   (select (ite V a!2 a!4) 0)
                   (ite (and V U) 67 (select (ite V a!2 a!4) 1))
                   (select (ite V a!2 a!4) 4294967297)
                   (select (ite V a!2 a!4) 4294967298)
                   (select (ite V a!2 a!4) 8589934593)
                   (select (ite V a!2 a!4) 8589934594)
                   (select (ite V a!2 a!4) 8589934595)
                   (select (ite R a!6 a!8) 0)
                   (ite (and R Q) 67 (select (ite R a!6 a!8) 1))
                   (select (ite R a!6 a!8) 4294967297)
                   (select (ite R a!6 a!8) 4294967298)
                   (select (ite R a!6 a!8) 8589934593)
                   (select (ite R a!6 a!8) 8589934594)
                   (select (ite R a!6 a!8) 8589934595))))
(let ((a!11 (and (State V U T S R Q P O N M L K J I H G F E D C B A)
                 (= (select (ite V a!2 a!4) 0) (select (ite R a!6 a!8) 0))
                 (= (select a!9 1) (select a!10 1))
                 (= (select a!9 8589934593) (select a!10 8589934593))
                 (= (select a!9 8589934594) (select a!10 8589934594))
                 (= (select a!9 8589934595) (select a!10 8589934595))
                 false)))
  (=> a!11 a!12))))) :named step_2))
(rule (! (let ((a!1 (and (State V U T S R Q P O N M L K J I H G F E D C B A)
                (not (and (= N G) (= M F) (= J C) (= I B) (= H A))))))
  (=> a!1 Bad)) :named observe_3))
(rule (! (let ((a!1 (State V U T S R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 (= N G) (= M F) (= J C) (= I B) (= H A) false) a!1)) :named step_3))
(rule (! (let ((a!1 (and (State V U T S R Q P O N M L K J I H G F E D C B A)
                (not (and (= N G) (= M F) (= J C) (= I B) (= H A))))))
  (=> a!1 Bad)) :named observe_4))
(rule (! (=> (and (State V U T S R Q P O N M L K J I H G F E D C B A)
         (= N G)
         (= M F)
         (= J C)
         (= I B)
         (= H A)
         false)
    (State V false T S R false P O N M L K J I H G F E D C B A)) :named step_4))
(rule (! (let ((a!1 (and (State V U T S R Q P O N M L K J I H G F E D C B A)
                (not (and (= N G) (= M F) (= J C) (= I B) (= H A))))))
  (=> a!1 Bad)) :named observe_5))
(rule (! (let ((a!1 (State V U T S R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 (= N G) (= M F) (= J C) (= I B) (= H A) true) a!1)) :named step_5))
(rule (! (=> (and (State V U T S R Q P O A1 Z Y X W N M L K J I H G F)
         (>= E 0)
         (<= E 255)
         (>= D 0)
         (<= D 255)
         (>= C 256)
         (>= B 256)
         (>= A 256))
    (State V U T S R Q P O E D Y X C B A E D J I C B A)) :named common_public_assignment))

(query Bad)
