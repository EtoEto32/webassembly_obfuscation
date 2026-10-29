(declare-rel State (Bool Bool Bool Bool Int Int Int Int Int Int Int Int Int Int Int Int))
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
(declare-var Z Int)
(declare-var A1 Int)
(declare-var B1 Int)
(declare-var C1 Int)
(declare-var D1 Int)
(declare-var E1 Int)
(declare-var F1 Int)
(declare-var G1 Bool)
(declare-var H1 Bool)
(declare-var I1 Bool)
(declare-var J1 Bool)
(rule (State false false true false 257 257 257 256 256 257 257 257 257 256 256 257))
(rule (! (let ((a!1 (and (State P O N M L K J I H G F E D C B A)
                (not (and (= L F) (= K E) (= J D) (= I C) (= H B) (= G A))))))
  (=> a!1 Bad)) :named observe_0))
(rule (! (let ((a!1 (State P O N M L K J I H G F E D C B A)))
  (=> (and a!1 (= L F) (= K E) (= J D) (= I C) (= H B) (= G A) true) a!1)) :named step_0))
(rule (! (let ((a!1 (and (State P O N M L K J I H G F E D C B A)
                (not (and (= L F) (= K E) (= J D) (= I C) (= H B) (= G A))))))
  (=> a!1 Bad)) :named observe_1))
(rule (! (let ((a!1 (State P O N M L K J I H G F E D C B A)))
  (=> (and a!1 (= L F) (= K E) (= J D) (= I C) (= H B) (= G A) true) a!1)) :named step_1))
(rule (! (let ((a!1 (store (store (store ((as const (Array Int Int)) 0) 4294967296 L)
                         4294967297
                         K)
                  8589934593
                  I))
      (a!2 (store (store (store ((as const (Array Int Int)) 0) 4294967296 L)
                         4294967297
                         K)
                  8589934592
                  J))
      (a!4 (store (store (store ((as const (Array Int Int)) 0) 4294967296 F)
                         4294967297
                         E)
                  8589934593
                  C))
      (a!5 (store (store (store ((as const (Array Int Int)) 0) 4294967296 F)
                         4294967297
                         E)
                  8589934592
                  D)))
(let ((a!3 (ite P
                (store (store (store a!1 8589934594 H) 8589934595 G)
                       8589934592
                       257)
                (store (store (store a!2 8589934593 I) 8589934594 H)
                       8589934595
                       G)))
      (a!6 (ite N
                (store (store (store a!4 8589934594 B) 8589934595 A)
                       8589934592
                       257)
                (store (store (store a!5 8589934593 C) 8589934594 B)
                       8589934595
                       A))))
(let ((a!7 (= (select (ite (and P O) (store a!3 8589934593 258) a!3) 4294967297)
              (select (ite (and N M) (store a!6 8589934593 258) a!6) 4294967297)))
      (a!8 (= (select (ite (and P O) (store a!3 8589934593 258) a!3) 8589934592)
              (select (ite (and N M) (store a!6 8589934593 258) a!6) 8589934592)))
      (a!9 (= (select (ite (and P O) (store a!3 8589934593 258) a!3) 8589934593)
              (select (ite (and N M) (store a!6 8589934593 258) a!6) 8589934593)))
      (a!10 (= (select (ite (and P O) (store a!3 8589934593 258) a!3)
                       8589934594)
               (select (ite (and N M) (store a!6 8589934593 258) a!6)
                       8589934594)))
      (a!11 (= (select (ite (and P O) (store a!3 8589934593 258) a!3)
                       8589934595)
               (select (ite (and N M) (store a!6 8589934593 258) a!6)
                       8589934595))))
(let ((a!12 (not (and (= (select a!3 4294967296) (select a!6 4294967296))
                      a!7
                      a!8
                      a!9
                      a!10
                      a!11))))
  (=> (and (State P O N M L K J I H G F E D C B A) a!12) Bad))))) :named observe_2))
