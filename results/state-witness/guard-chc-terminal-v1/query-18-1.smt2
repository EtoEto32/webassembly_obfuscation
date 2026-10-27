(declare-rel State (Bool Bool Bool Bool Int Int Int Int Int Int Int Int Int Int Int Int Int Int Int Int Int Int))
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
(declare-var O Int)
(declare-var P Int)
(declare-var Q Int)
(declare-var R Int)
(declare-var S Bool)
(declare-var T Bool)
(declare-var U Bool)
(declare-var V Bool)
(rule (State false
       false
       true
       false
       257
       257
       257
       257
       257
       257
       257
       257
       258
       257
       257
       257
       257
       257
       257
       257
       257
       258))
(rule (! (let ((a!1 (and (State V U T S R Q P O N M L K J I H G F E D C B A)
                (not (and (= R I)
                          (= Q H)
                          (= P G)
                          (= O F)
                          (= N E)
                          (= M D)
                          (= L C)
                          (= K B)
                          (= J A))))))
  (=> a!1 Bad)) :named observe_0))
(rule (! (let ((a!1 (State V U T S R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1
           (= R I)
           (= Q H)
           (= P G)
           (= O F)
           (= N E)
           (= M D)
           (= L C)
           (= K B)
           (= J A)
           true)
      a!1)) :named step_0))
(rule (! (let ((a!1 (and (State V U T S R Q P O N M L K J I H G F E D C B A)
                (not (and (= R I)
                          (= Q H)
                          (= P G)
                          (= O F)
                          (= N E)
                          (= M D)
                          (= L C)
                          (= K B)
                          (= J A))))))
  (=> a!1 Bad)) :named observe_1))
(rule (! (let ((a!1 (State V U T S R Q P O N M L K J I H G F E D C B A)))
  (=> (and a!1
           (= R I)
           (= Q H)
           (= P G)
           (= O F)
           (= N E)
           (= M D)
           (= L C)
           (= K B)
           (= J A)
           true)
      a!1)) :named step_1))
(rule (! (let ((a!1 (store (store (store ((as const (Array Int Int)) 0) 4294967296 R)
                         8589934592
                         Q)
                  8589934593
                  P))
      (a!4 (store (store (store ((as const (Array Int Int)) 0) 4294967296 I)
                         8589934592
                         H)
                  8589934593
                  G)))
(let ((a!2 (store (store (store (store a!1 8589934594 O) 8589934595 N)
                         8589934596
                         M)
                  8589934597
                  L))
      (a!5 (store (store (store (store a!4 8589934594 F) 8589934595 E)
                         8589934596
                         D)
                  8589934597
                  C)))
(let ((a!3 (ite V
                (store (store a!2 8589934598 K) 8589934599 257)
                (store (store a!2 8589934598 K) 8589934599 J)))
      (a!6 (ite T
                (store (store a!5 8589934598 B) 8589934599 257)
                (store (store a!5 8589934598 B) 8589934599 A))))
(let ((a!7 (= (select (ite (and V U) (store a!3 8589934592 258) a!3) 8589934592)
              (select (ite (and T S) (store a!6 8589934592 258) a!6) 8589934592)))
      (a!8 (= (select (ite (and V U) (store a!3 8589934592 258) a!3) 8589934593)
              (select (ite (and T S) (store a!6 8589934592 258) a!6) 8589934593)))
      (a!9 (= (select (ite (and V U) (store a!3 8589934592 258) a!3) 8589934594)
              (select (ite (and T S) (store a!6 8589934592 258) a!6) 8589934594)))
      (a!10 (= (select (ite (and V U) (store a!3 8589934592 258) a!3)
                       8589934595)
               (select (ite (and T S) (store a!6 8589934592 258) a!6)
                       8589934595)))
      (a!11 (= (select (ite (and V U) (store a!3 8589934592 258) a!3)
                       8589934596)
               (select (ite (and T S) (store a!6 8589934592 258) a!6)
                       8589934596)))
      (a!12 (= (select (ite (and V U) (store a!3 8589934592 258) a!3)
                       8589934597)
               (select (ite (and T S) (store a!6 8589934592 258) a!6)
                       8589934597)))
      (a!13 (= (select (ite (and V U) (store a!3 8589934592 258) a!3)
                       8589934598)
               (select (ite (and T S) (store a!6 8589934592 258) a!6)
                       8589934598)))
      (a!14 (= (select (ite (and V U) (store a!3 8589934592 258) a!3)
                       8589934599)
               (select (ite (and T S) (store a!6 8589934592 258) a!6)
                       8589934599))))
(let ((a!15 (not (and (= (and V U) (and T S))
                      (= R I)
                      a!7
                      a!8
                      a!9
                      a!10
                      a!11
                      a!12
                      a!13
                      a!14))))
  (=> (and (State V U T S R Q P O N M L K J I H G F E D C B A) a!15) Bad)))))) :named observe_2))
(rule (! (let ((a!1 (store (store (store ((as const (Array Int Int)) 0) 4294967296 R)
                         8589934592
                         Q)
                  8589934593
                  P))
      (a!4 (store (store (store ((as const (Array Int Int)) 0) 4294967296 I)
                         8589934592
                         H)
                  8589934593
                  G)))
(let ((a!2 (store (store (store (store a!1 8589934594 O) 8589934595 N)
                         8589934596
                         M)
                  8589934597
                  L))
      (a!5 (store (store (store (store a!4 8589934594 F) 8589934595 E)
                         8589934596
                         D)
                  8589934597
                  C)))
(let ((a!3 (ite V
                (store (store a!2 8589934598 K) 8589934599 257)
                (store (store a!2 8589934598 K) 8589934599 J)))
      (a!6 (ite T
                (store (store a!5 8589934598 B) 8589934599 257)
                (store (store a!5 8589934598 B) 8589934599 A))))
(let ((a!7 (= (select (ite (and V U) (store a!3 8589934592 258) a!3) 8589934592)
              (select (ite (and T S) (store a!6 8589934592 258) a!6) 8589934592)))
      (a!8 (= (select (ite (and V U) (store a!3 8589934592 258) a!3) 8589934593)
              (select (ite (and T S) (store a!6 8589934592 258) a!6) 8589934593)))
      (a!9 (= (select (ite (and V U) (store a!3 8589934592 258) a!3) 8589934594)
              (select (ite (and T S) (store a!6 8589934592 258) a!6) 8589934594)))
      (a!10 (= (select (ite (and V U) (store a!3 8589934592 258) a!3)
                       8589934595)
               (select (ite (and T S) (store a!6 8589934592 258) a!6)
                       8589934595)))
      (a!11 (= (select (ite (and V U) (store a!3 8589934592 258) a!3)
                       8589934596)
               (select (ite (and T S) (store a!6 8589934592 258) a!6)
                       8589934596)))
      (a!12 (= (select (ite (and V U) (store a!3 8589934592 258) a!3)
                       8589934597)
               (select (ite (and T S) (store a!6 8589934592 258) a!6)
                       8589934597)))
      (a!13 (= (select (ite (and V U) (store a!3 8589934592 258) a!3)
                       8589934598)
               (select (ite (and T S) (store a!6 8589934592 258) a!6)
                       8589934598)))
      (a!14 (= (select (ite (and V U) (store a!3 8589934592 258) a!3)
                       8589934599)
               (select (ite (and T S) (store a!6 8589934592 258) a!6)
                       8589934599))))
  (=> (and (State V U T S R Q P O N M L K J I H G F E D C B A)
           (= (and V U) (and T S))
           (= R I)
           a!7
           a!8
           a!9
           a!10
           a!11
           a!12
           a!13
           a!14
           (or (and V U) (and T S)))
      (State false
             U
             false
             S
             R
             (ite (and V U) 258 Q)
             P
             O
             N
             M
             L
             K
             (ite V 257 J)
             I
             (ite (and T S) 258 H)
             G
             F
             E
             D
             C
             B
             (ite T 257 A))))))) :named step_2))
(rule (! (let ((a!1 (and (State V U T S R Q P O N M L K J I H G F E D C B A)
                (not (and (= R I)
                          (= P G)
                          (= O F)
                          (= N E)
                          (= M D)
                          (= L C)
                          (= K B)
                          (= J A))))))
  (=> a!1 Bad)) :named observe_3))
(rule (! (=> (and (State V U T S R Q P O N M L K J I H G F E D C B A)
         (= R I)
         (= P G)
         (= O F)
         (= N E)
         (= M D)
         (= L C)
         (= K B)
         (= J A)
         true)
    (State V U T S R P O N M L K J J I G F E D C B A A)) :named step_3))
(rule (! (let ((a!1 (and (State V U T S R Q P O N M L K J I H G F E D C B A)
                (not (and (= Q H)
                          (= P G)
                          (= O F)
                          (= N E)
                          (= M D)
                          (= L C)
                          (= K B)
                          (= J A))))))
  (=> a!1 Bad)) :named observe_4))
(rule (! (=> (and (State V U T S R Q P O N M L K J I H G F E D C B A)
         (= Q H)
         (= P G)
         (= O F)
         (= N E)
         (= M D)
         (= L C)
         (= K B)
         (= J A)
         true)
    (State V U T S Q Q P O N M L K J H H G F E D C B A)) :named step_4))

(query Bad)
