(declare-rel State (Bool Bool Bool Bool Bool Bool Bool Bool Int Int Int Int Int Int Int Int))
(declare-rel Bad ())
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
(declare-var M Bool)
(declare-var N Bool)
(declare-var O Bool)
(declare-var P Bool)
(declare-var Q Int)
(declare-var R Int)
(declare-var S Int)
(declare-var T Int)
(declare-var U Int)
(declare-var V Int)
(declare-var W Int)
(declare-var X Int)
(declare-var Y Int)
(declare-var Z Bool)
(declare-var A1 Bool)
(declare-var B1 Bool)
(declare-var C1 Bool)
(declare-var D1 Bool)
(declare-var E1 Bool)
(declare-var F1 Bool)
(declare-var G1 Bool)
(rule (State false
       true
       false
       false
       false
       true
       true
       false
       258
       257
       256
       258
       258
       257
       256
       258))
(rule (! (let ((a!1 (and (State P O N M L K J I H G F E D C B A)
                (not (and (= H D) (= G C) (= F B) (= E A))))))
  (=> a!1 Bad)) :named observe_0))
(rule (! (let ((a!1 (State P O N M L K J I H G F E D C B A)))
  (=> (and a!1 (= H D) (= G C) (= F B) (= E A) true) a!1)) :named step_0))
(rule (! (let ((a!1 (and (State P O N M L K J I H G F E D C B A)
                (not (and (= H D) (= G C) (= F B) (= E A))))))
  (=> a!1 Bad)) :named observe_1))
(rule (! (let ((a!1 (State P O N M L K J I H G F E D C B A)))
  (=> (and a!1 (= H D) (= G C) (= F B) (= E A) true) a!1)) :named step_1))
(rule (! (let ((a!1 (store (store (store ((as const (Array Int Int)) 0) 4294967298 H)
                         8589934593
                         F)
                  8589934594
                  E))
      (a!2 (store (store (store ((as const (Array Int Int)) 0) 4294967298 H)
                         8589934592
                         G)
                  8589934593
                  F))
      (a!4 (store (store (store ((as const (Array Int Int)) 0) 4294967298 D)
                         8589934593
                         B)
                  8589934594
                  A))
      (a!5 (store (store (store ((as const (Array Int Int)) 0) 4294967298 D)
                         8589934592
                         C)
                  8589934593
                  B)))
(let ((a!3 (ite N (store a!1 8589934592 257) (store a!2 8589934594 E)))
      (a!6 (ite J (store a!4 8589934592 257) (store a!5 8589934594 A))))
(let ((a!7 (= (select (ite (and N M) (store a!3 8589934593 258) a!3) 8589934592)
              (select (ite (and J I) (store a!6 8589934593 258) a!6) 8589934592)))
      (a!8 (= (select (ite (and N M) (store a!3 8589934593 258) a!3) 8589934593)
              (select (ite (and J I) (store a!6 8589934593 258) a!6) 8589934593)))
      (a!9 (= (select (ite (and N M) (store a!3 8589934593 258) a!3) 8589934594)
              (select (ite (and J I) (store a!6 8589934593 258) a!6) 8589934594))))
(let ((a!10 (not (and (= (and N M P) (and J I L))
                      (= (select a!3 4294967298) (select a!6 4294967298))
                      a!7
                      a!8
                      a!9))))
  (=> (and (State P O N M L K J I H G F E D C B A) a!10) Bad))))) :named observe_2))
(rule (! (let ((a!1 (store (store (store ((as const (Array Int Int)) 0) 4294967298 H)
                         8589934593
                         F)
                  8589934594
                  E))
      (a!2 (store (store (store ((as const (Array Int Int)) 0) 4294967298 H)
                         8589934592
                         G)
                  8589934593
                  F))
      (a!4 (store (store (store ((as const (Array Int Int)) 0) 4294967298 D)
                         8589934593
                         B)
                  8589934594
                  A))
      (a!5 (store (store (store ((as const (Array Int Int)) 0) 4294967298 D)
                         8589934592
                         C)
                  8589934593
                  B)))
(let ((a!3 (ite N (store a!1 8589934592 257) (store a!2 8589934594 E)))
      (a!6 (ite J (store a!4 8589934592 257) (store a!5 8589934594 A))))
(let ((a!7 (= (select (ite (and N M) (store a!3 8589934593 258) a!3) 8589934592)
              (select (ite (and J I) (store a!6 8589934593 258) a!6) 8589934592)))
      (a!8 (= (select (ite (and N M) (store a!3 8589934593 258) a!3) 8589934593)
              (select (ite (and J I) (store a!6 8589934593 258) a!6) 8589934593)))
      (a!9 (= (select (ite (and N M) (store a!3 8589934593 258) a!3) 8589934594)
              (select (ite (and J I) (store a!6 8589934593 258) a!6) 8589934594))))
  (=> (and (State P O N M L K J I H G F E D C B A)
           (= (and N M P) (and J I L))
           (= (select a!3 4294967298) (select a!6 4294967298))
           a!7
           a!8
           a!9
           (or (and N M P) (and J I L)))
      (State P
             O
             false
             M
             L
             K
             false
             I
             (select a!3 4294967298)
             (select a!3 8589934592)
             (ite (and N M) 258 (select a!3 8589934593))
             (select a!3 8589934594)
             (select a!6 4294967298)
             (select a!6 8589934592)
             (ite (and J I) 258 (select a!6 8589934593))
             (select a!6 8589934594)))))) :named step_2))
(rule (! (let ((a!1 (and (State P O N M L K J I H G F E D C B A)
                (not (and (= G C) (= F B) (= E A))))))
  (=> a!1 Bad)) :named observe_3))
(rule (! (=> (and (State P O N M L K J I H G F E D C B A) (= G C) (= F B) (= E A) true)
    (State P O N M L K J I 256 G F E 256 C B A)) :named step_3))
(rule (! (let ((a!1 (and (State P O N M L K J I H G F E D C B A)
                (not (and (= H D) (= G C) (= F B) (= E A))))))
  (=> a!1 Bad)) :named observe_4))
(rule (! (=> (and (State P O N M L K J I H G F E D C B A)
         (= H D)
         (= G C)
         (= F B)
         (= E A)
         false)
    (State P O false M L K false I H G F E D C B A)) :named step_4))
(rule (! (let ((a!1 (and (State P O N M L K J I H G F E D C B A)
                (not (and (= H D) (= G C) (= F B) (= E A))))))
  (=> a!1 Bad)) :named observe_5))
(rule (! (let ((a!1 (State P O N M L K J I H G F E D C B A)))
  (=> (and a!1 (= H D) (= G C) (= F B) (= E A) true) a!1)) :named step_5))
(rule (! (=> (and (State P O N M L K J I Q H G F E D C B) (>= A 256))
    (State P O N M L K J I A H G F A D C B)) :named common_public_assignment))

(query Bad)
