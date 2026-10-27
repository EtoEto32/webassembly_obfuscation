(module
 (type $0 (func (param i32) (result i32)))
 (export "run" (func $0))
 (func $0 (param $0 i32) (result i32)
  (i32.sub
   (i32.mul
    (i32.xor
     (i32.sub
      (i32.xor
       (i32.mul
        (i32.xor
         (i32.sub
          (i32.xor
           (i32.mul
            (i32.add
             (i32.xor
              (i32.sub
               (i32.xor
                (i32.add
                 (i32.add
                  (i32.mul
                   (i32.xor
                    (i32.add
                     (i32.mul
                      (i32.xor
                       (i32.add
                        (i32.xor
                         (i32.mul
                          (i32.add
                           (i32.xor
                            (i32.sub
                             (i32.mul
                              (i32.xor
                               (i32.add
                                (i32.mul
                                 (i32.xor
                                  (i32.sub
                                   (i32.mul
                                    (i32.xor
                                     (i32.mul
                                      (i32.add
                                       (i32.xor
                                        (i32.mul
                                         (i32.xor
                                          (i32.sub
                                           (i32.mul
                                            (i32.xor
                                             (i32.mul
                                              (i32.sub
                                               (i32.xor
                                                (i32.sub
                                                 (i32.xor
                                                  (i32.sub
                                                   (i32.xor
                                                    (i32.sub
                                                     (i32.mul
                                                      (i32.xor
                                                       (i32.sub
                                                        (i32.xor
                                                         (i32.mul
                                                          (i32.sub
                                                           (i32.xor
                                                            (i32.sub
                                                             (i32.xor
                                                              (i32.sub
                                                               (i32.mul
                                                                (i32.xor
                                                                 (i32.add
                                                                  (i32.xor
                                                                   (i32.mul
                                                                    (i32.add
                                                                     (local.get $0)
                                                                     (i32.const 731756199)
                                                                    )
                                                                    (i32.const 1135366007)
                                                                   )
                                                                   (i32.const -1222858228)
                                                                  )
                                                                  (i32.const 970082092)
                                                                 )
                                                                 (i32.const 1363612968)
                                                                )
                                                                (i32.const -186632491)
                                                               )
                                                               (i32.const 289752600)
                                                              )
                                                              (i32.const -1101003536)
                                                             )
                                                             (i32.const 377000994)
                                                            )
                                                            (i32.const 691941399)
                                                           )
                                                           (i32.const 100116105)
                                                          )
                                                          (i32.const -1152492455)
                                                         )
                                                         (i32.const 796743407)
                                                        )
                                                        (i32.const 1360020067)
                                                       )
                                                       (i32.const 860156768)
                                                      )
                                                      (i32.const 1151570315)
                                                     )
                                                     (i32.const 989417050)
                                                    )
                                                    (i32.const -198625906)
                                                   )
                                                   (i32.const 251210250)
                                                  )
                                                  (i32.const -2018126414)
                                                 )
                                                 (i32.const 1348860964)
                                                )
                                                (i32.const 474015003)
                                               )
                                               (i32.const 24425134)
                                              )
                                              (i32.const -159637977)
                                             )
                                             (i32.const -1751959236)
                                            )
                                            (i32.const 498725877)
                                           )
                                           (i32.const 1072221483)
                                          )
                                          (i32.const -1699627479)
                                         )
                                         (i32.const 626819767)
                                        )
                                        (i32.const 550693235)
                                       )
                                       (i32.const 2035673625)
                                      )
                                      (i32.const 1916796037)
                                     )
                                     (i32.const -919275339)
                                    )
                                    (i32.const 200199775)
                                   )
                                   (i32.const 1724975570)
                                  )
                                  (i32.const -1733081800)
                                 )
                                 (i32.const 725425613)
                                )
                                (i32.const 407033032)
                               )
                               (i32.const -2030259480)
                              )
                              (i32.const 517747737)
                             )
                             (i32.const 300175651)
                            )
                            (i32.const -509635080)
                           )
                           (i32.const 202533016)
                          )
                          (i32.const -749579607)
                         )
                         (i32.const -1095358918)
                        )
                        (i32.const 1987901760)
                       )
                       (i32.const -1969714010)
                      )
                      (i32.const 650488403)
                     )
                     (i32.const 388020436)
                    )
                    (i32.const 1247455387)
                   )
                   (i32.const 1085256297)
                  )
                  (i32.const 1023479230)
                 )
                 (i32.const 1289279342)
                )
                (i32.const 1444289201)
               )
               (i32.const 1538543862)
              )
              (i32.const -1450452389)
             )
             (i32.const 1926646603)
            )
            (i32.const 1194440157)
           )
           (i32.const -669022682)
          )
          (i32.const 1639888105)
         )
         (i32.const 1443819686)
        )
        (i32.const 659196399)
       )
       (i32.const 2088219325)
      )
      (i32.const 1117389259)
     )
     (i32.const -1501776403)
    )
    (i32.const -2126499213)
   )
   (i32.const 1945412149)
  )
 )
)


