(declare-rel State (Bool Bool Bool Bool Int Int Int Int Int Int Int Int Int Int Int Int Int Int))
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
(rule (State true
       true
       false
       true
       256
       256
       258
       258
       256
       258
       256
       256
       256
       258
       258
       256
       258
       256))
(rule (! (=> (and (State R Q P O N M L K J I H G F E D C B A) (not true)) Bad) :named observe_0))
(rule (! (let ((a!1 (State R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 true true) a!1)) :named step_0))
(rule (! (=> (and (State R Q P O N M L K J I H G F E D C B A) (not true)) Bad) :named observe_1))
(rule (! (let ((a!1 (State R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 true true) a!1)) :named step_1))
(rule (! (=> (and (State R Q P O N M L K J I H G F E D C B A) (not true)) Bad) :named observe_2))
(rule (! (=> (and (State R Q P O N M L K J I H G F E D C B A) true false)
    (State R false P false N M L K J I H G F E D C B A)) :named step_2))
(rule (! (=> (and (State R Q P O N M L K J I H G F E D C B A) (not true)) Bad) :named observe_3))
(rule (! (=> (and (State R Q P O N M L K J I H G F E D C B A) true true)
    (State R Q P O 258 M L K J I H 258 F E D C B A)) :named step_3))
(rule (! (=> (and (State R Q P O N M L K J I H G F E D C B A) (not true)) Bad) :named observe_4))
(rule (! (let ((a!1 (State R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 true false) a!1)) :named step_4))
(rule (! (let ((a!1 (State R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1) a!1)) :named common_public_assignment))

(query Bad)
