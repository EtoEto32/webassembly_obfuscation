(declare-rel State (Bool Bool Bool Bool Int Int Int Int Int Int))
(declare-rel Bad ())
(declare-var A Int)
(declare-var B Int)
(declare-var C Int)
(declare-var D Int)
(declare-var E Int)
(declare-var F Int)
(declare-var G Bool)
(declare-var H Bool)
(declare-var I Bool)
(declare-var J Bool)
(rule (State false false true false 257 257 257 257 257 257))
(rule (! (let ((a!1 (and (State J I H G F E D C B A) (not (and (= F C) (= E B) (= D A))))))
  (=> a!1 Bad)) :named observe_0))
(rule (! (let ((a!1 (State J I H G F E D C B A)))
  (=> (and a!1 (= F C) (= E B) (= D A) true) a!1)) :named step_0))
(rule (! (let ((a!1 (and (State J I H G F E D C B A) (not (and (= F C) (= E B) (= D A))))))
  (=> a!1 Bad)) :named observe_1))
(rule (! (let ((a!1 (State J I H G F E D C B A)))
  (=> (and a!1 (= F C) (= E B) (= D A) true) a!1)) :named step_1))
(rule (! (let ((a!1 (store (store (store ((as const (Array Int Int)) 0) 4294967296 F)
                         8589934592
                         E)
                  8589934593
                  257))
      (a!2 (store (store (store ((as const (Array Int Int)) 0) 4294967296 F)
                         8589934592
                         E)
                  8589934593
                  D))
      (a!4 (store (store (store ((as const (Array Int Int)) 0) 4294967296 C)
                         8589934592
                         B)
                  8589934593
                  257))
      (a!5 (store (store (store ((as const (Array Int Int)) 0) 4294967296 C)
                         8589934592
                         B)
                  8589934593
                  A)))
(let ((a!3 (ite (and J I)
                (store (ite J a!1 a!2) 8589934592 258)
                (ite J a!1 a!2)))
      (a!6 (ite (and H G)
                (store (ite H a!4 a!5) 8589934592 258)
                (ite H a!4 a!5))))
(let ((a!7 (not (and (= (and J I) (and H G))
                     (= F C)
                     (= (select a!3 8589934592) (select a!6 8589934592))
                     (= (select a!3 8589934593) (select a!6 8589934593))))))
  (=> (and (State J I H G F E D C B A) a!7) Bad)))) :named observe_2))
(rule (! (let ((a!1 (store (store (store ((as const (Array Int Int)) 0) 4294967296 F)
                         8589934592
                         E)
                  8589934593
                  257))
      (a!2 (store (store (store ((as const (Array Int Int)) 0) 4294967296 F)
                         8589934592
                         E)
                  8589934593
                  D))
      (a!4 (store (store (store ((as const (Array Int Int)) 0) 4294967296 C)
                         8589934592
                         B)
                  8589934593
                  257))
      (a!5 (store (store (store ((as const (Array Int Int)) 0) 4294967296 C)
                         8589934592
                         B)
                  8589934593
                  A)))
(let ((a!3 (ite (and J I)
                (store (ite J a!1 a!2) 8589934592 258)
                (ite J a!1 a!2)))
      (a!6 (ite (and H G)
                (store (ite H a!4 a!5) 8589934592 258)
                (ite H a!4 a!5))))
  (=> (and (State J I H G F E D C B A)
           (= (and J I) (and H G))
           (= F C)
           (= (select a!3 8589934592) (select a!6 8589934592))
           (= (select a!3 8589934593) (select a!6 8589934593))
           true)
      (State false
             I
             false
             G
             F
             (ite (and J I) 258 E)
             (ite J 257 D)
             C
             (ite (and H G) 258 B)
             (ite H 257 A))))) :named step_2))
(rule (! (let ((a!1 (and (State J I H G F E D C B A) (not (and (= F C) (= D A))))))
  (=> a!1 Bad)) :named observe_3))
(rule (! (=> (and (State J I H G F E D C B A) (= F C) (= D A) true)
    (State J I H G F D D C A A)) :named step_3))
(rule (! (let ((a!1 (and (State J I H G F E D C B A) (not (and (= E B) (= D A))))))
  (=> a!1 Bad)) :named observe_4))
(rule (! (=> (and (State J I H G F E D C B A) (= E B) (= D A) true)
    (State J I H G E E D B B A)) :named step_4))

(query Bad)
