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
(declare-var F1 Bool)
(declare-var G1 Bool)
(declare-var H1 Bool)
(declare-var I1 Bool)
(declare-var J1 Bool)
(declare-var K1 Bool)
(declare-var L1 Bool)
(declare-var M1 Bool)
(rule (State false
       true
       false
       false
       false
       false
       true
       false
       23
       4
       205
       257
       256
       23
       4
       205
       257
       256))
(rule (! (let ((a!1 (and (State R Q P O N M L K J I H G F E D C B A)
                (not (and (= J E) (= I D) (= H C))))))
  (=> a!1 Bad)) :named observe_0))
(rule (! (let ((a!1 (State R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 (= J E) (= I D) (= H C) true) a!1)) :named step_0))
(rule (! (let ((a!1 (and (State R Q P O N M L K J I H G F E D C B A)
                (not (and (= J E) (= I D) (= H C))))))
  (=> a!1 Bad)) :named observe_1))
(rule (! (let ((a!1 (State R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 (= J E) (= I D) (= H C) true) a!1)) :named step_1))
(rule (! (let ((a!1 (store (store (store ((as const (Array Int Int)) 0) 0 J) 1 I) 2 H))
      (a!3 (store (store (store ((as const (Array Int Int)) 0) 0 E) 1 D) 2 C)))
(let ((a!2 (ite P
                (store (store a!1 8589934593 F) 8589934592 257)
                (store (store a!1 8589934592 G) 8589934593 F)))
      (a!4 (ite L
                (store (store a!3 8589934593 A) 8589934592 257)
                (store (store a!3 8589934592 B) 8589934593 A))))
(let ((a!5 (= (select (ite (and P O) (store a!2 8589934593 258) a!2) 1)
              (select (ite (and L K) (store a!4 8589934593 258) a!4) 1)))
      (a!6 (= (select (ite (and P O) (store a!2 8589934593 258) a!2) 2)
              (select (ite (and L K) (store a!4 8589934593 258) a!4) 2))))
(let ((a!7 (not (and (= (select a!2 0) (select a!4 0)) a!5 a!6))))
  (=> (and (State R Q P O N M L K J I H G F E D C B A) a!7) Bad))))) :named observe_2))
(rule (! (let ((a!1 (store (store (store ((as const (Array Int Int)) 0) 0 J) 1 I) 2 H))
      (a!3 (store (store (store ((as const (Array Int Int)) 0) 0 E) 1 D) 2 C)))
(let ((a!2 (ite P
                (store (store a!1 8589934593 F) 8589934592 257)
                (store (store a!1 8589934592 G) 8589934593 F)))
      (a!4 (ite L
                (store (store a!3 8589934593 A) 8589934592 257)
                (store (store a!3 8589934592 B) 8589934593 A))))
(let ((a!5 (= (select (ite (and P O) (store a!2 8589934593 258) a!2) 1)
              (select (ite (and L K) (store a!4 8589934593 258) a!4) 1)))
      (a!6 (= (select (ite (and P O) (store a!2 8589934593 258) a!2) 2)
              (select (ite (and L K) (store a!4 8589934593 258) a!4) 2)))
      (a!7 (State (and (not (and P O)) R)
                  Q
                  false
                  O
                  (and (not (and L K)) N)
                  M
                  false
                  K
                  (select a!2 0)
                  (select a!2 1)
                  (select a!2 2)
                  (select a!2 8589934592)
                  (ite (and P O) 258 (select a!2 8589934593))
                  (select a!4 0)
                  (select a!4 1)
                  (select a!4 2)
                  (select a!4 8589934592)
                  (ite (and L K) 258 (select a!4 8589934593)))))
  (=> (and (State R Q P O N M L K J I H G F E D C B A)
           (= (select a!2 0) (select a!4 0))
           a!5
           a!6
           false)
      a!7)))) :named step_2))
(rule (! (let ((a!1 (and (State R Q P O N M L K J I H G F E D C B A)
                (not (and (= J E) (= I D) (= H C))))))
  (=> a!1 Bad)) :named observe_3))
(rule (! (=> (and (State R Q P O N M L K J I H G F E D C B A)
         (= J E)
         (= I D)
         (= H C)
         false)
    (State false Q false O false M false K J I H G F E D C B A)) :named step_3))
(rule (! (let ((a!1 (and (State R Q P O N M L K J I H G F E D C B A)
                (not (and (= J E) (= I D) (= H C))))))
  (=> a!1 Bad)) :named observe_4))
(rule (! (let ((a!1 (State R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 (= J E) (= I D) (= H C) false) a!1)) :named step_4))
(rule (! (let ((a!1 (and (State R Q P O N M L K J I H G F E D C B A)
                (not (and (= J E) (= I D) (= H C))))))
  (=> a!1 Bad)) :named observe_5))
(rule (! (let ((a!1 (State R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 (= J E) (= I D) (= H C) true) a!1)) :named step_5))
(rule (! (=> (and (State R Q P O N M L K U T S J I H G F E D)
         (>= C 0)
         (<= C 255)
         (>= B 0)
         (<= B 255)
         (>= A 0)
         (<= A 255))
    (State R Q P O N M L K C B A J I C B A E D)) :named common_public_assignment))

(query Bad)
