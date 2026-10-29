(declare-rel State (Bool Bool Bool Bool Int Int Int Int Int Int))
(declare-rel Bad ())
(declare-var A Int)
(declare-var B Int)
(declare-var C Int)
(declare-var D Int)
(declare-var E Int)
(declare-var F Int)
(declare-var G Bool)
(declare-var H Bool)
(declare-var I Bool)
(declare-var J Bool)
(rule (State false false true false 257 257 258 257 257 258))
(rule (! (=> (and (State J I H G F E D C B A) (not true)) Bad) :named observe_0))
(rule (! (let ((a!1 (State J I H G F E D C B A)))
  (=> (and a!1 true true) a!1)) :named step_0))
(rule (! (=> (and (State J I H G F E D C B A) (not true)) Bad) :named observe_1))
(rule (! (let ((a!1 (State J I H G F E D C B A)))
  (=> (and a!1 true true) a!1)) :named step_1))
(rule (! (let ((a!1 (and (State J I H G F E D C B A) (not (= (and J I) (and H G))))))
  (=> a!1 Bad)) :named observe_2))
(rule (! (=> (and (State J I H G F E D C B A) (= (and J I) (and H G)) true)
    (State false
           I
           false
           G
           F
           (ite (and J I) 258 E)
           (ite J 257 D)
           C
           (ite (and H G) 258 B)
           (ite H 257 A))) :named step_2))
(rule (! (=> (and (State J I H G F E D C B A) (not true)) Bad) :named observe_3))
(rule (! (=> (and (State J I H G F E D C B A) true true) (State J I H G F D D C A A)) :named step_3))
(rule (! (=> (and (State J I H G F E D C B A) (not true)) Bad) :named observe_4))
(rule (! (=> (and (State J I H G F E D C B A) true true) (State J I H G E E D B B A)) :named step_4))

(query Bad)
