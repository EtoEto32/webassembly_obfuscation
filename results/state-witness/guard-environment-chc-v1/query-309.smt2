(declare-rel State (Bool Bool Bool Bool Int Int Int Int Int Int Int Int Int Int Int Int Int Int))
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
(declare-var F1 Int)
(declare-var G1 Int)
(declare-var H1 Int)
(declare-var I1 Int)
(declare-var J1 Int)
(declare-var K1 Bool)
(declare-var L1 Bool)
(declare-var M1 Bool)
(declare-var N1 Bool)
(rule (State false
       false
       true
       false
       256
       258
       256
       256
       256
       258
       257
       256
       258
       256
       256
       256
       258
       257))
(rule (! (let ((a!1 (and (State R Q P O N M L K J I H G F E D C B A)
                (not (and (= N G) (= M F) (= L E) (= K D))))))
  (=> a!1 Bad)) :named observe_0))
(rule (! (let ((a!1 (State R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 (= N G) (= M F) (= L E) (= K D) true) a!1)) :named step_0))
(rule (! (let ((a!1 (and (State R Q P O N M L K J I H G F E D C B A)
                (not (and (= N G) (= M F) (= L E) (= K D))))))
  (=> a!1 Bad)) :named observe_1))
(rule (! (let ((a!1 (State R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 (= N G) (= M F) (= L E) (= K D) true) a!1)) :named step_1))
(rule (! (let ((a!1 (store (store (store ((as const (Array Int Int)) 0) 4294967296 N)
                         4294967297
                         M)
                  4294967298
                  L))
      (a!5 (store (store (store ((as const (Array Int Int)) 0) 4294967296 G)
                         4294967297
                         F)
                  4294967298
                  E)))
(let ((a!2 (store (store (store (store a!1 4294967299 K) 8589934593 I)
                         8589934594
                         H)
                  8589934592
                  257))
      (a!3 (store (store (store (store a!1 4294967299 K) 8589934592 J)
                         8589934593
                         I)
                  8589934594
                  H))
      (a!6 (store (store (store (store a!5 4294967299 D) 8589934593 B)
                         8589934594
                         A)
                  8589934592
                  257))
      (a!7 (store (store (store (store a!5 4294967299 D) 8589934592 C)
                         8589934593
                         B)
                  8589934594
                  A)))
(let ((a!4 (ite (and R Q)
                (store (ite R a!2 a!3) 8589934593 258)
                (ite R a!2 a!3)))
      (a!8 (ite (and P O)
                (store (ite P a!6 a!7) 8589934593 258)
                (ite P a!6 a!7))))
(let ((a!9 (not (and (= (select a!4 4294967296) (select a!8 4294967296))
                     (= (select a!4 4294967297) (select a!8 4294967297))
                     (= (select a!4 4294967298) (select a!8 4294967298))
                     (= (select a!4 4294967299) (select a!8 4294967299))))))
  (=> (and (State R Q P O N M L K J I H G F E D C B A) a!9) Bad))))) :named observe_2))
(rule (! (let ((a!1 (store (store (store ((as const (Array Int Int)) 0) 4294967296 N)
                         4294967297
                         M)
                  4294967298
                  L))
      (a!5 (store (store (store ((as const (Array Int Int)) 0) 4294967296 G)
                         4294967297
                         F)
                  4294967298
                  E)))
(let ((a!2 (store (store (store (store a!1 4294967299 K) 8589934593 I)
                         8589934594
                         H)
                  8589934592
                  257))
      (a!3 (store (store (store (store a!1 4294967299 K) 8589934592 J)
                         8589934593
                         I)
                  8589934594
                  H))
      (a!6 (store (store (store (store a!5 4294967299 D) 8589934593 B)
                         8589934594
                         A)
                  8589934592
                  257))
      (a!7 (store (store (store (store a!5 4294967299 D) 8589934592 C)
                         8589934593
                         B)
                  8589934594
                  A)))
(let ((a!4 (ite (and R Q)
                (store (ite R a!2 a!3) 8589934593 258)
                (ite R a!2 a!3)))
      (a!8 (ite (and P O)
                (store (ite P a!6 a!7) 8589934593 258)
                (ite P a!6 a!7))))
  (=> (and (State R Q P O N M L K J I H G F E D C B A)
           (= (select a!4 4294967296) (select a!8 4294967296))
           (= (select a!4 4294967297) (select a!8 4294967297))
           (= (select a!4 4294967298) (select a!8 4294967298))
           (= (select a!4 4294967299) (select a!8 4294967299))
           false)
      (State false
             Q
             false
             O
             (select a!4 4294967296)
             (select a!4 4294967297)
             (select a!4 4294967298)
             (select a!4 4294967299)
             (select a!4 8589934592)
             (select a!4 8589934593)
             (select a!4 8589934594)
             (select a!8 4294967296)
             (select a!8 4294967297)
             (select a!8 4294967298)
             (select a!8 4294967299)
             (select a!8 8589934592)
             (select a!8 8589934593)
             (select a!8 8589934594)))))) :named step_2))
(rule (! (let ((a!1 (store (store (store ((as const (Array Int Int)) 0) 4294967296 N)
                         4294967298
                         L)
                  4294967299
                  K))
      (a!3 (store (store (store ((as const (Array Int Int)) 0) 4294967296 N)
                         4294967297
                         M)
                  4294967298
                  L))
      (a!5 (store (store (store ((as const (Array Int Int)) 0) 4294967296 G)
                         4294967298
                         E)
                  4294967299
                  D))
      (a!7 (store (store (store ((as const (Array Int Int)) 0) 4294967296 G)
                         4294967297
                         F)
                  4294967298
                  E)))
(let ((a!2 (store (store (store (store a!1 8589934592 J) 8589934593 I)
                         8589934594
                         H)
                  4294967297
                  258))
      (a!4 (store (store (store (store a!3 4294967299 K) 8589934592 J)
                         8589934593
                         I)
                  8589934594
                  H))
      (a!6 (store (store (store (store a!5 8589934592 C) 8589934593 B)
                         8589934594
                         A)
                  4294967297
                  258))
      (a!8 (store (store (store (store a!7 4294967299 D) 8589934592 C)
                         8589934593
                         B)
                  8589934594
                  A)))
(let ((a!9 (and (= (select (ite R a!2 a!4) 4294967296)
                   (select (ite P a!6 a!8) 4294967296))
                (= (select (ite R a!2 a!4) 4294967297)
                   (select (ite P a!6 a!8) 4294967297))
                (= (select (ite R a!2 a!4) 4294967298)
                   (select (ite P a!6 a!8) 4294967298))
                (= (select (ite R a!2 a!4) 4294967299)
                   (select (ite P a!6 a!8) 4294967299)))))
  (=> (and (State R Q P O N M L K J I H G F E D C B A) (not a!9)) Bad)))) :named observe_3))
(rule (! (let ((a!1 (store (store (store ((as const (Array Int Int)) 0) 4294967296 N)
                         4294967298
                         L)
                  4294967299
                  K))
      (a!3 (store (store (store ((as const (Array Int Int)) 0) 4294967296 N)
                         4294967297
                         M)
                  4294967298
                  L))
      (a!5 (store (store (store ((as const (Array Int Int)) 0) 4294967296 G)
                         4294967298
                         E)
                  4294967299
                  D))
      (a!7 (store (store (store ((as const (Array Int Int)) 0) 4294967296 G)
                         4294967297
                         F)
                  4294967298
                  E)))
(let ((a!2 (store (store (store (store a!1 8589934592 J) 8589934593 I)
                         8589934594
                         H)
                  4294967297
                  258))
      (a!4 (store (store (store (store a!3 4294967299 K) 8589934592 J)
                         8589934593
                         I)
                  8589934594
                  H))
      (a!6 (store (store (store (store a!5 8589934592 C) 8589934593 B)
                         8589934594
                         A)
                  4294967297
                  258))
      (a!8 (store (store (store (store a!7 4294967299 D) 8589934592 C)
                         8589934593
                         B)
                  8589934594
                  A)))
(let ((a!9 (and (State R Q P O N M L K J I H G F E D C B A)
                (= (select (ite R a!2 a!4) 4294967296)
                   (select (ite P a!6 a!8) 4294967296))
                (= (select (ite R a!2 a!4) 4294967297)
                   (select (ite P a!6 a!8) 4294967297))
                (= (select (ite R a!2 a!4) 4294967298)
                   (select (ite P a!6 a!8) 4294967298))
                (= (select (ite R a!2 a!4) 4294967299)
                   (select (ite P a!6 a!8) 4294967299))
                false)))
  (=> a!9
      (State R
             Q
             P
             O
             (select (ite R a!2 a!4) 4294967296)
             (select (ite R a!2 a!4) 4294967297)
             (select (ite R a!2 a!4) 4294967298)
             (select (ite R a!2 a!4) 4294967299)
             (select (ite R a!2 a!4) 8589934592)
             (select (ite R a!2 a!4) 8589934593)
             (select (ite R a!2 a!4) 8589934594)
             (select (ite P a!6 a!8) 4294967296)
             (select (ite P a!6 a!8) 4294967297)
             (select (ite P a!6 a!8) 4294967298)
             (select (ite P a!6 a!8) 4294967299)
             (select (ite P a!6 a!8) 8589934592)
             (select (ite P a!6 a!8) 8589934593)
             (select (ite P a!6 a!8) 8589934594)))))) :named step_3))
(rule (! (let ((a!1 (and (State R Q P O N M L K J I H G F E D C B A)
                (not (and (= K D) (= M F) (= L E))))))
  (=> a!1 Bad)) :named observe_4))
(rule (! (=> (and (State R Q P O N M L K J I H G F E D C B A)
         (= K D)
         (= M F)
         (= L E)
         true)
    (State R Q P O K M L K J I H D F E D C B A)) :named step_4))
(rule (! (=> (and (State R Q P O V U T S N M L K J I H G F E)
         (>= D 256)
         (>= C 256)
         (>= B 256)
         (>= A 256))
    (State R Q P O D C B A N M L D C B A G F E)) :named common_public_assignment))

(query Bad)
