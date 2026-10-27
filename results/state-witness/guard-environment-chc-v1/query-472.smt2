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
(declare-var M1 Bool)
(declare-var N1 Bool)
(declare-var O1 Bool)
(declare-var P1 Bool)
(declare-var Q1 Bool)
(declare-var R1 Bool)
(declare-var S1 Bool)
(declare-var T1 Bool)
(rule (State false
       true
       false
       true
       false
       false
       true
       false
       144
       197
       105
       22
       122
       258
       258
       144
       197
       105
       22
       122
       258
       258))
(rule (! (=> (and (State V U T S R Q P O N M L K J I H G F E D C B A) (not true)) Bad) :named observe_0))
(rule (! (let ((a!1 (State V U T S R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 true true) a!1)) :named step_0))
(rule (! (=> (and (State V U T S R Q P O N M L K J I H G F E D C B A) (not true)) Bad) :named observe_1))
(rule (! (let ((a!1 (State V U T S R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 true true) a!1)) :named step_1))
(rule (! (=> (and (State V U T S R Q P O N M L K J I H G F E D C B A) (not true)) Bad) :named observe_2))
(rule (! (let ((a!1 (State V U T S R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 true true) a!1)) :named step_2))
(rule (! (=> (and (State V U T S R Q P O N M L K J I H G F E D C B A) (not true)) Bad) :named observe_3))
(rule (! (=> (and (State V U T S R Q P O N M L K J I H G F E D C B A) true true)
    (State V U T S R Q P O N 65 65 K J I H G 65 65 D C B A)) :named step_3))
(rule (! (=> (and (State V U T S R Q P O N M L K J I H G F E D C B A) (not true)) Bad) :named observe_4))
(rule (! (let ((a!1 (store (store (store ((as const (Array Int Int)) 0) 0 N) 1 M) 2 L))
      (a!4 (store (store (store ((as const (Array Int Int)) 0) 0 G) 1 F) 2 E)))
(let ((a!2 (store (store (store (store a!1 3 K) 4 J) 8589934593 H)
                  8589934592
                  258))
      (a!3 (store (store (store (store a!1 3 K) 4 J) 8589934592 I) 8589934593 H))
      (a!5 (store (store (store (store a!4 3 D) 4 C) 8589934593 A)
                  8589934592
                  258))
      (a!6 (store (store (store (store a!4 3 D) 4 C) 8589934592 B) 8589934593 A)))
  (=> (and (State V U T S R Q P O N M L K J I H G F E D C B A) true true)
      (State false
             U
             T
             S
             false
             Q
             P
             O
             (select (ite S a!2 a!3) 0)
             (select (ite S a!2 a!3) 1)
             (select (ite S a!2 a!3) 2)
             (select (ite S a!2 a!3) 3)
             (select (ite S a!2 a!3) 4)
             (select (ite S a!2 a!3) 8589934592)
             (select (ite S a!2 a!3) 8589934593)
             (select (ite O a!5 a!6) 0)
             (select (ite O a!5 a!6) 1)
             (select (ite O a!5 a!6) 2)
             (select (ite O a!5 a!6) 3)
             (select (ite O a!5 a!6) 4)
             (select (ite O a!5 a!6) 8589934592)
             (select (ite O a!5 a!6) 8589934593))))) :named step_4))
(rule (! (let ((a!1 (and (State V U T S R Q P O N M L K J I H G F E D C B A)
                (not (and (= N G) (= M F) (= L E) (= K D) (= J C))))))
  (=> a!1 Bad)) :named observe_5))
(rule (! (let ((a!1 (State V U T S R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 (= N G) (= M F) (= L E) (= K D) (= J C) true) a!1)) :named step_5))
(rule (! (=> (and (State V U T S R Q P O X W N M L K J I H G F E D C)
         (>= B 256)
         (>= A 256))
    (State V U T S R Q P O X W N M L B A I H G F E B A)) :named common_public_assignment))

(query Bad)
