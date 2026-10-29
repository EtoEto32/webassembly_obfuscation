(declare-rel State (Bool Bool Bool Bool Int Int Int Int Int Int Int Int Int Int Int Int Int Int Int Int Int Int))
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
(declare-var O Int)
(declare-var P Int)
(declare-var Q Int)
(declare-var R Int)
(declare-var S Bool)
(declare-var T Bool)
(declare-var U Bool)
(declare-var V Bool)
(rule (State false
       false
       true
       false
       257
       257
       257
       257
       257
       257
       257
       257
       258
       257
       257
       257
       257
       257
       257
       257
       257
       258))
(rule (! (=> (and (State V U T S R Q P O N M L K J I H G F E D C B A) (not true)) Bad) :named observe_0))
(rule (! (let ((a!1 (State V U T S R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 true true) a!1)) :named step_0))
(rule (! (=> (and (State V U T S R Q P O N M L K J I H G F E D C B A) (not true)) Bad) :named observe_1))
(rule (! (let ((a!1 (State V U T S R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 true true) a!1)) :named step_1))
(rule (! (let ((a!1 (and (State V U T S R Q P O N M L K J I H G F E D C B A)
                (not (= (and V U) (and T S))))))
  (=> a!1 Bad)) :named observe_2))
(rule (! (=> (and (State V U T S R Q P O N M L K J I H G F E D C B A)
         (= (and V U) (and T S))
         (or (and V U) (and T S)))
    (State false
           U
           false
           S
           R
           (ite (and V U) 258 Q)
           P
           O
           N
           M
           L
           K
           (ite V 257 J)
           I
           (ite (and T S) 258 H)
           G
           F
           E
           D
           C
           B
           (ite T 257 A))) :named step_2))
(rule (! (=> (and (State V U T S R Q P O N M L K J I H G F E D C B A) (not true)) Bad) :named observe_3))
(rule (! (=> (and (State V U T S R Q P O N M L K J I H G F E D C B A) true true)
    (State V U T S R P O N M L K J J I G F E D C B A A)) :named step_3))
(rule (! (=> (and (State V U T S R Q P O N M L K J I H G F E D C B A) (not true)) Bad) :named observe_4))
(rule (! (=> (and (State V U T S R Q P O N M L K J I H G F E D C B A) true true)
    (State V U T S Q Q P O N M L K J H H G F E D C B A)) :named step_4))

(query Bad)
