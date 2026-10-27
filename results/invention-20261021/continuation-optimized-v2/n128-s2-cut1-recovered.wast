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
                                        (i32.sub
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
                                                          (i32.const -386761497)
                                                         )
                                                         (i32.const -843558969)
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
                                          (i32.const 1713987520)
                                         )
                                         (i32.const 1247166822)
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
(assert_return (invoke "run" (i32.const -536358888)) (i32.const 1902912413))
(assert_return (invoke "run" (i32.const -316519022)) (i32.const 2035171595))
(assert_return (invoke "run" (i32.const 1999444926)) (i32.const -1433594129))
(assert_return (invoke "run" (i32.const 1836307861)) (i32.const 2062949010))
(assert_return (invoke "run" (i32.const -1999370860)) (i32.const -1638478735))
(assert_return (invoke "run" (i32.const -1236742428)) (i32.const 783372129))
(assert_return (invoke "run" (i32.const -638318793)) (i32.const -409206880))
(assert_return (invoke "run" (i32.const 801524830)) (i32.const -137697457))
(assert_return (invoke "run" (i32.const 2010588984)) (i32.const -2037898883))
(assert_return (invoke "run" (i32.const -1545207053)) (i32.const -1009504316))
(assert_return (invoke "run" (i32.const 1722472429)) (i32.const -1030804614))
(assert_return (invoke "run" (i32.const 2048022146)) (i32.const 1718985627))
(assert_return (invoke "run" (i32.const -1979119377)) (i32.const -133310296))
(assert_return (invoke "run" (i32.const -1625254927)) (i32.const 1253009766))
(assert_return (invoke "run" (i32.const 140257358)) (i32.const 1913181471))
(assert_return (invoke "run" (i32.const -342316884)) (i32.const -235421671))
(assert_return (invoke "run" (i32.const -1776803803)) (i32.const -1173745022))
(assert_return (invoke "run" (i32.const 394414497)) (i32.const -338660170))
(assert_return (invoke "run" (i32.const -764652745)) (i32.const 1061649312))
(assert_return (invoke "run" (i32.const 15637674)) (i32.const 982154035))
(assert_return (invoke "run" (i32.const 103094533)) (i32.const -1486045406))
(assert_return (invoke "run" (i32.const -1657111306)) (i32.const -304628265))
(assert_return (invoke "run" (i32.const 1782534593)) (i32.const -187363562))
(assert_return (invoke "run" (i32.const -451851208)) (i32.const 2094282877))
(assert_return (invoke "run" (i32.const 503874530)) (i32.const -305677509))
(assert_return (invoke "run" (i32.const -1834447278)) (i32.const 36561739))
(assert_return (invoke "run" (i32.const -1956406554)) (i32.const -1560994969))
(assert_return (invoke "run" (i32.const 972964637)) (i32.const 1858723402))
(assert_return (invoke "run" (i32.const -316027291)) (i32.const 435332162))
(assert_return (invoke "run" (i32.const 511692429)) (i32.const 1298355802))
(assert_return (invoke "run" (i32.const -1586061021)) (i32.const -1484137388))
(assert_return (invoke "run" (i32.const 2139937972)) (i32.const 943302481))
(assert_return (invoke "run" (i32.const -1128026460)) (i32.const -2066911327))
(assert_return (invoke "run" (i32.const 78884868)) (i32.const 1671237825))
(assert_return (invoke "run" (i32.const 141033416)) (i32.const 396768813))
(assert_return (invoke "run" (i32.const 1371618414)) (i32.const 452785535))
(assert_return (invoke "run" (i32.const 1845541485)) (i32.const 1889944314))
(assert_return (invoke "run" (i32.const -865489166)) (i32.const 1943443627))
(assert_return (invoke "run" (i32.const 2066894652)) (i32.const -409636535))
(assert_return (invoke "run" (i32.const 1324177148)) (i32.const -2016354679))
(assert_return (invoke "run" (i32.const -932713378)) (i32.const 297060175))
(assert_return (invoke "run" (i32.const 959171929)) (i32.const 589985534))
(assert_return (invoke "run" (i32.const 756051903)) (i32.const -240489448))
(assert_return (invoke "run" (i32.const 1549435713)) (i32.const -1028505194))
(assert_return (invoke "run" (i32.const -164222922)) (i32.const 896920215))
(assert_return (invoke "run" (i32.const 1139441271)) (i32.const -681457568))
(assert_return (invoke "run" (i32.const 1806728269)) (i32.const 801923482))
(assert_return (invoke "run" (i32.const 807050161)) (i32.const 914799270))
(assert_return (invoke "run" (i32.const -1306522264)) (i32.const -1452934131))
(assert_return (invoke "run" (i32.const 1222297368)) (i32.const 638357661))
(assert_return (invoke "run" (i32.const -1892404007)) (i32.const 1598127486))
(assert_return (invoke "run" (i32.const -448800700)) (i32.const -89950847))
(assert_return (invoke "run" (i32.const 1138182194)) (i32.const -611040149))
(assert_return (invoke "run" (i32.const -1028504022)) (i32.const 547911603))
(assert_return (invoke "run" (i32.const -707052947)) (i32.const -830487814))
(assert_return (invoke "run" (i32.const -483409311)) (i32.const 1552390134))
(assert_return (invoke "run" (i32.const 496613671)) (i32.const 1851526704))
(assert_return (invoke "run" (i32.const -1086316527)) (i32.const -2094778938))
(assert_return (invoke "run" (i32.const 87466456)) (i32.const -281202723))
(assert_return (invoke "run" (i32.const -1765767390)) (i32.const 2065945339))
(assert_return (invoke "run" (i32.const -23322974)) (i32.const 262350203))
(assert_return (invoke "run" (i32.const -782112545)) (i32.const 2042756344))
(assert_return (invoke "run" (i32.const -1086916496)) (i32.const -1805612539))
(assert_return (invoke "run" (i32.const -1903568622)) (i32.const 1597930379))
(assert_return (invoke "run" (i32.const 621972660)) (i32.const 638113617))
(assert_return (invoke "run" (i32.const 389602612)) (i32.const 809138897))
(assert_return (invoke "run" (i32.const -1889905707)) (i32.const -2062944430))
(assert_return (invoke "run" (i32.const 994172779)) (i32.const 1879929228))
(assert_return (invoke "run" (i32.const 386718693)) (i32.const -1603016510))
(assert_return (invoke "run" (i32.const 883767896)) (i32.const -1498073251))
(assert_return (invoke "run" (i32.const -320501031)) (i32.const -1684830338))
(assert_return (invoke "run" (i32.const 1203299266)) (i32.const 1340279387))
(assert_return (invoke "run" (i32.const 1498735196)) (i32.const 2142821673))
(assert_return (invoke "run" (i32.const -177292167)) (i32.const -494980514))
(assert_return (invoke "run" (i32.const -1606425397)) (i32.const 1026831916))
(assert_return (invoke "run" (i32.const 348896761)) (i32.const -1617869090))
(assert_return (invoke "run" (i32.const -41613254)) (i32.const -1552263005))
(assert_return (invoke "run" (i32.const -1000146364)) (i32.const 213332865))
(assert_return (invoke "run" (i32.const -823164309)) (i32.const 285573772))
(assert_return (invoke "run" (i32.const 1525897217)) (i32.const 109551574))
(assert_return (invoke "run" (i32.const 1742993348)) (i32.const -1506616319))
(assert_return (invoke "run" (i32.const 1400422033)) (i32.const -555456186))
(assert_return (invoke "run" (i32.const -1533632955)) (i32.const -1740264990))
(assert_return (invoke "run" (i32.const 77698302)) (i32.const -546574161))
(assert_return (invoke "run" (i32.const 305293483)) (i32.const -1870285748))
(assert_return (invoke "run" (i32.const -2111590794)) (i32.const -1597337001))
(assert_return (invoke "run" (i32.const 1729781718)) (i32.const -549111177))
(assert_return (invoke "run" (i32.const 879343659)) (i32.const 524313804))
(assert_return (invoke "run" (i32.const 1826543652)) (i32.const -1065647583))
(assert_return (invoke "run" (i32.const 1109456251)) (i32.const -1342243716))
(assert_return (invoke "run" (i32.const 1380783769)) (i32.const -776090178))
(assert_return (invoke "run" (i32.const 912006272)) (i32.const -1407075723))
(assert_return (invoke "run" (i32.const 1206193912)) (i32.const 1853728445))
(assert_return (invoke "run" (i32.const 356577843)) (i32.const 1525590148))
(assert_return (invoke "run" (i32.const -738482937)) (i32.const -1276969776))
(assert_return (invoke "run" (i32.const 1803860066)) (i32.const -560524613))
(assert_return (invoke "run" (i32.const 1190454628)) (i32.const -1895802143))
(assert_return (invoke "run" (i32.const 375629668)) (i32.const -1310813983))
(assert_return (invoke "run" (i32.const 323361766)) (i32.const -1747668377))
(assert_return (invoke "run" (i32.const -1582566678)) (i32.const -2011929357))