(rule (! (let ((a!1 (store (store (store ((as const (Array Int Int)) 0) 4294967296 L)
                         4294967297
                         K)
                  8589934593
                  I))
      (a!2 (store (store (store ((as const (Array Int Int)) 0) 4294967296 L)
                         4294967297
                         K)
                  8589934592
                  J))
      (a!4 (store (store (store ((as const (Array Int Int)) 0) 4294967296 F)
                         4294967297
                         E)
                  8589934593
                  C))
      (a!5 (store (store (store ((as const (Array Int Int)) 0) 4294967296 F)
                         4294967297
                         E)
                  8589934592
                  D)))
(let ((a!3 (ite P
                (store (store (store a!1 8589934594 H) 8589934595 G)
                       8589934592
                       257)
                (store (store (store a!2 8589934593 I) 8589934594 H)
                       8589934595
                       G)))
      (a!6 (ite N
                (store (store (store a!4 8589934594 B) 8589934595 A)
                       8589934592
                       257)
                (store (store (store a!5 8589934593 C) 8589934594 B)
                       8589934595
                       A))))
(let ((a!7 (= (select (ite (and P O) (store a!3 8589934593 258) a!3) 4294967297)
              (select (ite (and N M) (store a!6 8589934593 258) a!6) 4294967297)))
      (a!8 (= (select (ite (and P O) (store a!3 8589934593 258) a!3) 8589934592)
              (select (ite (and N M) (store a!6 8589934593 258) a!6) 8589934592)))
      (a!9 (= (select (ite (and P O) (store a!3 8589934593 258) a!3) 8589934593)
              (select (ite (and N M) (store a!6 8589934593 258) a!6) 8589934593)))
      (a!10 (= (select (ite (and P O) (store a!3 8589934593 258) a!3)
                       8589934594)
               (select (ite (and N M) (store a!6 8589934593 258) a!6)
                       8589934594)))
      (a!11 (= (select (ite (and P O) (store a!3 8589934593 258) a!3)
                       8589934595)
               (select (ite (and N M) (store a!6 8589934593 258) a!6)
                       8589934595))))
  (=> (and (State P O N M L K J I H G F E D C B A)
           (= (select a!3 4294967296) (select a!6 4294967296))
           a!7
           a!8
           a!9
           a!10
           a!11
           true)
      (State false
             O
             false
             M
             (select a!3 4294967296)
             (select a!3 4294967297)
             (select a!3 8589934592)
             (ite (and P O) 258 (select a!3 8589934593))
             (select a!3 8589934594)
             (select a!3 8589934595)
             (select a!6 4294967296)
             (select a!6 4294967297)
             (select a!6 8589934592)
             (ite (and N M) 258 (select a!6 8589934593))
             (select a!6 8589934594)
             (select a!6 8589934595)))))) :named step_2))
(rule (! (let ((a!1 (and (State P O N M L K J I H G F E D C B A)
                (not (and (= L F) (= K E) (= J D) (= I C) (= H B) (= G A))))))
  (=> a!1 Bad)) :named observe_3))
(rule (! (let ((a!1 (State P O N M L K J I H G F E D C B A)))
  (=> (and a!1 (= L F) (= K E) (= J D) (= I C) (= H B) (= G A) true) a!1)) :named step_3))
(rule (! (let ((a!1 (and (State P O N M L K J I H G F E D C B A)
                (not (and (= L F) (= K E) (= J D) (= I C) (= H B) (= G A))))))
  (=> a!1 Bad)) :named observe_4))
(rule (! (let ((a!1 (State P O N M L K J I H G F E D C B A)))
  (=> (and a!1 (= L F) (= K E) (= J D) (= I C) (= H B) (= G A) true) a!1)) :named step_4))
(rule (! (=> (and (State P O N M T S R Q L K J I H G F E)
         (>= D 256)
         (>= C 256)
         (>= B 256)
         (>= A 256))
    (State P O N M T S D C B A J I D C B A)) :named common_public_assignment))

(query Bad)
