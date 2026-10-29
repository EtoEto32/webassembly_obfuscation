(declare-rel State (Bool Bool Bool Bool Int Int Int Int Int Int Int Int Int Int Int Int Int Int Int Int Int Int Int Int Int Int Int Int Int Int Int Int Int Int Int Int Int Int))
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
(declare-var I1 Bool)
(declare-var J1 Bool)
(declare-var K1 Bool)
(declare-var L1 Bool)
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
       257
       257
       257
       257
       257
       257
       257
       257
       258))
(rule (! (let ((a!1 (and (State L1
                       K1
                       J1
                       I1
                       H1
                       G1
                       F1
                       E1
                       D1
                       C1
                       B1
                       A1
                       Z
                       Y
                       X
                       W
                       V
                       U
                       T
                       S
                       R
                       Q
                       P
                       O
                       N
                       M
                       L
                       K
                       J
                       I
                       H
                       G
                       F
                       E
                       D
                       C
                       B
                       A)
                (not (and (= H1 Q)
                          (= G1 P)
                          (= F1 O)
                          (= E1 N)
                          (= D1 M)
                          (= C1 L)
                          (= B1 K)
                          (= A1 J)
                          (= Z I)
                          (= Y H)
                          (= X G)
                          (= W F)
                          (= V E)
                          (= U D)
                          (= T C)
                          (= S B)
                          (= R A))))))
  (=> a!1 Bad)) :named observe_0))
(rule (! (let ((a!1 (State L1
                  K1
                  J1
                  I1
                  H1
                  G1
                  F1
                  E1
                  D1
                  C1
                  B1
                  A1
                  Z
                  Y
                  X
                  W
                  V
                  U
                  T
                  S
                  R
                  Q
                  P
                  O
                  N
                  M
                  L
                  K
                  J
                  I
                  H
                  G
                  F
                  E
                  D
                  C
                  B
                  A)))
  (=> (and a!1
           (= H1 Q)
           (= G1 P)
           (= F1 O)
           (= E1 N)
           (= D1 M)
           (= C1 L)
           (= B1 K)
           (= A1 J)
           (= Z I)
           (= Y H)
           (= X G)
           (= W F)
           (= V E)
           (= U D)
           (= T C)
           (= S B)
           (= R A)
           true)
      a!1)) :named step_0))
(rule (! (let ((a!1 (and (State L1
                       K1
                       J1
                       I1
                       H1
                       G1
                       F1
                       E1
                       D1
                       C1
                       B1
                       A1
                       Z
                       Y
                       X
                       W
                       V
                       U
                       T
                       S
                       R
                       Q
                       P
                       O
                       N
                       M
                       L
                       K
                       J
                       I
                       H
                       G
                       F
                       E
                       D
                       C
                       B
                       A)
                (not (and (= H1 Q)
                          (= G1 P)
                          (= F1 O)
                          (= E1 N)
                          (= D1 M)
                          (= C1 L)
                          (= B1 K)
                          (= A1 J)
                          (= Z I)
                          (= Y H)
                          (= X G)
                          (= W F)
                          (= V E)
                          (= U D)
                          (= T C)
                          (= S B)
                          (= R A))))))
  (=> a!1 Bad)) :named observe_1))
(rule (! (let ((a!1 (State L1
                  K1
                  J1
                  I1
                  H1
                  G1
                  F1
                  E1
                  D1
                  C1
                  B1
                  A1
                  Z
                  Y
                  X
                  W
                  V
                  U
                  T
                  S
                  R
                  Q
                  P
                  O
                  N
                  M
                  L
                  K
                  J
                  I
                  H
                  G
                  F
                  E
                  D
                  C
                  B
                  A)))
  (=> (and a!1
           (= H1 Q)
           (= G1 P)
           (= F1 O)
           (= E1 N)
           (= D1 M)
           (= C1 L)
           (= B1 K)
           (= A1 J)
           (= Z I)
           (= Y H)
           (= X G)
           (= W F)
           (= V E)
           (= U D)
           (= T C)
           (= S B)
           (= R A)
           true)
      a!1)) :named step_1))