(assert_return (invoke "run" (i32.const 0)) (i32.const 361388761))
(assert_return (invoke "run" (i32.const 1)) (i32.const -1029357128))
(assert_return (invoke "run" (i32.const -1)) (i32.const 652822718))
(assert_return (invoke "run" (i32.const 2147483647)) (i32.const -1494660930))
(assert_return (invoke "run" (i32.const -2147483648)) (i32.const -1786094887))
(assert_return (invoke "run" (i32.const 1439807885)) (i32.const -622417300))
(assert_return (invoke "run" (i32.const 735487473)) (i32.const 605868136))
(assert_return (invoke "run" (i32.const -1354098065)) (i32.const 870145006))
(assert_return (invoke "run" (i32.const -1423089209)) (i32.const -316833162))
(assert_return (invoke "run" (i32.const -2076200602)) (i32.const 124082175))
(assert_return (invoke "run" (i32.const -2081775675)) (i32.const -833193004))
(assert_return (invoke "run" (i32.const -549694564)) (i32.const -561448915))
(assert_return (invoke "run" (i32.const 1045288149)) (i32.const 93716580))
(assert_return (invoke "run" (i32.const -316526290)) (i32.const -1848824265))
(assert_return (invoke "run" (i32.const 1113848457)) (i32.const -2140146448))
(assert_return (invoke "run" (i32.const -2104553301)) (i32.const -718555246))
(assert_return (invoke "run" (i32.const -1013187400)) (i32.const -592470463))
(assert_return (invoke "run" (i32.const -1593572931)) (i32.const 1395564124))
(assert_return (invoke "run" (i32.const 1970151927)) (i32.const 2059420518))
(assert_return (invoke "run" (i32.const -215366785)) (i32.const -873003714))
(assert_return (invoke "run" (i32.const 765994079)) (i32.const -495030946))
(assert_return (invoke "run" (i32.const -848767249)) (i32.const 1053600110))
(assert_return (invoke "run" (i32.const -1062122981)) (i32.const 206747266))
(assert_return (invoke "run" (i32.const -1506150977)) (i32.const -547789698))
(assert_return (invoke "run" (i32.const -1093069495)) (i32.const 1429731760))
(assert_return (invoke "run" (i32.const -993538388)) (i32.const -1608472963))
(assert_return (invoke "run" (i32.const -1927469004)) (i32.const 1475742197))
(assert_return (invoke "run" (i32.const -1533297954)) (i32.const -1201658841))
(assert_return (invoke "run" (i32.const 1108216859)) (i32.const -737910654))
(assert_return (invoke "run" (i32.const 1631121771)) (i32.const -1818950574))
(assert_return (invoke "run" (i32.const -578102494)) (i32.const -2058111805))
(assert_return (invoke "run" (i32.const 37583177)) (i32.const -425802320))
(assert_return (invoke "run" (i32.const -318853137)) (i32.const -846607762))
(assert_return (invoke "run" (i32.const 1812406522)) (i32.const 458103627))
(assert_return (invoke "run" (i32.const 297362373)) (i32.const -2090899500))
(assert_return (invoke "run" (i32.const 30909278)) (i32.const -586846297))
(assert_return (invoke "run" (i32.const 579271595)) (i32.const -2146391406))
(assert_return (invoke "run" (i32.const 1783574221)) (i32.const -322414932))
(assert_return (invoke "run" (i32.const 1003279277)) (i32.const 1877616588))
(assert_return (invoke "run" (i32.const -1536227457)) (i32.const -1633803970))
(assert_return (invoke "run" (i32.const 1652701294)) (i32.const 1733731959))
(assert_return (invoke "run" (i32.const 824343758)) (i32.const 374280727))
(assert_return (invoke "run" (i32.const -483627099)) (i32.const 367364852))
(assert_return (invoke "run" (i32.const 1783323913)) (i32.const -482874768))
(assert_return (invoke "run" (i32.const -135172651)) (i32.const -663407260))
(assert_return (invoke "run" (i32.const 2144551125)) (i32.const -980753308))
(assert_return (invoke "run" (i32.const 419548952)) (i32.const 1099957473))
(assert_return (invoke "run" (i32.const -1246482534)) (i32.const -69805269))
(assert_return (invoke "run" (i32.const 1074058115)) (i32.const 179734970))
(assert_return (invoke "run" (i32.const 2062123801)) (i32.const 905460928))
(assert_return (invoke "run" (i32.const 1841611273)) (i32.const 524105584))
(assert_return (invoke "run" (i32.const -1366032143)) (i32.const -1531576472))
(assert_return (invoke "run" (i32.const 1123468319)) (i32.const -1828921826))
(assert_return (invoke "run" (i32.const -1967782053)) (i32.const 293579970))
(assert_return (invoke "run" (i32.const -1297319745)) (i32.const -365424770))
(assert_return (invoke "run" (i32.const 1767178498)) (i32.const -1942710557))
(assert_return (invoke "run" (i32.const -222623813)) (i32.const -1812227998))
(assert_return (invoke "run" (i32.const -871968895)) (i32.const 1927023672))
(assert_return (invoke "run" (i32.const -729400527)) (i32.const -856194648))
(assert_return (invoke "run" (i32.const 965411405)) (i32.const 610928428))
(assert_return (invoke "run" (i32.const -1696060288)) (i32.const -1552656295))
(assert_return (invoke "run" (i32.const 50532579)) (i32.const 437588442))
(assert_return (invoke "run" (i32.const 2030112170)) (i32.const 2137469051))
(assert_return (invoke "run" (i32.const 1242893758)) (i32.const 1816032199))
(assert_return (invoke "run" (i32.const -332061202)) (i32.const -2011151625))
(assert_return (invoke "run" (i32.const -1695740976)) (i32.const -431271895))
(assert_return (invoke "run" (i32.const 921098366)) (i32.const -740818553))
(assert_return (invoke "run" (i32.const 1850940690)) (i32.const -549613517))
(assert_return (invoke "run" (i32.const 702632848)) (i32.const -298877975))
(assert_return (invoke "run" (i32.const -1202219414)) (i32.const -1080790213))
(assert_return (invoke "run" (i32.const -1035324349)) (i32.const 815198842))
(assert_return (invoke "run" (i32.const 2062587542)) (i32.const 241704687))
(assert_return (invoke "run" (i32.const -1179652927)) (i32.const 1271913336))
(assert_return (invoke "run" (i32.const -650722529)) (i32.const -1026312930))
(assert_return (invoke "run" (i32.const 1313075833)) (i32.const -1024077600))
(assert_return (invoke "run" (i32.const 1569799297)) (i32.const 1336298808))
(assert_return (invoke "run" (i32.const 1893904943)) (i32.const -1990404690))
(assert_return (invoke "run" (i32.const -1573126969)) (i32.const 1178493302))
(assert_return (invoke "run" (i32.const -1747075814)) (i32.const 478508459))
(assert_return (invoke "run" (i32.const -1831318300)) (i32.const -689010011))
(assert_return (invoke "run" (i32.const 828209559)) (i32.const 1366538566))
(assert_return (invoke "run" (i32.const -1118601167)) (i32.const -1649023320))
(assert_return (invoke "run" (i32.const 1194882190)) (i32.const 1034107351))
(assert_return (invoke "run" (i32.const -1328624283)) (i32.const 1620632244))
(assert_return (invoke "run" (i32.const -802255968)) (i32.const 35805497))
(assert_return (invoke "run" (i32.const -546674545)) (i32.const -739994674))
(assert_return (invoke "run" (i32.const 908564656)) (i32.const 231248713))
(assert_return (invoke "run" (i32.const 644960068)) (i32.const -134322491))
(assert_return (invoke "run" (i32.const -812432126)) (i32.const 1713701603))
(assert_return (invoke "run" (i32.const -706694111)) (i32.const 1136128280))
(assert_return (invoke "run" (i32.const 1276411428)) (i32.const -576228891))
(assert_return (invoke "run" (i32.const 1006907310)) (i32.const -1694015561))
(assert_return (invoke "run" (i32.const 1811177577)) (i32.const -613398000))
(assert_return (invoke "run" (i32.const -1827735071)) (i32.const -474912296))
(assert_return (invoke "run" (i32.const 1179545156)) (i32.const -2109256251))
(assert_return (invoke "run" (i32.const -1213130606)) (i32.const -1905464653))
(assert_return (invoke "run" (i32.const -1444089142)) (i32.const 1227892699))
(assert_return (invoke "run" (i32.const 753916695)) (i32.const 1144013766))
(assert_return (invoke "run" (i32.const -1918695572)) (i32.const 858217533))
(assert_return (invoke "run" (i32.const 1314115681)) (i32.const -236183720))
(assert_return (invoke "run" (i32.const 1201323280)) (i32.const 1615366249))
(assert_return (invoke "run" (i32.const 784984526)) (i32.const -63217897))
(assert_return (invoke "run" (i32.const -1042597320)) (i32.const -535996223))
(assert_return (invoke "run" (i32.const 519463986)) (i32.const -1079413741))
(assert_return (invoke "run" (i32.const -581718993)) (i32.const -1459089490))