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
(declare-var J1 Int)
(declare-var K1 Int)
(declare-var L1 Bool)
(declare-var M1 Bool)
(declare-var N1 Bool)
(declare-var O1 Bool)
(declare-var P1 Bool)
(declare-var Q1 Bool)
(declare-var R1 Bool)
(declare-var S1 Bool)
(rule (State true
       false
       true
       true
       true
       false
       false
       true
       139
       257
       256
       257
       257
       258
       139
       257
       256
       257
       257
       258))
(rule (! (=> (and (State T S R Q P O N M L K J I H G F E D C B A) (not true)) Bad) :named observe_0))
(rule (! (let ((a!1 (State T S R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 true true) a!1)) :named step_0))
(rule (! (=> (and (State T S R Q P O N M L K J I H G F E D C B A) (not true)) Bad) :named observe_1))
(rule (! (let ((a!1 (State T S R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 true true) a!1)) :named step_1))
(rule (! (=> (and (State T S R Q P O N M L K J I H G F E D C B A) (not true)) Bad) :named observe_2))
(rule (! (let ((a!1 (State T S R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 true true) a!1)) :named step_2))
(rule (! (=> (and (State T S R Q P O N M L K J I H G F E D C B A) (not true)) Bad) :named observe_3))
(rule (! (=> (and (State T S R Q P O N M L K J I H G F E D C B A) true true)
    (State T S R Q P O N M L K 258 258 H G F E 258 258 B A)) :named step_3))
(rule (! (=> (and (State T S R Q P O N M L K J I H G F E D C B A) (not true)) Bad) :named observe_4))
(rule (! (let ((a!1 (State T S R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 true true) a!1)) :named step_4))
(rule (! (=> (and (State T S R Q P O N M L K J I H G F E D C B A) (not (= L F))) Bad) :named observe_5))
(rule (! (let ((a!1 (State T S R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 (= L F) true) a!1)) :named step_5))
(rule (! (=> (and (State T S R Q P O N M Y X W V U L K J I H G F)
         (>= E 256)
         (>= D 256)
         (>= C 256)
         (>= B 256)
         (>= A 256))
    (State T S R Q P O N M Y E D C B A K E D C B A)) :named common_public_assignment))

(query Bad)
