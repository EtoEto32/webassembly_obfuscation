(declare-rel State (Bool Bool Bool Bool Int Int Int Int))
(declare-rel Bad ())
(declare-var A Int)
(declare-var B Int)
(declare-var C Int)
(declare-var D Int)
(declare-var E Bool)
(declare-var F Bool)
(declare-var G Bool)
(declare-var H Bool)
(rule (State false false true false 257 258 257 258))
(rule (! (=> (and (State H G F E D C B A) (not (= D B))) Bad) :named observe_0))
(rule (! (=> (and (State H G F E D C B A) (= D B) true) (State H G F E D C B A)) :named step_0))
(rule (! (=> (and (State H G F E D C B A) (not (= D B))) Bad) :named observe_1))
(rule (! (=> (and (State H G F E D C B A) (= D B) true) (State H G F E D C B A)) :named step_1))
(rule (! (let ((a!1 (not (and (= (and H G) (and F E)) (= D B)))))
  (=> (and (State H G F E D C B A) a!1) Bad)) :named observe_2))
(rule (! (=> (and (State H G F E D C B A)
         (= (and H G) (and F E))
         (= D B)
         (or (and H G) (and F E)))
    (State false
           G
           false
           E
           D
           (ite (and H G) 258 (ite H 257 C))
           B
           (ite (and F E) 258 (ite F 257 A)))) :named step_2))
(rule (! (=> (and (State H G F E D C B A) (not (= D B))) Bad) :named observe_3))
(rule (! (=> (and (State H G F E D C B A) (= D B) true) (State H G F E D C B A)) :named step_3))
(rule (! (=> (and (State H G F E D C B A) (not (= C A))) Bad) :named observe_4))
(rule (! (=> (and (State H G F E D C B A) (= C A) true) (State H G F E C C A A)) :named step_4))

(query Bad)
