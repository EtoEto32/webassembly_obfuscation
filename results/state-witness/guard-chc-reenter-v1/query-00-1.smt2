(declare-rel State (Bool Bool Bool Bool Int Int Int Int))
(declare-rel Bad ())
(declare-var A Int)
(declare-var B Int)
(declare-var C Int)
(declare-var D Int)
(declare-var E Bool)
(declare-var F Bool)
(declare-var G Bool)
(declare-var H Bool)
(rule (State false false true false 257 258 257 258))
(rule (! (let ((a!1 (and (State H G F E D C B A) (not (and (= D B) (= C A))))))
  (=> a!1 Bad)) :named observe_0))
(rule (! (=> (and (State H G F E D C B A) (= D B) (= C A) true) (State H G F E D C B A)) :named step_0))
(rule (! (let ((a!1 (and (State H G F E D C B A) (not (and (= D B) (= C A))))))
  (=> a!1 Bad)) :named observe_1))
(rule (! (=> (and (State H G F E D C B A) (= D B) (= C A) true) (State H G F E D C B A)) :named step_1))
(rule (! (let ((a!1 (ite H
                (store (store ((as const (Array Int Int)) 0) 4294967296 D)
                       8589934592
                       257)
                (store (store ((as const (Array Int Int)) 0) 4294967296 D)
                       8589934592
                       C)))
      (a!2 (ite F
                (store (store ((as const (Array Int Int)) 0) 4294967296 B)
                       8589934592
                       257)
                (store (store ((as const (Array Int Int)) 0) 4294967296 B)
                       8589934592
                       A))))
(let ((a!3 (= (select (ite (and H G) (store a!1 8589934592 258) a!1) 8589934592)
              (select (ite (and F E) (store a!2 8589934592 258) a!2) 8589934592))))
(let ((a!4 (not (and (= (and H G) (and F E)) (= D B) a!3))))
  (=> (and (State H G F E D C B A) a!4) Bad)))) :named observe_2))
(rule (! (let ((a!1 (ite H
                (store (store ((as const (Array Int Int)) 0) 4294967296 D)
                       8589934592
                       257)
                (store (store ((as const (Array Int Int)) 0) 4294967296 D)
                       8589934592
                       C)))
      (a!2 (ite F
                (store (store ((as const (Array Int Int)) 0) 4294967296 B)
                       8589934592
                       257)
                (store (store ((as const (Array Int Int)) 0) 4294967296 B)
                       8589934592
                       A))))
(let ((a!3 (= (select (ite (and H G) (store a!1 8589934592 258) a!1) 8589934592)
              (select (ite (and F E) (store a!2 8589934592 258) a!2) 8589934592))))
  (=> (and (State H G F E D C B A) (= (and H G) (and F E)) (= D B) a!3 true)
      (State false
             G
             false
             E
             D
             (ite (and H G) 258 (ite H 257 C))
             B
             (ite (and F E) 258 (ite F 257 A)))))) :named step_2))
(rule (! (let ((a!1 (and (State H G F E D C B A) (not (and (= D B) (= C A))))))
  (=> a!1 Bad)) :named observe_3))
(rule (! (=> (and (State H G F E D C B A) (= D B) (= C A) true) (State H G F E D C B A)) :named step_3))
(rule (! (=> (and (State H G F E D C B A) (not (= C A))) Bad) :named observe_4))
(rule (! (=> (and (State H G F E D C B A) (= C A) true) (State H G F E C C A A)) :named step_4))

(query Bad)