(rule (! (let ((a!1 (store (store (store ((as const (Array Int Int)) 0) 4294967296 H1)
                         8589934592
                         G1)
                  8589934593
                  F1))
      (a!6 (store (store (store ((as const (Array Int Int)) 0) 4294967296 Q)
                         8589934592
                         P)
                  8589934593
                  O)))
(let ((a!2 (store (store (store (store a!1 8589934594 E1) 8589934595 D1)
                         8589934596
                         C1)
                  8589934597
                  B1))
      (a!7 (store (store (store (store a!6 8589934594 N) 8589934595 M)
                         8589934596
                         L)
                  8589934597
                  K)))
(let ((a!3 (store (store (store (store a!2 8589934598 A1) 8589934599 Z)
                         8589934600
                         Y)
                  8589934601
                  X))
      (a!8 (store (store (store (store a!7 8589934598 J) 8589934599 I)
                         8589934600
                         H)
                  8589934601
                  G)))
(let ((a!4 (store (store (store (store a!3 8589934602 W) 8589934603 V)
                         8589934604
                         U)
                  8589934605
                  T))
      (a!9 (store (store (store (store a!8 8589934602 F) 8589934603 E)
                         8589934604
                         D)
                  8589934605
                  C)))
(let ((a!5 (ite L1
                (store (store a!4 8589934606 S) 8589934607 257)
                (store (store a!4 8589934606 S) 8589934607 R)))
      (a!10 (ite J1
                 (store (store a!9 8589934606 B) 8589934607 257)
                 (store (store a!9 8589934606 B) 8589934607 A))))
(let ((a!11 (= (select (ite (and L1 K1) (store a!5 8589934592 258) a!5)
                       8589934592)
               (select (ite (and J1 I1) (store a!10 8589934592 258) a!10)
                       8589934592)))
      (a!12 (= (select (ite (and L1 K1) (store a!5 8589934592 258) a!5)
                       8589934593)
               (select (ite (and J1 I1) (store a!10 8589934592 258) a!10)
                       8589934593)))
      (a!13 (= (select (ite (and L1 K1) (store a!5 8589934592 258) a!5)
                       8589934594)
               (select (ite (and J1 I1) (store a!10 8589934592 258) a!10)
                       8589934594)))
      (a!14 (= (select (ite (and L1 K1) (store a!5 8589934592 258) a!5)
                       8589934595)
               (select (ite (and J1 I1) (store a!10 8589934592 258) a!10)
                       8589934595)))
      (a!15 (= (select (ite (and L1 K1) (store a!5 8589934592 258) a!5)
                       8589934596)
               (select (ite (and J1 I1) (store a!10 8589934592 258) a!10)
                       8589934596)))
      (a!16 (= (select (ite (and L1 K1) (store a!5 8589934592 258) a!5)
                       8589934597)
               (select (ite (and J1 I1) (store a!10 8589934592 258) a!10)
                       8589934597)))
      (a!17 (= (select (ite (and L1 K1) (store a!5 8589934592 258) a!5)
                       8589934598)
               (select (ite (and J1 I1) (store a!10 8589934592 258) a!10)
                       8589934598)))
      (a!18 (= (select (ite (and L1 K1) (store a!5 8589934592 258) a!5)
                       8589934599)
               (select (ite (and J1 I1) (store a!10 8589934592 258) a!10)
                       8589934599)))
      (a!19 (= (select (ite (and L1 K1) (store a!5 8589934592 258) a!5)
                       8589934600)
               (select (ite (and J1 I1) (store a!10 8589934592 258) a!10)
                       8589934600)))
      (a!20 (= (select (ite (and L1 K1) (store a!5 8589934592 258) a!5)
                       8589934601)
               (select (ite (and J1 I1) (store a!10 8589934592 258) a!10)
                       8589934601)))
      (a!21 (= (select (ite (and L1 K1) (store a!5 8589934592 258) a!5)
                       8589934602)
               (select (ite (and J1 I1) (store a!10 8589934592 258) a!10)
                       8589934602)))
      (a!22 (= (select (ite (and L1 K1) (store a!5 8589934592 258) a!5)
                       8589934603)
               (select (ite (and J1 I1) (store a!10 8589934592 258) a!10)
                       8589934603)))
      (a!23 (= (select (ite (and L1 K1) (store a!5 8589934592 258) a!5)
                       8589934604)
               (select (ite (and J1 I1) (store a!10 8589934592 258) a!10)
                       8589934604)))
      (a!24 (= (select (ite (and L1 K1) (store a!5 8589934592 258) a!5)
                       8589934605)
               (select (ite (and J1 I1) (store a!10 8589934592 258) a!10)
                       8589934605)))
      (a!25 (= (select (ite (and L1 K1) (store a!5 8589934592 258) a!5)
                       8589934606)
               (select (ite (and J1 I1) (store a!10 8589934592 258) a!10)
                       8589934606)))
      (a!26 (= (select (ite (and L1 K1) (store a!5 8589934592 258) a!5)
                       8589934607)
               (select (ite (and J1 I1) (store a!10 8589934592 258) a!10)
                       8589934607))))
(let ((a!27 (not (and (= (and L1 K1) (and J1 I1))
                      (= H1 Q)
                      a!11
                      a!12
                      a!13
                      a!14
                      a!15
                      a!16
                      a!17
                      a!18
                      a!19
                      a!20
                      a!21
                      a!22
                      a!23
                      a!24
                      a!25
                      a!26))))
  (=> (and (State L1
                  K1
                  J1
                  I1
                  H1
                  G1
                  F1
                  E1
                  D1
                  C1
                  B1
                  A1
                  Z
                  Y
                  X
                  W
                  V
                  U
                  T
                  S
                  R
                  Q
                  P
                  O
                  N
                  M
                  L
                  K
                  J
                  I
                  H
                  G
                  F
                  E
                  D
                  C
                  B
                  A)
           a!27)
      Bad)))))))) :named observe_2))
