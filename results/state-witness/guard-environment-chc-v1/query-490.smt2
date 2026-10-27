(declare-rel State (Bool Bool Bool Bool Bool Bool Bool Bool Int Int Int Int Int Int Int Int Int Int))
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
(declare-var K Bool)
(declare-var L Bool)
(declare-var M Bool)
(declare-var N Bool)
(declare-var O Bool)
(declare-var P Bool)
(declare-var Q Bool)
(declare-var R Bool)
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
(declare-var F1 Int)
(declare-var G1 Int)
(declare-var H1 Bool)
(declare-var I1 Bool)
(declare-var J1 Bool)
(declare-var K1 Bool)
(declare-var L1 Bool)
(declare-var M1 Bool)
(declare-var N1 Bool)
(declare-var O1 Bool)
(rule (State false
       false
       false
       true
       true
       false
       false
       true
       65
       52
       199
       256
       258
       65
       52
       199
       256
       258))
(rule (! (=> (and (State R Q P O N M L K J I H G F E D C B A) (not true)) Bad) :named observe_0))
(rule (! (let ((a!1 (State R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 true true) a!1)) :named step_0))
(rule (! (=> (and (State R Q P O N M L K J I H G F E D C B A) (not true)) Bad) :named observe_1))
(rule (! (let ((a!1 (State R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 true true) a!1)) :named step_1))
(rule (! (=> (and (State R Q P O N M L K J I H G F E D C B A) (not true)) Bad) :named observe_2))
(rule (! (let ((a!1 (store (store (store ((as const (Array Int Int)) 0) 1 I) 2 H)
                  8589934594
                  G))
      (a!2 (store (store (store ((as const (Array Int Int)) 0) 0 J) 1 I) 2 H))
      (a!4 (store (store (store ((as const (Array Int Int)) 0) 1 D) 2 C)
                  8589934594
                  B))
      (a!5 (store (store (store ((as const (Array Int Int)) 0) 0 E) 1 D) 2 C)))
(let ((a!3 (ite R
                (store (store a!1 8589934595 F) 0 65)
                (store (store a!2 8589934594 G) 8589934595 F)))
      (a!6 (ite N
                (store (store a!4 8589934595 A) 0 65)
                (store (store a!5 8589934594 B) 8589934595 A))))
  (=> (and (State R Q P O N M L K J I H G F E D C B A) true true)
      (State false
             Q
             P
             O
             false
             M
             L
             K
             (select a!3 0)
             (ite (and R Q) 67 (select a!3 1))
             (select a!3 2)
             (select a!3 8589934594)
             (select a!3 8589934595)
             (select a!6 0)
             (ite (and N M) 67 (select a!6 1))
             (select a!6 2)
             (select a!6 8589934594)
             (select a!6 8589934595))))) :named step_2))
(rule (! (=> (and (State R Q P O N M L K J I H G F E D C B A) (not true)) Bad) :named observe_3))
(rule (! (=> (and (State R Q P O N M L K J I H G F E D C B A) true true)
    (State R Q P false N M L false J I H F F E D C A A)) :named step_3))
(rule (! (=> (and (State R Q P O N M L K J I H G F E D C B A) (not true)) Bad) :named observe_4))
(rule (! (=> (and (State R Q P O N M L K J I H G F E D C B A) true true)
    (State false Q P O false M L K J I H G F E D C B A)) :named step_4))
(rule (! (let ((a!1 (and (State R Q P O N M L K J I H G F E D C B A)
                (not (and (= J E) (= I D) (= H C))))))
  (=> a!1 Bad)) :named observe_5))
(rule (! (let ((a!1 (State R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 (= J E) (= I D) (= H C) true) a!1)) :named step_5))
(rule (! (=> (and (State R Q P O N M L K W V U T S J I H G F)
         (>= E 0)
         (<= E 255)
         (>= D 0)
         (<= D 255)
         (>= C 0)
         (<= C 255)
         (>= B 256)
         (>= A 256))
    (State R Q P O N M L K E D C B A E D C B A)) :named common_public_assignment))

(query Bad)
