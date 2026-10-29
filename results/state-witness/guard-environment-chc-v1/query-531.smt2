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
(declare-var C1 Bool)
(declare-var D1 Bool)
(declare-var E1 Bool)
(declare-var F1 Bool)
(declare-var G1 Bool)
(declare-var H1 Bool)
(declare-var I1 Bool)
(declare-var J1 Bool)
(rule (State false
       true
       false
       false
       false
       true
       true
       false
       137
       140
       252
       65
       25
       137
       140
       252
       65
       25))
(rule (! (=> (and (State R Q P O N M L K J I H G F E D C B A) (not true)) Bad) :named observe_0))
(rule (! (let ((a!1 (State R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 true true) a!1)) :named step_0))
(rule (! (=> (and (State R Q P O N M L K J I H G F E D C B A) (not true)) Bad) :named observe_1))
(rule (! (let ((a!1 (State R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 true true) a!1)) :named step_1))
(rule (! (=> (and (State R Q P O N M L K J I H G F E D C B A) (not true)) Bad) :named observe_2))
(rule (! (let ((a!1 (State R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 true false) a!1)) :named step_2))
(rule (! (=> (and (State R Q P O N M L K J I H G F E D C B A) (not true)) Bad) :named observe_3))
(rule (! (let ((a!1 (State R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 true false) a!1)) :named step_3))
(rule (! (=> (and (State R Q P O N M L K J I H G F E D C B A) (not true)) Bad) :named observe_4))
(rule (! (let ((a!1 (State R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 true false) a!1)) :named step_4))
(rule (! (let ((a!1 (and (State R Q P O N M L K J I H G F E D C B A)
                (not (and (= J E) (= I D) (= H C) (= G B) (= F A))))))
  (=> a!1 Bad)) :named observe_5))
(rule (! (let ((a!1 (State R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 (= J E) (= I D) (= H C) (= G B) (= F A) true) a!1)) :named step_5))
(rule (! (let ((a!1 (State R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1) a!1)) :named common_public_assignment))

(query Bad)