(rule (! (let ((a!1 (store (store (store ((as const (Array Int Int)) 0) 4294967296 H1)
                         8589934592
                         G1)
                  8589934593
                  F1))
      (a!6 (store (store (store ((as const (Array Int Int)) 0) 4294967296 Q)
                         8589934592
                         P)
                  8589934593
                  O)))
(let ((a!2 (store (store (store (store a!1 8589934594 E1) 8589934595 D1)
                         8589934596
                         C1)
                  8589934597
                  B1))
      (a!7 (store (store (store (store a!6 8589934594 N) 8589934595 M)
                         8589934596
                         L)
                  8589934597
                  K)))
(let ((a!3 (store (store (store (store a!2 8589934598 A1) 8589934599 Z)
                         8589934600
                         Y)
                  8589934601
                  X))
      (a!8 (store (store (store (store a!7 8589934598 J) 8589934599 I)
                         8589934600
                         H)
                  8589934601
                  G)))
(let ((a!4 (store (store (store (store a!3 8589934602 W) 8589934603 V)
                         8589934604
                         U)
                  8589934605
                  T))
      (a!9 (store (store (store (store a!8 8589934602 F) 8589934603 E)
                         8589934604
                         D)
                  8589934605
                  C)))
(let ((a!5 (ite L1
                (store (store a!4 8589934606 S) 8589934607 257)
                (store (store a!4 8589934606 S) 8589934607 R)))
      (a!10 (ite J1
                 (store (store a!9 8589934606 B) 8589934607 257)
                 (store (store a!9 8589934606 B) 8589934607 A))))
(let ((a!11 (= (select (ite (and L1 K1) (store a!5 8589934592 258) a!5)
                       8589934592)
               (select (ite (and J1 I1) (store a!10 8589934592 258) a!10)
                       8589934592)))
      (a!12 (= (select (ite (and L1 K1) (store a!5 8589934592 258) a!5)
                       8589934593)
               (select (ite (and J1 I1) (store a!10 8589934592 258) a!10)
                       8589934593)))
      (a!13 (= (select (ite (and L1 K1) (store a!5 8589934592 258) a!5)
                       8589934594)
               (select (ite (and J1 I1) (store a!10 8589934592 258) a!10)
                       8589934594)))
      (a!14 (= (select (ite (and L1 K1) (store a!5 8589934592 258) a!5)
                       8589934595)
               (select (ite (and J1 I1) (store a!10 8589934592 258) a!10)
                       8589934595)))
      (a!15 (= (select (ite (and L1 K1) (store a!5 8589934592 258) a!5)
                       8589934596)
               (select (ite (and J1 I1) (store a!10 8589934592 258) a!10)
                       8589934596)))
      (a!16 (= (select (ite (and L1 K1) (store a!5 8589934592 258) a!5)
                       8589934597)
               (select (ite (and J1 I1) (store a!10 8589934592 258) a!10)
                       8589934597)))
      (a!17 (= (select (ite (and L1 K1) (store a!5 8589934592 258) a!5)
                       8589934598)
               (select (ite (and J1 I1) (store a!10 8589934592 258) a!10)
                       8589934598)))
      (a!18 (= (select (ite (and L1 K1) (store a!5 8589934592 258) a!5)
                       8589934599)
               (select (ite (and J1 I1) (store a!10 8589934592 258) a!10)
                       8589934599)))
      (a!19 (= (select (ite (and L1 K1) (store a!5 8589934592 258) a!5)
                       8589934600)
               (select (ite (and J1 I1) (store a!10 8589934592 258) a!10)
                       8589934600)))
      (a!20 (= (select (ite (and L1 K1) (store a!5 8589934592 258) a!5)
                       8589934601)
               (select (ite (and J1 I1) (store a!10 8589934592 258) a!10)
                       8589934601)))
      (a!21 (= (select (ite (and L1 K1) (store a!5 8589934592 258) a!5)
                       8589934602)
               (select (ite (and J1 I1) (store a!10 8589934592 258) a!10)
                       8589934602)))
      (a!22 (= (select (ite (and L1 K1) (store a!5 8589934592 258) a!5)
                       8589934603)
               (select (ite (and J1 I1) (store a!10 8589934592 258) a!10)
                       8589934603)))
      (a!23 (= (select (ite (and L1 K1) (store a!5 8589934592 258) a!5)
                       8589934604)
               (select (ite (and J1 I1) (store a!10 8589934592 258) a!10)
                       8589934604)))
      (a!24 (= (select (ite (and L1 K1) (store a!5 8589934592 258) a!5)
                       8589934605)
               (select (ite (and J1 I1) (store a!10 8589934592 258) a!10)
                       8589934605)))
      (a!25 (= (select (ite (and L1 K1) (store a!5 8589934592 258) a!5)
                       8589934606)
               (select (ite (and J1 I1) (store a!10 8589934592 258) a!10)
                       8589934606)))
      (a!26 (= (select (ite (and L1 K1) (store a!5 8589934592 258) a!5)
                       8589934607)
               (select (ite (and J1 I1) (store a!10 8589934592 258) a!10)
                       8589934607))))
  (=> (and (State L1
                  K1
                  J1
                  I1
                  H1
                  G1
                  F1
                  E1
                  D1
                  C1
                  B1
                  A1
                  Z
                  Y
                  X
                  W
                  V
                  U
                  T
                  S
                  R
                  Q
                  P
                  O
                  N
                  M
                  L
                  K
                  J
                  I
                  H
                  G
                  F
                  E
                  D
                  C
                  B
                  A)
           (= (and L1 K1) (and J1 I1))
           (= H1 Q)
           a!11
           a!12
           a!13
           a!14
           a!15
           a!16
           a!17
           a!18
           a!19
           a!20
           a!21
           a!22
           a!23
           a!24
           a!25
           a!26
           true)
      (State false
             K1
             false
             I1
             H1
             (ite (and L1 K1) 258 G1)
             F1
             E1
             D1
             C1
             B1
             A1
             Z
             Y
             X
             W
             V
             U
             T
             S
             (ite L1 257 R)
             Q
             (ite (and J1 I1) 258 P)
             O
             N
             M
             L
             K
             J
             I
             H
             G
             F
             E
             D
             C
             B
             (ite J1 257 A))))))))) :named step_2))
