(module
 (type $0 (func (param i32) (result i32)))
 (type $1 (cont $0))
 (type $2 (func (result i32 (ref $1))))
 (tag $tag$0 (type $0) (param i32) (result i32))
 (export "run" (func $1))
 (func $0 (param $0 i32) (result i32)
  (i32.xor
   (i32.mul
    (i32.sub
     (i32.mul
      (i32.xor
       (i32.add
        (i32.mul
         (i32.xor
          (i32.add
           (i32.mul
            (i32.xor
             (i32.sub
              (i32.mul
               (i32.xor
                (i32.sub
                 (i32.mul
                  (i32.xor
                   (i32.mul
                    (i32.sub
                     (i32.xor
                      (i32.sub
                       (i32.mul
                        (i32.xor
                         (i32.add
                          (suspend $tag$0
                           (i32.sub
                            (i32.xor
                             (i32.sub
                              (i32.mul
                               (i32.xor
                                (i32.mul
                                 (i32.sub
                                  (i32.xor
                                   (i32.add
                                    (i32.mul
                                     (i32.xor
                                      (i32.sub
                                       (i32.xor
                                        (i32.sub
                                         (i32.mul
                                          (i32.xor
                                           (i32.sub
                                            (i32.mul
                                             (i32.xor
                                              (i32.add
                                               (i32.mul
                                                (i32.xor
                                                 (i32.mul
                                                  (i32.xor
                                                   (i32.add
                                                    (local.get $0)
                                                    (i32.const 782107941)
                                                   )
                                                   (i32.const -2106579695)
                                                  )
                                                  (i32.const 1831562813)
                                                 )
                                                 (i32.const 636419493)
                                                )
                                                (i32.const 1842741523)
                                               )
                                               (i32.const 1389698432)
                                              )
                                              (i32.const -166203550)
                                             )
                                             (i32.const 784234921)
                                            )
                                            (i32.const 2040765873)
                                           )
                                           (i32.const 625619744)
                                          )
                                          (i32.const -2142107253)
                                         )
                                         (i32.const 707189431)
                                        )
                                        (i32.const -535775327)
                                       )
                                       (i32.const 638647664)
                                      )
                                      (i32.const -271114601)
                                     )
                                     (i32.const 1907496817)
                                    )
                                    (i32.const 1345520287)
                                   )
                                   (i32.const 1328919085)
                                  )
                                  (i32.const 1129583911)
                                 )
                                 (i32.const -912292361)
                                )
                                (i32.const -1965868599)
                               )
                               (i32.const -1472086877)
                              )
                              (i32.const 603176395)
                             )
                             (i32.const 2012507776)
                            )
                            (i32.const 832709457)
                           )
                          )
                          (i32.const 642273056)
                         )
                         (i32.const 1502320648)
                        )
                        (i32.const 1014482685)
                       )
                       (i32.const 1286082075)
                      )
                      (i32.const -1445643270)
                     )
                     (i32.const 1133673571)
                    )
                    (i32.const -1006035607)
                   )
                   (i32.const 1999124716)
                  )
                  (i32.const -1235583151)
                 )
                 (i32.const 1543271184)
                )
                (i32.const -261993028)
               )
               (i32.const -1514200361)
              )
              (i32.const 1292856432)
             )
             (i32.const -484274029)
            )
            (i32.const 1664266175)
           )
           (i32.const 1732906941)
          )
          (i32.const 591200015)
         )
         (i32.const -195196877)
        )
        (i32.const 306539338)
       )
       (i32.const -677032542)
      )
      (i32.const -244954899)
     )
     (i32.const 723824811)
    )
    (i32.const -1101996535)
   )
   (i32.const -736472834)
  )
 )
 (func $1 (param $0 i32) (result i32)
  (local $1 i32)
  (local $2 (ref $1))
  (local $scratch (tuple i32 (ref $1)))
  (local $scratch_4 i32)
  (resume $1
   (i32.mul
    (i32.xor
     (i32.add
      (i32.xor
       (i32.add
        (i32.xor
         (i32.sub
          (i32.mul
           (i32.xor
            (i32.sub
             (i32.xor
              (i32.sub
               (i32.mul
                (i32.xor
                 (i32.add
                  (local.tee $1
                   (block (result i32)
                    (local.set $scratch_4
                     (tuple.extract 2 0
                      (local.tee $scratch
                       (block $block (type $2) (result i32 (ref $1))
                        (return
                         (resume $1 (on $tag$0 $block)
                          (local.get $0)
                          (cont.new $1
                           (ref.func $0)
                          )
                         )
                        )
                       )
                      )
                     )
                    )
                    (local.set $2
                     (tuple.extract 2 1
                      (local.get $scratch)
                     )
                    )
                    (local.get $scratch_4)
                   )
                  )
                  (i32.const 1299530155)
                 )
                 (i32.const -448057694)
                )
                (i32.const -131516945)
               )
               (i32.const 199321205)
              )
              (i32.const 371918037)
             )
             (i32.const 1175894198)
            )
            (i32.const -707003826)
           )
           (i32.const -1883591027)
          )
          (i32.const 291333266)
         )
         (i32.const 1151148210)
        )
        (i32.const 948596431)
       )
       (i32.const 328234447)
      )
      (i32.const 326538399)
     )
     (i32.const 2082833020)
    )
    (i32.const -1843537403)
   )
   (local.get $2)
  )
 )
)


