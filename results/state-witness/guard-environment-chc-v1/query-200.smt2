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
(declare-var O Int)
(declare-var P Int)
(declare-var Q Int)
(declare-var R Int)
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
(rule (State false false true false 258 257 256 258 256 258 257 256 258 256))
(rule (! (let ((a!1 (and (State N M L K J I H G F E D C B A)
                (not (and (= I D) (= H C) (= G B) (= F A))))))
  (=> a!1 Bad)) :named observe_0))
(rule (! (let ((a!1 (State N M L K J I H G F E D C B A)))
  (=> (and a!1 (= I D) (= H C) (= G B) (= F A) true) a!1)) :named step_0))
(rule (! (let ((a!1 (and (State N M L K J I H G F E D C B A)
                (not (and (= I D) (= H C) (= G B) (= F A))))))
  (=> a!1 Bad)) :named observe_1))
(rule (! (let ((a!1 (State N M L K J I H G F E D C B A)))
  (=> (and a!1 (= I D) (= H C) (= G B) (= F A) true) a!1)) :named step_1))
(rule (! (let ((a!1 (store (store (store ((as const (Array Int Int)) 0) 4294967299 J)
                         8589934593
                         H)
                  8589934594
                  G))
      (a!2 (store (store (store ((as const (Array Int Int)) 0) 4294967299 J)
                         8589934592
                         I)
                  8589934593
                  H))
      (a!4 (store (store (store ((as const (Array Int Int)) 0) 4294967299 E)
                         8589934593
                         C)
                  8589934594
                  B))
      (a!5 (store (store (store ((as const (Array Int Int)) 0) 4294967299 E)
                         8589934592
                         D)
                  8589934593
                  C)))
(let ((a!3 (ite N
                (store (store a!1 8589934595 F) 8589934592 257)
                (store (store a!2 8589934594 G) 8589934595 F)))
      (a!6 (ite L
                (store (store a!4 8589934595 A) 8589934592 257)
                (store (store a!5 8589934594 B) 8589934595 A))))
(let ((a!7 (= (select (ite (and N M) (store a!3 8589934593 258) a!3) 8589934593)
              (select (ite (and L K) (store a!6 8589934593 258) a!6) 8589934593)))
      (a!8 (= (select (ite (and N M) (store a!3 8589934593 258) a!3) 8589934594)
              (select (ite (and L K) (store a!6 8589934593 258) a!6) 8589934594)))
      (a!9 (= (select (ite (and N M) (store a!3 8589934593 258) a!3) 8589934595)
              (select (ite (and L K) (store a!6 8589934593 258) a!6) 8589934595))))
(let ((a!10 (not (and (= (select a!3 8589934592) (select a!6 8589934592))
                      a!7
                      a!8
                      a!9))))
  (=> (and (State N M L K J I H G F E D C B A) a!10) Bad))))) :named observe_2))
(rule (! (let ((a!1 (store (store (store ((as const (Array Int Int)) 0) 4294967299 J)
                         8589934593
                         H)
                  8589934594
                  G))
      (a!2 (store (store (store ((as const (Array Int Int)) 0) 4294967299 J)
                         8589934592
                         I)
                  8589934593
                  H))
      (a!4 (store (store (store ((as const (Array Int Int)) 0) 4294967299 E)
                         8589934593
                         C)
                  8589934594
                  B))
      (a!5 (store (store (store ((as const (Array Int Int)) 0) 4294967299 E)
                         8589934592
                         D)
                  8589934593
                  C)))
(let ((a!3 (ite N
                (store (store a!1 8589934595 F) 8589934592 257)
                (store (store a!2 8589934594 G) 8589934595 F)))
      (a!6 (ite L
                (store (store a!4 8589934595 A) 8589934592 257)
                (store (store a!5 8589934594 B) 8589934595 A))))
(let ((a!7 (= (select (ite (and N M) (store a!3 8589934593 258) a!3) 8589934593)
              (select (ite (and L K) (store a!6 8589934593 258) a!6) 8589934593)))
      (a!8 (= (select (ite (and N M) (store a!3 8589934593 258) a!3) 8589934594)
              (select (ite (and L K) (store a!6 8589934593 258) a!6) 8589934594)))
      (a!9 (= (select (ite (and N M) (store a!3 8589934593 258) a!3) 8589934595)
              (select (ite (and L K) (store a!6 8589934593 258) a!6) 8589934595))))
  (=> (and (State N M L K J I H G F E D C B A)
           (= (select a!3 8589934592) (select a!6 8589934592))
           a!7
           a!8
           a!9
           true)
      (State false
             M
             false
             K
             (select a!3 4294967299)
             (select a!3 8589934592)
             (ite (and N M) 258 (select a!3 8589934593))
             (select a!3 8589934594)
             (select a!3 8589934595)
             (select a!6 4294967299)
             (select a!6 8589934592)
             (ite (and L K) 258 (select a!6 8589934593))
             (select a!6 8589934594)
             (select a!6 8589934595)))))) :named step_2))
