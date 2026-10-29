(declare-rel State (Bool Bool Bool Bool Bool Bool Bool Bool Int Int Int Int Int Int))
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
(declare-var K Bool)
(declare-var L Bool)
(declare-var M Bool)
(declare-var N Bool)
(declare-var O Int)
(declare-var P Int)
(declare-var Q Int)
(declare-var R Int)
(declare-var S Int)
(declare-var T Int)
(declare-var U Int)
(declare-var V Bool)
(declare-var W Bool)
(declare-var X Bool)
(declare-var Y Bool)
(declare-var Z Bool)
(declare-var A1 Bool)
(declare-var B1 Bool)
(declare-var C1 Bool)
(rule (State false false false false false false true false 151 258 256 151 258 256))
(rule (! (=> (and (State N M L K J I H G F E D C B A) (not (= F C))) Bad) :named observe_0))
(rule (! (let ((a!1 (State N M L K J I H G F E D C B A)))
  (=> (and a!1 (= F C) true) a!1)) :named step_0))
(rule (! (=> (and (State N M L K J I H G F E D C B A) (not (= F C))) Bad) :named observe_1))
(rule (! (let ((a!1 (State N M L K J I H G F E D C B A)))
  (=> (and a!1 (= F C) true) a!1)) :named step_1))
(rule (! (let ((a!1 (store (store (store ((as const (Array Int Int)) 0) 3 F)
                         8589934593
                         D)
                  8589934592
                  257))
      (a!2 (store (store (store ((as const (Array Int Int)) 0) 3 F)
                         8589934592
                         E)
                  8589934593
                  D))
      (a!4 (store (store (store ((as const (Array Int Int)) 0) 3 C)
                         8589934593
                         A)
                  8589934592
                  257))
      (a!5 (store (store (store ((as const (Array Int Int)) 0) 3 C)
                         8589934592
                         B)
                  8589934593
                  A)))
(let ((a!3 (store (ite (and L K)
                       (store (ite L a!1 a!2) 8589934593 258)
                       (ite L a!1 a!2))
                  3
                  255))
      (a!6 (store (ite (and H G)
                       (store (ite H a!4 a!5) 8589934593 258)
                       (ite H a!4 a!5))
                  3
                  255)))
(let ((a!7 (= (select (ite (and L K) a!3 (ite L a!1 a!2)) 3)
              (select (ite (and H G) a!6 (ite H a!4 a!5)) 3))))
(let ((a!8 (not (and (= (and L K) (and H G)) a!7))))
  (=> (and (State N M L K J I H G F E D C B A) a!8) Bad))))) :named observe_2))
(rule (! (let ((a!1 (store (store (store ((as const (Array Int Int)) 0) 3 F)
                         8589934593
                         D)
                  8589934592
                  257))
      (a!2 (store (store (store ((as const (Array Int Int)) 0) 3 F)
                         8589934592
                         E)
                  8589934593
                  D))
      (a!5 (store (store (store ((as const (Array Int Int)) 0) 3 C)
                         8589934593
                         A)
                  8589934592
                  257))
      (a!6 (store (store (store ((as const (Array Int Int)) 0) 3 C)
                         8589934592
                         B)
                  8589934593
                  A)))
(let ((a!3 (store (ite (and L K)
                       (store (ite L a!1 a!2) 8589934593 258)
                       (ite L a!1 a!2))
                  3
                  255))
      (a!7 (store (ite (and H G)
                       (store (ite H a!5 a!6) 8589934593 258)
                       (ite H a!5 a!6))
                  3
                  255)))
(let ((a!4 (select (ite (and L K) a!3 (ite L a!1 a!2)) 3))
      (a!8 (select (ite (and H G) a!7 (ite H a!5 a!6)) 3)))
(let ((a!9 (State N
                  M
                  false
                  K
                  J
                  I
                  false
                  G
                  a!4
                  (select (ite (and L K) a!3 (ite L a!1 a!2)) 8589934592)
                  (select (ite (and L K) a!3 (ite L a!1 a!2)) 8589934593)
                  a!8
                  (select (ite (and H G) a!7 (ite H a!5 a!6)) 8589934592)
                  (select (ite (and H G) a!7 (ite H a!5 a!6)) 8589934593))))
  (=> (and (State N M L K J I H G F E D C B A)
           (= (and L K) (and H G))
           (= a!4 a!8)
           (or (and L K) (and H G)))
      a!9))))) :named step_2))
(rule (! (=> (and (State N M L K J I H G F E D C B A) (not (= F C))) Bad) :named observe_3))
(rule (! (let ((a!1 (State N M L K J I H G F E D C B A)))
  (=> (and a!1 (= F C) true) a!1)) :named step_3))
(rule (! (=> (and (State N M L K J I H G F E D C B A) (not (= F C))) Bad) :named observe_4))
(rule (! (=> (and (State N M L K J I H G F E D C B A) (= F C) false)
    (State N false L false J false H false F E D C B A)) :named step_4))
(rule (! (=> (and (State N M L K J I H G F E D C B A) (not (= F C))) Bad) :named observe_5))
(rule (! (let ((a!1 (State N M L K J I H G F E D C B A)))
  (=> (and a!1 (= F C) true) a!1)) :named step_5))
(rule (! (=> (and (State N M L K J I H G O F E D C B) (>= A 0) (<= A 255))
    (State N M L K J I H G A F E A C B)) :named common_public_assignment))

(query Bad)
