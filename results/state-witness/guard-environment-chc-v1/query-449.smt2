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
(declare-var E1 Bool)
(declare-var F1 Bool)
(declare-var G1 Bool)
(declare-var H1 Bool)
(declare-var I1 Bool)
(declare-var J1 Bool)
(declare-var K1 Bool)
(declare-var L1 Bool)
(rule (State false
       true
       true
       true
       false
       false
       true
       true
       239
       137
       63
       256
       256
       239
       137
       63
       256
       256))
(rule (! (=> (and (State R Q P O N M L K J I H G F E D C B A) (not true)) Bad) :named observe_0))
(rule (! (let ((a!1 (State R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 true true) a!1)) :named step_0))
(rule (! (=> (and (State R Q P O N M L K J I H G F E D C B A) (not true)) Bad) :named observe_1))
(rule (! (let ((a!1 (State R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 true true) a!1)) :named step_1))
(rule (! (=> (and (State R Q P O N M L K J I H G F E D C B A) (not (= P L))) Bad) :named observe_2))
(rule (! (let ((a!1 (store (store (store ((as const (Array Int Int)) 0) 0 J) 1 I) 2 H))
      (a!3 (store (store (store ((as const (Array Int Int)) 0) 0 E) 1 D) 2 C)))
(let ((a!2 (ite P
                (store (store a!1 4294967296 257) 4294967297 258)
                (store (store a!1 4294967296 G) 4294967297 F)))
      (a!4 (ite L
                (store (store a!3 4294967296 257) 4294967297 258)
                (store (store a!3 4294967296 B) 4294967297 A))))
  (=> (and (State R Q P O N M L K J I H G F E D C B A) (= P L) (or P L))
      (State R
             Q
             false
             O
             N
             M
             false
             K
             (select a!2 0)
             (select a!2 1)
             (select a!2 2)
             (select a!2 4294967296)
             (select a!2 4294967297)
             (select a!4 0)
             (select a!4 1)
             (select a!4 2)
             (select a!4 4294967296)
             (select a!4 4294967297))))) :named step_2))
(rule (! (=> (and (State R Q P O N M L K J I H G F E D C B A) (not true)) Bad) :named observe_3))
(rule (! (=> (and (State R Q P O N M L K J I H G F E D C B A) true false)
    (State false Q P O false M L K 0 I H G F 0 D C B A)) :named step_3))
(rule (! (=> (and (State R Q P O N M L K J I H G F E D C B A) (not true)) Bad) :named observe_4))
(rule (! (=> (and (State R Q P O N M L K J I H G F E D C B A) true false)
    (State R false P O N false L K J I H G F E D C B A)) :named step_4))
(rule (! (let ((a!1 (and (State R Q P O N M L K J I H G F E D C B A)
                (not (and (= J E) (= I D) (= H C))))))
  (=> a!1 Bad)) :named observe_5))
(rule (! (let ((a!1 (State R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 (= J E) (= I D) (= H C) true) a!1)) :named step_5))
(rule (! (=> (and (State R Q P O N M L K T S J I H G F E D C) (>= B 256) (>= A 256))
    (State R Q P O N M L K T S J B A G F E B A)) :named common_public_assignment))

(query Bad)
