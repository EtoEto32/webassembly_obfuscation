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
       257))
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
         (not (= H1 Q)))
    Bad) :named observe_0))
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
  (=> (and a!1 (= H1 Q) true) a!1)) :named step_0))
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
         (not (= H1 Q)))
    Bad) :named observe_1))
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
  (=> (and a!1 (= H1 Q) true) a!1)) :named step_1))
(rule (! (let ((a!1 (not (and (= (and L1 K1) (and J1 I1)) (= H1 Q)))))
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
           a!1)
      Bad)) :named observe_2))
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
         (= (and L1 K1) (and J1 I1))
         (= H1 Q)
         (or (and L1 K1) (and J1 I1)))
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
           (ite J1 257 A))) :named step_2))
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
         (not (= H1 Q)))
    Bad) :named observe_3))
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