(rule (! (let ((a!1 (and (State N M L K J I H G F E D C B A)
                (not (and (= I D) (= H C) (= G B) (= F A))))))
  (=> a!1 Bad)) :named observe_3))
(rule (! (let ((a!1 (State N M L K J I H G F E D C B A)))
  (=> (and a!1 (= I D) (= H C) (= G B) (= F A) true) a!1)) :named step_3))
(rule (! (let ((a!1 (store (store (store ((as const (Array Int Int)) 0) 8589934592 I)
                         8589934593
                         H)
                  8589934594
                  G))
      (a!2 (store (store (store ((as const (Array Int Int)) 0) 4294967299 J)
                         8589934592
                         I)
                  8589934593
                  H))
      (a!4 (store (store (store ((as const (Array Int Int)) 0) 8589934592 D)
                         8589934593
                         C)
                  8589934594
                  B))
      (a!5 (store (store (store ((as const (Array Int Int)) 0) 4294967299 E)
                         8589934592
                         D)
                  8589934593
                  C)))
(let ((a!3 (ite M
                (store (store a!1 8589934595 F) 4294967299 257)
                (store (store a!2 8589934594 G) 8589934595 F)))
      (a!6 (ite K
                (store (store a!4 8589934595 A) 4294967299 257)
                (store (store a!5 8589934594 B) 8589934595 A))))
(let ((a!7 (not (and (= M K)
                     (= (select a!3 8589934592) (select a!6 8589934592))
                     (= (select a!3 8589934593) (select a!6 8589934593))
                     (= (select a!3 8589934594) (select a!6 8589934594))
                     (= (select a!3 8589934595) (select a!6 8589934595))))))
  (=> (and (State N M L K J I H G F E D C B A) a!7) Bad)))) :named observe_4))
(rule (! (let ((a!1 (store (store (store ((as const (Array Int Int)) 0) 8589934592 I)
                         8589934593
                         H)
                  8589934594
                  G))
      (a!2 (store (store (store ((as const (Array Int Int)) 0) 4294967299 J)
                         8589934592
                         I)
                  8589934593
                  H))
      (a!4 (store (store (store ((as const (Array Int Int)) 0) 8589934592 D)
                         8589934593
                         C)
                  8589934594
                  B))
      (a!5 (store (store (store ((as const (Array Int Int)) 0) 4294967299 E)
                         8589934592
                         D)
                  8589934593
                  C)))
(let ((a!3 (ite M
                (store (store a!1 8589934595 F) 4294967299 257)
                (store (store a!2 8589934594 G) 8589934595 F)))
      (a!6 (ite K
                (store (store a!4 8589934595 A) 4294967299 257)
                (store (store a!5 8589934594 B) 8589934595 A))))
  (=> (and (State N M L K J I H G F E D C B A)
           (= M K)
           (= (select a!3 8589934592) (select a!6 8589934592))
           (= (select a!3 8589934593) (select a!6 8589934593))
           (= (select a!3 8589934594) (select a!6 8589934594))
           (= (select a!3 8589934595) (select a!6 8589934595))
           true)
      (State N
             M
             L
             K
             (select a!3 4294967299)
             (select a!3 8589934592)
             (select a!3 8589934593)
             (select a!3 8589934594)
             (select a!3 8589934595)
             (select a!6 4294967299)
             (select a!6 8589934592)
             (select a!6 8589934593)
             (select a!6 8589934594)
             (select a!6 8589934595))))) :named step_4))
(rule (! (=> (and (State N M L K R Q P O J I H G F E)
         (>= D 256)
         (>= C 256)
         (>= B 256)
         (>= A 256))
    (State N M L K R D C B A I D C B A)) :named common_public_assignment))

(query Bad)