(assert_return (invoke "run" (i32.const 0)) (i32.const 1536408821))
(assert_return (invoke "run" (i32.const 1)) (i32.const -56969258))
(assert_return (invoke "run" (i32.const -1)) (i32.const 1402608088))
(assert_return (invoke "run" (i32.const 2147483647)) (i32.const -744875560))
(assert_return (invoke "run" (i32.const -2147483648)) (i32.const -611074827))
(assert_return (invoke "run" (i32.const -411958416)) (i32.const 72938245))
(assert_return (invoke "run" (i32.const 1120404087)) (i32.const -2132308896))
(assert_return (invoke "run" (i32.const 1709112008)) (i32.const 1804080941))
(assert_return (invoke "run" (i32.const -1510481581)) (i32.const 2054924388))
(assert_return (invoke "run" (i32.const 2099601353)) (i32.const 547796878))
(assert_return (invoke "run" (i32.const 625051791)) (i32.const 640110344))
(assert_return (invoke "run" (i32.const -1632241111)) (i32.const 421545902))
(assert_return (invoke "run" (i32.const -399894949)) (i32.const -683878116))
(assert_return (invoke "run" (i32.const 732786516)) (i32.const 1028195505))
(assert_return (invoke "run" (i32.const 849392505)) (i32.const -1382263970))
(assert_return (invoke "run" (i32.const -546951445)) (i32.const 1694239244))
(assert_return (invoke "run" (i32.const -595339828)) (i32.const 1082400889))
(assert_return (invoke "run" (i32.const -343680365)) (i32.const 1735542052))
(assert_return (invoke "run" (i32.const -1542421957)) (i32.const 312652732))
(assert_return (invoke "run" (i32.const -765312319)) (i32.const 1706748438))
(assert_return (invoke "run" (i32.const -1915502956)) (i32.const -241325199))
(assert_return (invoke "run" (i32.const -1944354001)) (i32.const -1509221528))
(assert_return (invoke "run" (i32.const 1255997916)) (i32.const -881764439))
(assert_return (invoke "run" (i32.const -1822764909)) (i32.const 666529572))
(assert_return (invoke "run" (i32.const -1084383991)) (i32.const -225410738))
(assert_return (invoke "run" (i32.const 286658247)) (i32.const -948754160))
(assert_return (invoke "run" (i32.const -1721947039)) (i32.const -97184266))
(assert_return (invoke "run" (i32.const -185936593)) (i32.const -76387992))
(assert_return (invoke "run" (i32.const -1974479840)) (i32.const -384426539))
(assert_return (invoke "run" (i32.const -625694221)) (i32.const 1007570116))
(assert_return (invoke "run" (i32.const -1103596767)) (i32.const -236291274))
(assert_return (invoke "run" (i32.const 1941202738)) (i32.const -1896595093))
(assert_return (invoke "run" (i32.const 61514351)) (i32.const 1068336424))
(assert_return (invoke "run" (i32.const -101244613)) (i32.const -1568250692))
(assert_return (invoke "run" (i32.const 182368991)) (i32.const -666541320))
(assert_return (invoke "run" (i32.const -933743237)) (i32.const 726056060))
(assert_return (invoke "run" (i32.const 1017662534)) (i32.const -38642041))
(assert_return (invoke "run" (i32.const -1800402386)) (i32.const 1087488959))
(assert_return (invoke "run" (i32.const 97185806)) (i32.const -263191969))
(assert_return (invoke "run" (i32.const -2016735287)) (i32.const 1848649614))
(assert_return (invoke "run" (i32.const -1903363118)) (i32.const 199796171))
(assert_return (invoke "run" (i32.const 1935202208)) (i32.const -89451947))
(assert_return (invoke "run" (i32.const 327803478)) (i32.const 48865783))
(assert_return (invoke "run" (i32.const -176051198)) (i32.const -361849317))
(assert_return (invoke "run" (i32.const -1529352198)) (i32.const -1387918877))
(assert_return (invoke "run" (i32.const -1867378375)) (i32.const 1177533854))
(assert_return (invoke "run" (i32.const -88293434)) (i32.const 942912263))
(assert_return (invoke "run" (i32.const -576705610)) (i32.const 533592855))
(assert_return (invoke "run" (i32.const -2026649390)) (i32.const 436668619))
(assert_return (invoke "run" (i32.const 1152475225)) (i32.const -364923906))
(assert_return (invoke "run" (i32.const -2043691093)) (i32.const 757190988))
(assert_return (invoke "run" (i32.const 1162306183)) (i32.const 1565274448))
(assert_return (invoke "run" (i32.const 1608607932)) (i32.const 1972030409))
(assert_return (invoke "run" (i32.const 479123451)) (i32.const 1542815740))
(assert_return (invoke "run" (i32.const -860905005)) (i32.const 1127135204))
(assert_return (invoke "run" (i32.const 928105861)) (i32.const 2122480802))
(assert_return (invoke "run" (i32.const -1001263249)) (i32.const 2054441000))
(assert_return (invoke "run" (i32.const -870765543)) (i32.const -1192637378))
(assert_return (invoke "run" (i32.const -833094813)) (i32.const -44711916))
(assert_return (invoke "run" (i32.const -351333985)) (i32.const 281346104))
(assert_return (invoke "run" (i32.const 896084493)) (i32.const 223117530))
(assert_return (invoke "run" (i32.const -1018057642)) (i32.const -1159555081))
(assert_return (invoke "run" (i32.const -147416036)) (i32.const 726101609))
(assert_return (invoke "run" (i32.const 1957866765)) (i32.const -292849190))
(assert_return (invoke "run" (i32.const -1448730244)) (i32.const -2019735031))
(assert_return (invoke "run" (i32.const -1221780062)) (i32.const -444907909))
(assert_return (invoke "run" (i32.const 1915467862)) (i32.const -564796425))
(assert_return (invoke "run" (i32.const 136040573)) (i32.const -1877790230))
(assert_return (invoke "run" (i32.const -971084949)) (i32.const 572906892))
(assert_return (invoke "run" (i32.const 491221352)) (i32.const 1914150925))
(assert_return (invoke "run" (i32.const 97138781)) (i32.const -1709532406))
(assert_return (invoke "run" (i32.const -1271353402)) (i32.const -624958713))
(assert_return (invoke "run" (i32.const 2120699491)) (i32.const 159690004))
(assert_return (invoke "run" (i32.const 820365949)) (i32.const -1266724886))
(assert_return (invoke "run" (i32.const 960156436)) (i32.const 1333139185))
(assert_return (invoke "run" (i32.const 1756039987)) (i32.const 246519684))
(assert_return (invoke "run" (i32.const 1728405728)) (i32.const -1901497067))
(assert_return (invoke "run" (i32.const 227212253)) (i32.const -1414885494))
(assert_return (invoke "run" (i32.const -664738656)) (i32.const 1748588885))
(assert_return (invoke "run" (i32.const -749635737)) (i32.const -687814672))
(assert_return (invoke "run" (i32.const -1634242897)) (i32.const -541346328))
(assert_return (invoke "run" (i32.const 2129914132)) (i32.const -304441103))
(assert_return (invoke "run" (i32.const 2119079523)) (i32.const -435190508))
(assert_return (invoke "run" (i32.const 452370905)) (i32.const 736566398))
(assert_return (invoke "run" (i32.const -600868653)) (i32.const 765800676))
(assert_return (invoke "run" (i32.const -500035829)) (i32.const 400401644))
(assert_return (invoke "run" (i32.const 1372749289)) (i32.const -1211640594))
(assert_return (invoke "run" (i32.const -1103015877)) (i32.const 1799325116))
(assert_return (invoke "run" (i32.const -1577461703)) (i32.const -683765090))
(assert_return (invoke "run" (i32.const 354094906)) (i32.const 2728355))
(assert_return (invoke "run" (i32.const -2125056993)) (i32.const 93187000))
(assert_return (invoke "run" (i32.const -1280492366)) (i32.const -413001237))
(assert_return (invoke "run" (i32.const -981472977)) (i32.const -1447527064))
(assert_return (invoke "run" (i32.const -34929719)) (i32.const 1995225998))
(assert_return (invoke "run" (i32.const -761022929)) (i32.const 1178283112))
(assert_return (invoke "run" (i32.const 1970631843)) (i32.const -1990129452))
(assert_return (invoke "run" (i32.const -778938409)) (i32.const -736255104))
(assert_return (invoke "run" (i32.const -214379289)) (i32.const 1845148272))
(assert_return (invoke "run" (i32.const -701673925)) (i32.const 286465980))
(assert_return (invoke "run" (i32.const -620510355)) (i32.const 1082396154))
(assert_return (invoke "run" (i32.const 87585061)) (i32.const 393611650))
(assert_return (invoke "run" (i32.const 1318133302)) (i32.const 1731316887))
(assert_return (invoke "run" (i32.const -1381909189)) (i32.const -1102884676))
(assert_return (invoke "run" (i32.const -616105535)) (i32.const 2029061910))
(assert_return (invoke "run" (i32.const 1953445492)) (i32.const -447829871))