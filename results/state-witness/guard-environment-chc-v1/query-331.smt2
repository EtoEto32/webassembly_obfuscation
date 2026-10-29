(declare-rel Bad ())
(declare-rel State (Bool Bool Bool Bool Int Int Int Int Int Int Int Int))
(declare-var A Int)
(declare-var B Int)
(declare-var C Int)
(declare-var D Int)
(declare-var E Int)
(declare-var F Int)
(declare-var G Int)
(declare-var H Int)
(declare-var I Bool)
(declare-var J Bool)
(declare-var K Bool)
(declare-var L Bool)
(declare-var M Int)
(declare-var N Int)
(declare-var O Int)
(declare-var P Int)
(declare-var Q Int)
(declare-var R Int)
(declare-var S Int)
(declare-var T Int)
(declare-var U Int)
(declare-var V Int)
(declare-var W Bool)
(declare-var X Bool)
(declare-var Y Bool)
(declare-var Z Bool)
(rule (State false false true false 258 256 257 256 258 256 257 256))
(rule (! (let ((a!1 (and (State L K J I H G F E D C B A)
                (not (and (= H D) (= G C) (= F B) (= E A))))))
  (=> a!1 Bad)) :named observe_0))
(rule (! (let ((a!1 (State L K J I H G F E D C B A)))
  (=> (and a!1 (= H D) (= G C) (= F B) (= E A) true) a!1)) :named step_0))
(rule (! (let ((a!1 (and (State L K J I H G F E D C B A)
                (not (and (= H D) (= G C) (= F B) (= E A))))))
  (=> a!1 Bad)) :named observe_1))
(rule (! (let ((a!1 (State L K J I H G F E D C B A)))
  (=> (and a!1 (= H D) (= G C) (= F B) (= E A) true) a!1)) :named step_1))
(rule (! (let ((a!1 (store (store (store ((as const (Array Int Int)) 0) 4294967298 H)
                         4294967299
                         G)
                  8589934593
                  E))
      (a!2 (store (store (store ((as const (Array Int Int)) 0) 4294967298 H)
                         4294967299
                         G)
                  8589934592
                  F))
      (a!4 (store (store (store ((as const (Array Int Int)) 0) 4294967298 D)
                         4294967299
                         C)
                  8589934593
                  A))
      (a!5 (store (store (store ((as const (Array Int Int)) 0) 4294967298 D)
                         4294967299
                         C)
                  8589934592
                  B)))
(let ((a!3 (ite L (store a!1 8589934592 257) (store a!2 8589934593 E)))
      (a!6 (ite J (store a!4 8589934592 257) (store a!5 8589934593 A))))
(let ((a!7 (= (select (ite (and L K) (store a!3 8589934593 258) a!3) 4294967299)
              (select (ite (and J I) (store a!6 8589934593 258) a!6) 4294967299)))
      (a!8 (= (select (ite (and L K) (store a!3 8589934593 258) a!3) 8589934592)
              (select (ite (and J I) (store a!6 8589934593 258) a!6) 8589934592)))
      (a!9 (= (select (ite (and L K) (store a!3 8589934593 258) a!3) 8589934593)
              (select (ite (and J I) (store a!6 8589934593 258) a!6) 8589934593))))
(let ((a!10 (not (and (= (select a!3 4294967298) (select a!6 4294967298))
                      a!7
                      a!8
                      a!9))))
  (=> (and (State L K J I H G F E D C B A) a!10) Bad))))) :named observe_2))
(rule (! (let ((a!1 (store (store (store ((as const (Array Int Int)) 0) 4294967298 H)
                         4294967299
                         G)
                  8589934593
                  E))
      (a!2 (store (store (store ((as const (Array Int Int)) 0) 4294967298 H)
                         4294967299
                         G)
                  8589934592
                  F))
      (a!4 (store (store (store ((as const (Array Int Int)) 0) 4294967298 D)
                         4294967299
                         C)
                  8589934593
                  A))
      (a!5 (store (store (store ((as const (Array Int Int)) 0) 4294967298 D)
                         4294967299
                         C)
                  8589934592
                  B)))
(let ((a!3 (ite L (store a!1 8589934592 257) (store a!2 8589934593 E)))
      (a!6 (ite J (store a!4 8589934592 257) (store a!5 8589934593 A))))
(let ((a!7 (= (select (ite (and L K) (store a!3 8589934593 258) a!3) 4294967299)
              (select (ite (and J I) (store a!6 8589934593 258) a!6) 4294967299)))
      (a!8 (= (select (ite (and L K) (store a!3 8589934593 258) a!3) 8589934592)
              (select (ite (and J I) (store a!6 8589934593 258) a!6) 8589934592)))
      (a!9 (= (select (ite (and L K) (store a!3 8589934593 258) a!3) 8589934593)
              (select (ite (and J I) (store a!6 8589934593 258) a!6) 8589934593))))
  (=> (and (State L K J I H G F E D C B A)
           (= (select a!3 4294967298) (select a!6 4294967298))
           a!7
           a!8
           a!9
           false)
      (State false
             K
             false
             I
             (select a!3 4294967298)
             (select a!3 4294967299)
             (select a!3 8589934592)
             (ite (and L K) 258 (select a!3 8589934593))
             (select a!6 4294967298)
             (select a!6 4294967299)
             (select a!6 8589934592)
             (ite (and J I) 258 (select a!6 8589934593))))))) :named step_2))
(rule (! (let ((a!1 (and (State L K J I H G F E D C B A)
                (not (and (= H D) (= G C) (= F B) (= E A))))))
  (=> a!1 Bad)) :named observe_3))
(rule (! (let ((a!1 (State L K J I H G F E D C B A)))
  (=> (and a!1 (= H D) (= G C) (= F B) (= E A) false) a!1)) :named step_3))
(rule (! (let ((a!1 (and (State L K J I H G F E D C B A)
                (not (and (= H D) (= G C) (= F B) (= E A))))))
  (=> a!1 Bad)) :named observe_4))
(rule (! (let ((a!1 (State L K J I H G F E D C B A)))
  (=> (and a!1 (= H D) (= G C) (= F B) (= E A) false) a!1)) :named step_4))
(rule (! (=> (and (State L K J I N M H G F E D C) (>= B 256) (>= A 256))
    (State L K J I B A H G B A D C)) :named common_public_assignment))

(query Bad)