(rule (! (let ((a!1 (and (State L1
                       K1
                       J1
                       I1
                       H1
                       G1
                       F1
                       E1
                       D1
                       C1
                       B1
                       A1
                       Z
                       Y
                       X
                       W
                       V
                       U
                       T
                       S
                       R
                       Q
                       P
                       O
                       N
                       M
                       L
                       K
                       J
                       I
                       H
                       G
                       F
                       E
                       D
                       C
                       B
                       A)
                (not (and (= H1 Q)
                          (= F1 O)
                          (= E1 N)
                          (= D1 M)
                          (= C1 L)
                          (= B1 K)
                          (= A1 J)
                          (= Z I)
                          (= Y H)
                          (= X G)
                          (= W F)
                          (= V E)
                          (= U D)
                          (= T C)
                          (= S B)
                          (= R A))))))
  (=> a!1 Bad)) :named observe_3))
(rule (! (=> (and (State L1
                K1
                J1
                I1
                H1
                G1
                F1
                E1
                D1
                C1
                B1
                A1
                Z
                Y
                X
                W
                V
                U
                T
                S
                R
                Q
                P
                O
                N
                M
                L
                K
                J
                I
                H
                G
                F
                E
                D
                C
                B
                A)
         (= H1 Q)
         (= F1 O)
         (= E1 N)
         (= D1 M)
         (= C1 L)
         (= B1 K)
         (= A1 J)
         (= Z I)
         (= Y H)
         (= X G)
         (= W F)
         (= V E)
         (= U D)
         (= T C)
         (= S B)
         (= R A)
         true)
    (State L1
           K1
           J1
           I1
           H1
           F1
           E1
           D1
           C1
           B1
           A1
           Z
           Y
           X
           W
           V
           U
           T
           S
           R
           R
           Q
           O
           N
           M
           L
           K
           J
           I
           H
           G
           F
           E
           D
           C
           B
           A
           A)) :named step_3))
(rule (! (=> (and (State L1
                K1
                J1
                I1
                H1
                G1
                F1
                E1
                D1
                C1
                B1
                A1
                Z
                Y
                X
                W
                V
                U
                T
                S
                R
                Q
                P
                O
                N
                M
                L
                K
                J
                I
                H
                G
                F
                E
                D
                C
                B
                A)
         (not true))
    Bad) :named observe_4))
(rule (! (=> (and (State L1
                K1
                J1
                I1
                H1
                G1
                F1
                E1
                D1
                C1
                B1
                A1
                Z
                Y
                X
                W
                V
                U
                T
                S
                R
                Q
                P
                O
                N
                M
                L
                K
                J
                I
                H
                G
                F
                E
                D
                C
                B
                A)
         true
         true)
    (State L1
           K1
           J1
           I1
           257
           257
           257
           257
           257
           257
           257
           257
           257
           257
           257
           257
           257
           257
           257
           257
           257
           257
           257
           257
           257
           257
           257
           257
           257
           257
           257
           257
           257
           257
           257
           257
           257
           257)) :named step_4))

(query Bad)
