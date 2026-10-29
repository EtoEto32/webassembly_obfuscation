(declare-rel State (Bool Bool Bool Bool Bool Bool Bool Bool Int Int Int Int Int Int Int Int Int Int Int Int Int Int))
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
(declare-var S Bool)
(declare-var T Bool)
(declare-var U Bool)
(declare-var V Bool)
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
(declare-var K1 Int)
(declare-var L1 Int)
(declare-var M1 Int)
(declare-var N1 Int)
(declare-var O1 Int)
(declare-var P1 Bool)
(declare-var Q1 Bool)
(declare-var R1 Bool)
(declare-var S1 Bool)
(declare-var T1 Bool)
(declare-var U1 Bool)
(declare-var V1 Bool)
(declare-var W1 Bool)
(rule (State true
       true
       false
       false
       true
       true
       true
       false
       214
       89
       190
       256
       258
       258
       257
       214
       89
       190
       256
       258
       258
       257))
(rule (! (let ((a!1 (and (State V U T S R Q P O N M L K J I H G F E D C B A)
                (not (and (= N G) (= M F) (= L E) (= K D) (= J C))))))
  (=> a!1 Bad)) :named observe_0))
(rule (! (let ((a!1 (State V U T S R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 (= N G) (= M F) (= L E) (= K D) (= J C) true) a!1)) :named step_0))
(rule (! (let ((a!1 (and (State V U T S R Q P O N M L K J I H G F E D C B A)
                (not (and (= N G) (= M F) (= L E) (= K D) (= J C))))))
  (=> a!1 Bad)) :named observe_1))
(rule (! (let ((a!1 (State V U T S R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 (= N G) (= M F) (= L E) (= K D) (= J C) true) a!1)) :named step_1))
(rule (! (let ((a!1 (store (store (store ((as const (Array Int Int)) 0) 2 N) 3 M) 4 L))
      (a!4 (store (store (store ((as const (Array Int Int)) 0) 2 G) 3 F) 4 E)))
(let ((a!2 (store (store (store (store a!1 4294967296 K) 4294967299 J)
                         8589934593
                         H)
                  8589934592
                  257))
      (a!3 (store (store (store (store a!1 4294967296 K) 4294967299 J)
                         8589934592
                         I)
                  8589934593
                  H))
      (a!5 (store (store (store (store a!4 4294967296 D) 4294967299 C)
                         8589934593
                         A)
                  8589934592
                  257))
      (a!6 (store (store (store (store a!4 4294967296 D) 4294967299 C)
                         8589934592
                         B)
                  8589934593
                  A)))
(let ((a!7 (ite (and T S)
                (store (ite T a!2 a!3) 8589934593 258)
                (ite T a!2 a!3)))
      (a!8 (ite (and P O)
                (store (ite P a!5 a!6) 8589934593 258)
                (ite P a!5 a!6))))
(let ((a!9 (and (= (select (ite T a!2 a!3) 2) (select (ite P a!5 a!6) 2))
                (= (select a!7 3) (select a!8 3))
                (= (select a!7 4) (select a!8 4))
                (= (select a!7 4294967296) (select a!8 4294967296))
                (= (select a!7 4294967299) (select a!8 4294967299)))))
  (=> (and (State V U T S R Q P O N M L K J I H G F E D C B A) (not a!9)) Bad))))) :named observe_2))
(rule (! (let ((a!1 (store (store (store ((as const (Array Int Int)) 0) 2 N) 3 M) 4 L))
      (a!4 (store (store (store ((as const (Array Int Int)) 0) 2 G) 3 F) 4 E)))
(let ((a!2 (store (store (store (store a!1 4294967296 K) 4294967299 J)
                         8589934593
                         H)
                  8589934592
                  257))
      (a!3 (store (store (store (store a!1 4294967296 K) 4294967299 J)
                         8589934592
                         I)
                  8589934593
                  H))
      (a!5 (store (store (store (store a!4 4294967296 D) 4294967299 C)
                         8589934593
                         A)
                  8589934592
                  257))
      (a!6 (store (store (store (store a!4 4294967296 D) 4294967299 C)
                         8589934592
                         B)
                  8589934593
                  A)))
(let ((a!7 (ite (and T S)
                (store (ite T a!2 a!3) 8589934593 258)
                (ite T a!2 a!3)))
      (a!8 (ite (and P O)
                (store (ite P a!5 a!6) 8589934593 258)
                (ite P a!5 a!6)))
      (a!10 (State V
                   U
                   false
                   S
                   R
                   Q
                   false
                   O
                   (select (ite T a!2 a!3) 2)
                   (select (ite T a!2 a!3) 3)
                   (select (ite T a!2 a!3) 4)
                   (select (ite T a!2 a!3) 4294967296)
                   (select (ite T a!2 a!3) 4294967299)
                   (select (ite T a!2 a!3) 8589934592)
                   (ite (and T S) 258 (select (ite T a!2 a!3) 8589934593))
                   (select (ite P a!5 a!6) 2)
                   (select (ite P a!5 a!6) 3)
                   (select (ite P a!5 a!6) 4)
                   (select (ite P a!5 a!6) 4294967296)
                   (select (ite P a!5 a!6) 4294967299)
                   (select (ite P a!5 a!6) 8589934592)
                   (ite (and P O) 258 (select (ite P a!5 a!6) 8589934593)))))
(let ((a!9 (and (State V U T S R Q P O N M L K J I H G F E D C B A)
                (= (select (ite T a!2 a!3) 2) (select (ite P a!5 a!6) 2))
                (= (select a!7 3) (select a!8 3))
                (= (select a!7 4) (select a!8 4))
                (= (select a!7 4294967296) (select a!8 4294967296))
                (= (select a!7 4294967299) (select a!8 4294967299))
                false)))
  (=> a!9 a!10))))) :named step_2))
(rule (! (let ((a!1 (and (State V U T S R Q P O N M L K J I H G F E D C B A)
                (not (and (= M F) (= L E) (= K D) (= J C))))))
  (=> a!1 Bad)) :named observe_3))
(rule (! (=> (and (State V U T S R Q P O N M L K J I H G F E D C B A)
         (= M F)
         (= L E)
         (= K D)
         (= J C)
         true)
    (State V U false false R Q false false M L L K J I H F E E D C B A)) :named step_3))
(rule (! (let ((a!1 (and (State V U T S R Q P O N M L K J I H G F E D C B A)
                (not (and (= N G) (= M F) (= L E) (= K D) (= J C))))))
  (=> a!1 Bad)) :named observe_4))
(rule (! (=> (and (State V U T S R Q P O N M L K J I H G F E D C B A)
         (= N G)
         (= M F)
         (= L E)
         (= K D)
         (= J C)
         false)
    (State V U T false R Q P false N M L K J I H G F E D C B A)) :named step_4))
(rule (! (let ((a!1 (and (State V U T S R Q P O N M L K J I H G F E D C B A)
                (not (and (= N G) (= M F) (= L E) (= K D) (= J C))))))
  (=> a!1 Bad)) :named observe_5))
(rule (! (let ((a!1 (State V U T S R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1 (= N G) (= M F) (= L E) (= K D) (= J C) true) a!1)) :named step_5))
(rule (! (=> (and (State V U T S R Q P O A1 Z Y X W N M L K J I H G F)
         (>= E 0)
         (<= E 255)
         (>= D 0)
         (<= D 255)
         (>= C 0)
         (<= C 255)
         (>= B 256)
         (>= A 256))
    (State V U T S R Q P O E D C B A N M E D C B A G F)) :named common_public_assignment))

(query Bad)
