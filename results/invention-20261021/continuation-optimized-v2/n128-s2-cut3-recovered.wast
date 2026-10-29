(module
 (type $0 (func (param i32) (result i32)))
 (export "run" (func $0))
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
                                         (i32.const 466820698)
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
)


(assert_return (invoke "run" (i32.const 0)) (i32.const 1536408821))
(assert_return (invoke "run" (i32.const 1)) (i32.const -56969258))
(assert_return (invoke "run" (i32.const -1)) (i32.const 1402608088))
(assert_return (invoke "run" (i32.const 2147483647)) (i32.const -744875560))
(assert_return (invoke "run" (i32.const -2147483648)) (i32.const -611074827))
(assert_return (invoke "run" (i32.const 196642359)) (i32.const -441609056))
(assert_return (invoke "run" (i32.const -224137111)) (i32.const 619023982))
(assert_return (invoke "run" (i32.const 1840964165)) (i32.const 202096098))
(assert_return (invoke "run" (i32.const 1349186009)) (i32.const -477074306))
(assert_return (invoke "run" (i32.const -101405053)) (i32.const 240472180))
(assert_return (invoke "run" (i32.const 2047020847)) (i32.const -196868248))
(assert_return (invoke "run" (i32.const 1888488264)) (i32.const -1837241683))
(assert_return (invoke "run" (i32.const 1194853836)) (i32.const -1366208391))
(assert_return (invoke "run" (i32.const -296306340)) (i32.const -1375396311))
(assert_return (invoke "run" (i32.const -30397743)) (i32.const -1001266938))
(assert_return (invoke "run" (i32.const 2106283988)) (i32.const -80467919))
(assert_return (invoke "run" (i32.const 177682147)) (i32.const 1850863252))
(assert_return (invoke "run" (i32.const 344333371)) (i32.const 985121212))
(assert_return (invoke "run" (i32.const -1356908749)) (i32.const 652731268))
(assert_return (invoke "run" (i32.const -45810228)) (i32.const 238614649))
(assert_return (invoke "run" (i32.const 509198255)) (i32.const 985639144))
(assert_return (invoke "run" (i32.const -926274962)) (i32.const 2104053631))
(assert_return (invoke "run" (i32.const -526908063)) (i32.const -900134666))
(assert_return (invoke "run" (i32.const -1897419949)) (i32.const 1609999972))
(assert_return (invoke "run" (i32.const 1139782435)) (i32.const 626004564))
(assert_return (invoke "run" (i32.const -1554838504)) (i32.const 1641779101))
(assert_return (invoke "run" (i32.const -1028926839)) (i32.const 1643289038))
(assert_return (invoke "run" (i32.const 595738337)) (i32.const 1292652918))
(assert_return (invoke "run" (i32.const 97044486)) (i32.const 1140742855))
(assert_return (invoke "run" (i32.const -435270933)) (i32.const -1576991220))
(assert_return (invoke "run" (i32.const 152845342)) (i32.const 430963855))
(assert_return (invoke "run" (i32.const 1471284239)) (i32.const -1488154744))
(assert_return (invoke "run" (i32.const -1408646396)) (i32.const -1489547839))
(assert_return (invoke "run" (i32.const 297388253)) (i32.const -1908500854))
(assert_return (invoke "run" (i32.const -185802350)) (i32.const 687183115))
(assert_return (invoke "run" (i32.const 779950304)) (i32.const 237665557))
(assert_return (invoke "run" (i32.const 978143580)) (i32.const 508358185))
(assert_return (invoke "run" (i32.const 80705809)) (i32.const -1248911162))
(assert_return (invoke "run" (i32.const -1913148908)) (i32.const 2094052337))
(assert_return (invoke "run" (i32.const -607657530)) (i32.const -458993401))
(assert_return (invoke "run" (i32.const -1427492005)) (i32.const -287476708))
(assert_return (invoke "run" (i32.const 180039131)) (i32.const -244243044))
(assert_return (invoke "run" (i32.const -738418780)) (i32.const -1839002975))
(assert_return (invoke "run" (i32.const 1931100308)) (i32.const -1194780303))
(assert_return (invoke "run" (i32.const -147914517)) (i32.const -1331038196))
(assert_return (invoke "run" (i32.const -514916398)) (i32.const -331761205))
(assert_return (invoke "run" (i32.const -32942220)) (i32.const 1692152721))
(assert_return (invoke "run" (i32.const 1374602582)) (i32.const 40491767))
(assert_return (invoke "run" (i32.const 1775091807)) (i32.const -772527752))
(assert_return (invoke "run" (i32.const 1410525099)) (i32.const 1303259468))
(assert_return (invoke "run" (i32.const 399398110)) (i32.const 1658226895))
(assert_return (invoke "run" (i32.const 495779884)) (i32.const 1755935385))
(assert_return (invoke "run" (i32.const 1552037765)) (i32.const -256558430))
(assert_return (invoke "run" (i32.const 934386663)) (i32.const -155474064))
(assert_return (invoke "run" (i32.const 1637109253)) (i32.const 836205090))
(assert_return (invoke "run" (i32.const -945568197)) (i32.const 2006919100))
(assert_return (invoke "run" (i32.const -651167491)) (i32.const 1623467370))
(assert_return (invoke "run" (i32.const -997255150)) (i32.const 988929163))
(assert_return (invoke "run" (i32.const -543019220)) (i32.const 1322482585))
(assert_return (invoke "run" (i32.const 104228282)) (i32.const -1371339997))
(assert_return (invoke "run" (i32.const -1033732941)) (i32.const -44486140))
(assert_return (invoke "run" (i32.const -887626606)) (i32.const 801268235))
(assert_return (invoke "run" (i32.const -1248494531)) (i32.const -1453921750))
(assert_return (invoke "run" (i32.const -136403613)) (i32.const -869808620))
(assert_return (invoke "run" (i32.const 489788821)) (i32.const 1981176466))
(assert_return (invoke "run" (i32.const -897518616)) (i32.const 993502605))
(assert_return (invoke "run" (i32.const -855314131)) (i32.const 225932602))
(assert_return (invoke "run" (i32.const 941525424)) (i32.const 351394245))
(assert_return (invoke "run" (i32.const 1335001476)) (i32.const -295093951))
(assert_return (invoke "run" (i32.const 810857385)) (i32.const 1204710958))
(assert_return (invoke "run" (i32.const -622100022)) (i32.const -1629766381))
(assert_return (invoke "run" (i32.const -556892538)) (i32.const 2102503495))
(assert_return (invoke "run" (i32.const -1175390569)) (i32.const 432484288))
(assert_return (invoke "run" (i32.const -2082208416)) (i32.const 975028373))
(assert_return (invoke "run" (i32.const -1600859830)) (i32.const -89893997))
(assert_return (invoke "run" (i32.const 571080179)) (i32.const -420781884))
(assert_return (invoke "run" (i32.const 823861408)) (i32.const 1530013013))
(assert_return (invoke "run" (i32.const -905214811)) (i32.const -2028521982))
(assert_return (invoke "run" (i32.const -1501023793)) (i32.const -416770872))
(assert_return (invoke "run" (i32.const -307065869)) (i32.const 72977092))
(assert_return (invoke "run" (i32.const 1347711179)) (i32.const 906207788))
(assert_return (invoke "run" (i32.const 303099828)) (i32.const -1204832175))
(assert_return (invoke "run" (i32.const 2069475227)) (i32.const -942406436))
(assert_return (invoke "run" (i32.const -1774411608)) (i32.const -142667571))
(assert_return (invoke "run" (i32.const 939774630)) (i32.const 1164383143))
(assert_return (invoke "run" (i32.const -1885540704)) (i32.const -1352153259))
(assert_return (invoke "run" (i32.const -2051936750)) (i32.const 305030795))
(assert_return (invoke "run" (i32.const 512985228)) (i32.const -895928903))
(assert_return (invoke "run" (i32.const 2093008707)) (i32.const -1194504780))
(assert_return (invoke "run" (i32.const -639733485)) (i32.const -885743964))
(assert_return (invoke "run" (i32.const -1863316467)) (i32.const 1747668698))
(assert_return (invoke "run" (i32.const 339128900)) (i32.const 271940481))
(assert_return (invoke "run" (i32.const -1182729338)) (i32.const 892572487))
(assert_return (invoke "run" (i32.const 1480032370)) (i32.const -1624624853))
(assert_return (invoke "run" (i32.const 902775823)) (i32.const 1007243144))
(assert_return (invoke "run" (i32.const 801077537)) (i32.const -1074858698))
(assert_return (invoke "run" (i32.const 826795445)) (i32.const 1934009586))
(assert_return (invoke "run" (i32.const 1181347377)) (i32.const -986389978))
(assert_return (invoke "run" (i32.const -642926818)) (i32.const -348934769))
(assert_return (invoke "run" (i32.const 524322736)) (i32.const -237673531))
(assert_return (invoke "run" (i32.const 501134370)) (i32.const 856541691))
(assert_return (invoke "run" (i32.const -1337963473)) (i32.const 1653780072))
(assert_return (invoke "run" (i32.const 1085315739)) (i32.const 1342627292))
(assert_return (invoke "run" (i32.const 81398920)) (i32.const -1969385363))
(assert_return (invoke "run" (i32.const 2053671758)) (i32.const 1386937887))