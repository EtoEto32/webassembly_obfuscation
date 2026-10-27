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
(declare-var B1 Bool)
(declare-var C1 Bool)
(declare-var D1 Bool)
(declare-var E1 Bool)
(rule (State false false true false 256 258 257 256 257 256 258 257 256 257))
(rule (! (let ((a!1 (and (State N M L K J I H G F E D C B A)
                (not (and (= J E) (= I D) (= H C) (= G B) (= F A))))))
  (=> a!1 Bad)) :named observe_0))
(rule (! (let ((a!1 (State N M L K J I H G F E D C B A)))
  (=> (and a!1 (= J E) (= I D) (= H C) (= G B) (= F A) true) a!1)) :named step_0))
(rule (! (let ((a!1 (and (State N M L K J I H G F E D C B A)
                (not (and (= J E) (= I D) (= H C) (= G B) (= F A))))))
  (=> a!1 Bad)) :named observe_1))
(rule (! (let ((a!1 (State N M L K J I H G F E D C B A)))
  (=> (and a!1 (= J E) (= I D) (= H C) (= G B) (= F A) true) a!1)) :named step_1))
(rule (! (let ((a!1 (store (store (store ((as const (Array Int Int)) 0) 4294967297 J)
                         4294967298
                         I)
                  8589934593
                  G))
      (a!2 (store (store (store ((as const (Array Int Int)) 0) 4294967297 J)
                         4294967298
                         I)
                  8589934592
                  H))
      (a!4 (store (store (store ((as const (Array Int Int)) 0) 4294967297 E)
                         4294967298
                         D)
                  8589934593
                  B))
      (a!5 (store (store (store ((as const (Array Int Int)) 0) 4294967297 E)
                         4294967298
                         D)
                  8589934592
                  C)))
(let ((a!3 (ite N
                (store (store a!1 8589934594 F) 8589934592 257)
                (store (store a!2 8589934593 G) 8589934594 F)))
      (a!6 (ite L
                (store (store a!4 8589934594 A) 8589934592 257)
                (store (store a!5 8589934593 B) 8589934594 A))))
(let ((a!7 (store (store (ite (and N M) (store a!3 8589934593 258) a!3)
                         4294967297
                         258)
                  4294967298
                  257))
      (a!8 (store (store (ite (and L K) (store a!6 8589934593 258) a!6)
                         4294967297
                         258)
                  4294967298
                  257)))
(let ((a!9 (= (select (ite (and N M) a!7 a!3) 4294967298)
              (select (ite (and L K) a!8 a!6) 4294967298)))
      (a!10 (= (select (ite (and N M) a!7 a!3) 8589934592)
               (select (ite (and L K) a!8 a!6) 8589934592)))
      (a!11 (= (select (ite (and N M) a!7 a!3) 8589934593)
               (select (ite (and L K) a!8 a!6) 8589934593)))
      (a!12 (= (select (ite (and N M) a!7 a!3) 8589934594)
               (select (ite (and L K) a!8 a!6) 8589934594))))
(let ((a!13 (and (= (ite (and N M) 258 (select a!3 4294967297))
                    (ite (and L K) 258 (select a!6 4294967297)))
                 a!9
                 a!10
                 a!11
                 a!12)))
  (=> (and (State N M L K J I H G F E D C B A) (not a!13)) Bad)))))) :named observe_2))
(rule (! (let ((a!1 (store (store (store ((as const (Array Int Int)) 0) 4294967297 J)
                         4294967298
                         I)
                  8589934593
                  G))
      (a!2 (store (store (store ((as const (Array Int Int)) 0) 4294967297 J)
                         4294967298
                         I)
                  8589934592
                  H))
      (a!4 (store (store (store ((as const (Array Int Int)) 0) 4294967297 E)
                         4294967298
                         D)
                  8589934593
                  B))
      (a!5 (store (store (store ((as const (Array Int Int)) 0) 4294967297 E)
                         4294967298
                         D)
                  8589934592
                  C)))
(let ((a!3 (ite N
                (store (store a!1 8589934594 F) 8589934592 257)
                (store (store a!2 8589934593 G) 8589934594 F)))
      (a!6 (ite L
                (store (store a!4 8589934594 A) 8589934592 257)
                (store (store a!5 8589934593 B) 8589934594 A))))
(let ((a!7 (store (store (ite (and N M) (store a!3 8589934593 258) a!3)
                         4294967297
                         258)
                  4294967298
                  257))
      (a!8 (store (store (ite (and L K) (store a!6 8589934593 258) a!6)
                         4294967297
                         258)
                  4294967298
                  257)))
(let ((a!9 (= (select (ite (and N M) a!7 a!3) 4294967298)
              (select (ite (and L K) a!8 a!6) 4294967298)))
      (a!10 (= (select (ite (and N M) a!7 a!3) 8589934592)
               (select (ite (and L K) a!8 a!6) 8589934592)))
      (a!11 (= (select (ite (and N M) a!7 a!3) 8589934593)
               (select (ite (and L K) a!8 a!6) 8589934593)))
      (a!12 (= (select (ite (and N M) a!7 a!3) 8589934594)
               (select (ite (and L K) a!8 a!6) 8589934594))))
(let ((a!13 (and (State N M L K J I H G F E D C B A)
                 (= (ite (and N M) 258 (select a!3 4294967297))
                    (ite (and L K) 258 (select a!6 4294967297)))
                 a!9
                 a!10
                 a!11
                 a!12
                 false)))
  (=> a!13
      (State false
             M
             false
             K
             (ite (and N M) 258 (select a!3 4294967297))
             (ite (and N M) 257 (select a!3 4294967298))
             (select a!3 8589934592)
             (ite (and N M) 258 (select a!3 8589934593))
             (select a!3 8589934594)
             (ite (and L K) 258 (select a!6 4294967297))
             (ite (and L K) 257 (select a!6 4294967298))
             (select a!6 8589934592)
             (ite (and L K) 258 (select a!6 8589934593))
             (select a!6 8589934594)))))))) :named step_2))
(rule (! (let ((a!1 (and (State N M L K J I H G F E D C B A)
                (not (and (= J E) (= I D) (= H C) (= G B) (= F A))))))
  (=> a!1 Bad)) :named observe_3))
(rule (! (let ((a!1 (State N M L K J I H G F E D C B A)))
  (=> (and a!1 (= J E) (= I D) (= H C) (= G B) (= F A) false) a!1)) :named step_3))
(rule (! (let ((a!1 (and (State N M L K J I H G F E D C B A)
                (not (and (= J E) (= I D) (= H C))))))
  (=> a!1 Bad)) :named observe_4))
(rule (! (=> (and (State N M L K J I H G F E D C B A) (= J E) (= I D) (= H C) false)
    (State N M L K J I H J I E D C E D)) :named step_4))
(rule (! (=> (and (State N M L K Q P O J I H G F E D) (>= C 256) (>= B 256) (>= A 256))
    (State N M L K Q P C B A H G C B A)) :named common_public_assignment))

(query Bad)
