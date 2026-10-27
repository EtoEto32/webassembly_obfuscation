(declare-rel Bad ())
(declare-rel State (Bool Bool Bool Bool Int Int Int Int Int Int Int Int Int Int))
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
(rule (State false false true false 257 257 257 257 258 257 257 257 257 258))
(rule (! (=> (and (State N M L K J I H G F E D C B A) (not (= J E))) Bad) :named observe_0))
(rule (! (let ((a!1 (State N M L K J I H G F E D C B A)))
  (=> (and a!1 (= J E) true) a!1)) :named step_0))
(rule (! (=> (and (State N M L K J I H G F E D C B A) (not (= J E))) Bad) :named observe_1))
(rule (! (let ((a!1 (State N M L K J I H G F E D C B A)))
  (=> (and a!1 (= J E) true) a!1)) :named step_1))
(rule (! (let ((a!1 (not (and (= (and N M) (and L K)) (= J E)))))
  (=> (and (State N M L K J I H G F E D C B A) a!1) Bad)) :named observe_2))
(rule (! (=> (and (State N M L K J I H G F E D C B A)
         (= (and N M) (and L K))
         (= J E)
         true)
    (State false
           M
           false
           K
           J
           (ite (and N M) 258 I)
           H
           G
           (ite N 257 F)
           E
           (ite (and L K) 258 D)
           C
           B
           (ite L 257 A))) :named step_2))
(rule (! (=> (and (State N M L K J I H G F E D C B A) (not (= J E))) Bad) :named observe_3))
(rule (! (=> (and (State N M L K J I H G F E D C B A) (= J E) true)
    (State N M L K J H G F F E C B A A)) :named step_3))
(rule (! (=> (and (State N M L K J I H G F E D C B A) (not true)) Bad) :named observe_4))
(rule (! (=> (and (State N M L K J I H G F E D C B A) true true)
    (State N M L K 257 257 257 257 257 257 257 257 257 257)) :named step_4))

(query Bad)
