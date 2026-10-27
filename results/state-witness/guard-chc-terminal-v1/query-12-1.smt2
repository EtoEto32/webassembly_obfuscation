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
(rule (State false false true false 257 257 257 257 258 257 257 257 257 258))
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
(rule (! (let ((a!1 (store (store (store ((as const (Array Int Int)) 0) 4294967296 J)
                         8589934592
                         I)
                  8589934593
                  H))
      (a!3 (store (store (store ((as const (Array Int Int)) 0) 4294967296 E)
                         8589934592
                         D)
                  8589934593
                  C)))
(let ((a!2 (ite N
                (store (store a!1 8589934594 G) 8589934595 257)
                (store (store a!1 8589934594 G) 8589934595 F)))
      (a!4 (ite L
                (store (store a!3 8589934594 B) 8589934595 257)
                (store (store a!3 8589934594 B) 8589934595 A))))
(let ((a!5 (= (select (ite (and N M) (store a!2 8589934592 258) a!2) 8589934592)
              (select (ite (and L K) (store a!4 8589934592 258) a!4) 8589934592)))
      (a!6 (= (select (ite (and N M) (store a!2 8589934592 258) a!2) 8589934593)
              (select (ite (and L K) (store a!4 8589934592 258) a!4) 8589934593)))
      (a!7 (= (select (ite (and N M) (store a!2 8589934592 258) a!2) 8589934594)
              (select (ite (and L K) (store a!4 8589934592 258) a!4) 8589934594)))
      (a!8 (= (select (ite (and N M) (store a!2 8589934592 258) a!2) 8589934595)
              (select (ite (and L K) (store a!4 8589934592 258) a!4) 8589934595))))
(let ((a!9 (not (and (= (and N M) (and L K)) (= J E) a!5 a!6 a!7 a!8))))
  (=> (and (State N M L K J I H G F E D C B A) a!9) Bad))))) :named observe_2))
(rule (! (let ((a!1 (store (store (store ((as const (Array Int Int)) 0) 4294967296 J)
                         8589934592
                         I)
                  8589934593
                  H))
      (a!3 (store (store (store ((as const (Array Int Int)) 0) 4294967296 E)
                         8589934592
                         D)
                  8589934593
                  C)))
(let ((a!2 (ite N
                (store (store a!1 8589934594 G) 8589934595 257)
                (store (store a!1 8589934594 G) 8589934595 F)))
      (a!4 (ite L
                (store (store a!3 8589934594 B) 8589934595 257)
                (store (store a!3 8589934594 B) 8589934595 A))))
(let ((a!5 (= (select (ite (and N M) (store a!2 8589934592 258) a!2) 8589934592)
              (select (ite (and L K) (store a!4 8589934592 258) a!4) 8589934592)))
      (a!6 (= (select (ite (and N M) (store a!2 8589934592 258) a!2) 8589934593)
              (select (ite (and L K) (store a!4 8589934592 258) a!4) 8589934593)))
      (a!7 (= (select (ite (and N M) (store a!2 8589934592 258) a!2) 8589934594)
              (select (ite (and L K) (store a!4 8589934592 258) a!4) 8589934594)))
      (a!8 (= (select (ite (and N M) (store a!2 8589934592 258) a!2) 8589934595)
              (select (ite (and L K) (store a!4 8589934592 258) a!4) 8589934595))))
  (=> (and (State N M L K J I H G F E D C B A)
           (= (and N M) (and L K))
           (= J E)
           a!5
           a!6
           a!7
           a!8
           (or (and N M) (and L K)))
      (State false
             M
             false
             K
             J
             (ite (and N M) 258 I)
             H
             G
             (ite N 257 F)
             E
             (ite (and L K) 258 D)
             C
             B
             (ite L 257 A)))))) :named step_2))
(rule (! (let ((a!1 (and (State N M L K J I H G F E D C B A)
                (not (and (= J E) (= H C) (= G B) (= F A))))))
  (=> a!1 Bad)) :named observe_3))
(rule (! (=> (and (State N M L K J I H G F E D C B A)
         (= J E)
         (= H C)
         (= G B)
         (= F A)
         true)
    (State N M L K J H G F F E C B A A)) :named step_3))
(rule (! (let ((a!1 (and (State N M L K J I H G F E D C B A)
                (not (and (= I D) (= H C) (= G B) (= F A))))))
  (=> a!1 Bad)) :named observe_4))
(rule (! (=> (and (State N M L K J I H G F E D C B A)
         (= I D)
         (= H C)
         (= G B)
         (= F A)
         true)
    (State N M L K I I H G F D D C B A)) :named step_4))

(query Bad)
