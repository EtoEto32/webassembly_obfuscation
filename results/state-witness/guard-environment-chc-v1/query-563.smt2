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
(declare-var G1 Bool)
(declare-var H1 Bool)
(declare-var I1 Bool)
(declare-var J1 Bool)
(declare-var K1 Bool)
(declare-var L1 Bool)
(declare-var M1 Bool)
(declare-var N1 Bool)
(rule (State false
       false
       true
       true
       true
       false
       false
       false
       214
       39
       131
       127
       256
       214
       39
       131
       127
       256))
(rule (! (=> (and (State R Q P O N M L K J I H G F E D C B A) (not true)) Bad) :named observe_0))
(rule (! (let ((a!1 (State R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 true true) a!1)) :named step_0))
(rule (! (=> (and (State R Q P O N M L K J I H G F E D C B A) (not true)) Bad) :named observe_1))
(rule (! (let ((a!1 (State R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 true true) a!1)) :named step_1))
(rule (! (=> (and (State R Q P O N M L K J I H G F E D C B A) (not true)) Bad) :named observe_2))
(rule (! (let ((a!1 (store (store (store ((as const (Array Int Int)) 0) 1 I) 2 H) 3 G))
      (a!2 (store (store (store ((as const (Array Int Int)) 0) 0 J) 1 I) 2 H))
      (a!4 (store (store (store ((as const (Array Int Int)) 0) 1 D) 2 C) 3 B))
      (a!5 (store (store (store ((as const (Array Int Int)) 0) 0 E) 1 D) 2 C)))
(let ((a!3 (ite R
                (store (store a!1 4294967299 F) 0 65)
                (store (store a!2 3 G) 4294967299 F)))
      (a!6 (ite N
                (store (store a!4 4294967299 A) 0 65)
                (store (store a!5 3 B) 4294967299 A))))
  (=> (and (State R Q P O N M L K J I H G F E D C B A) true false)
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
             (select a!3 3)
             (select a!3 4294967299)
             (select a!6 0)
             (ite (and N M) 67 (select a!6 1))
             (select a!6 2)
             (select a!6 3)
             (select a!6 4294967299))))) :named step_2))
(rule (! (=> (and (State R Q P O N M L K J I H G F E D C B A) (not true)) Bad) :named observe_3))
(rule (! (=> (and (State R Q P O N M L K J I H G F E D C B A) true true)
    (State R false P false N false L false J I H G F E D C B A)) :named step_3))
(rule (! (=> (and (State R Q P O N M L K J I H G F E D C B A) (not true)) Bad) :named observe_4))
(rule (! (let ((a!1 (State R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 true false) a!1)) :named step_4))
(rule (! (let ((a!1 (and (State R Q P O N M L K J I H G F E D C B A)
                (not (and (= J E) (= I D) (= H C) (= G B))))))
  (=> a!1 Bad)) :named observe_5))
(rule (! (let ((a!1 (State R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 (= J E) (= I D) (= H C) (= G B) true) a!1)) :named step_5))
(rule (! (=> (and (State R Q P O N M L K V U T S J I H G F E)
         (>= D 0)
         (<= D 255)
         (>= C 0)
         (<= C 255)
         (>= B 0)
         (<= B 255)
         (>= A 0)
         (<= A 255))
    (State R Q P O N M L K D C B A J D C B A E)) :named common_public_assignment))

(query Bad)
