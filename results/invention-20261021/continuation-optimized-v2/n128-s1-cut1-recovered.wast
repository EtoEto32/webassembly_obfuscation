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
                (i32.sub
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
                                                     (i32.sub
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
                                                      (i32.const 136700953)
                                                     )
                                                     (i32.const 1151570315)
                                                    )
                                                    (i32.const 2018069447)
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
                 (i32.const 1982208724)
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
(assert_return (invoke "run" (i32.const -2088564431)) (i32.const -944601176))
(assert_return (invoke "run" (i32.const 949404405)) (i32.const -2023749948))
(assert_return (invoke "run" (i32.const 174797578)) (i32.const -1969577701))
(assert_return (invoke "run" (i32.const 1758827523)) (i32.const 1389834554))
(assert_return (invoke "run" (i32.const 1966670251)) (i32.const 1838917778))
(assert_return (invoke "run" (i32.const 422594924)) (i32.const 528481853))
(assert_return (invoke "run" (i32.const 1816314998)) (i32.const -1398213361))
(assert_return (invoke "run" (i32.const 1974358479)) (i32.const -1077820402))
(assert_return (invoke "run" (i32.const 1691067528)) (i32.const 29630481))
(assert_return (invoke "run" (i32.const 233069847)) (i32.const -830628410))
(assert_return (invoke "run" (i32.const -1011013020)) (i32.const 976276261))
(assert_return (invoke "run" (i32.const -1963987736)) (i32.const 1104861873))
(assert_return (invoke "run" (i32.const -182352429)) (i32.const 1318976522))
(assert_return (invoke "run" (i32.const -1234381983)) (i32.const 629757528))
(assert_return (invoke "run" (i32.const -532219680)) (i32.const 2011515769))
(assert_return (invoke "run" (i32.const 1449772404)) (i32.const 1041697077))
(assert_return (invoke "run" (i32.const -97750289)) (i32.const 948084078))
(assert_return (invoke "run" (i32.const 488430626)) (i32.const -2042702397))
(assert_return (invoke "run" (i32.const 813737178)) (i32.const 1573399147))
(assert_return (invoke "run" (i32.const 1788889292)) (i32.const 426435805))
(assert_return (invoke "run" (i32.const -245374817)) (i32.const 1604005790))
(assert_return (invoke "run" (i32.const -573027593)) (i32.const 1260224614))
(assert_return (invoke "run" (i32.const -1539749824)) (i32.const 1640497689))
(assert_return (invoke "run" (i32.const 1173954111)) (i32.const 1091906046))
(assert_return (invoke "run" (i32.const 1950046466)) (i32.const 704003811))
(assert_return (invoke "run" (i32.const -1088191007)) (i32.const -1510519336))
(assert_return (invoke "run" (i32.const 2123374978)) (i32.const 1900080227))
(assert_return (invoke "run" (i32.const 1882951595)) (i32.const -1349003630))
(assert_return (invoke "run" (i32.const -869289815)) (i32.const 1018618960))
(assert_return (invoke "run" (i32.const 883518457)) (i32.const 1083371360))
(assert_return (invoke "run" (i32.const 1701974033)) (i32.const 717553608))
(assert_return (invoke "run" (i32.const -281667400)) (i32.const -483175871))
(assert_return (invoke "run" (i32.const 1705381217)) (i32.const 1561774168))
(assert_return (invoke "run" (i32.const 719126343)) (i32.const 1594678006))
(assert_return (invoke "run" (i32.const -1696005850)) (i32.const -1380050241))
(assert_return (invoke "run" (i32.const 1733789756)) (i32.const -754274547))
(assert_return (invoke "run" (i32.const 1692645718)) (i32.const -1240978513))
(assert_return (invoke "run" (i32.const -605158163)) (i32.const 1230748684))
(assert_return (invoke "run" (i32.const 1020977392)) (i32.const -1070630007))
(assert_return (invoke "run" (i32.const -1525335887)) (i32.const -361332184))
(assert_return (invoke "run" (i32.const 953246476)) (i32.const 1468382493))
(assert_return (invoke "run" (i32.const -1884148805)) (i32.const 180556898))
(assert_return (invoke "run" (i32.const 135849176)) (i32.const -1608159583))
(assert_return (invoke "run" (i32.const 1342537267)) (i32.const -1739698390))
(assert_return (invoke "run" (i32.const -1421977108)) (i32.const -1116089411))
(assert_return (invoke "run" (i32.const -1616892391)) (i32.const -2038656064))
(assert_return (invoke "run" (i32.const 567414454)) (i32.const -2126581681))
(assert_return (invoke "run" (i32.const 1910418620)) (i32.const -750686067))
(assert_return (invoke "run" (i32.const -1926975555)) (i32.const 884753500))
(assert_return (invoke "run" (i32.const -2132539586)) (i32.const 2130811463))
(assert_return (invoke "run" (i32.const -1623607785)) (i32.const 503006918))
(assert_return (invoke "run" (i32.const -356378444)) (i32.const -2068542603))
(assert_return (invoke "run" (i32.const -945077980)) (i32.const 1741634789))
(assert_return (invoke "run" (i32.const -1831184656)) (i32.const -1072316023))
(assert_return (invoke "run" (i32.const -475674928)) (i32.const -1312566487))
(assert_return (invoke "run" (i32.const 1740673252)) (i32.const 702715557))
(assert_return (invoke "run" (i32.const 1948841091)) (i32.const -983967046))
(assert_return (invoke "run" (i32.const -620361008)) (i32.const 1858711337))
(assert_return (invoke "run" (i32.const 2055024141)) (i32.const 2000933356))
(assert_return (invoke "run" (i32.const 99462810)) (i32.const -2125216213))
(assert_return (invoke "run" (i32.const 2032172186)) (i32.const -1024539605))
(assert_return (invoke "run" (i32.const -340915681)) (i32.const 1077511198))
(assert_return (invoke "run" (i32.const 1389629836)) (i32.const 823067805))
(assert_return (invoke "run" (i32.const 734036442)) (i32.const 96661355))
(assert_return (invoke "run" (i32.const -1860307165)) (i32.const 692953370))
(assert_return (invoke "run" (i32.const 876174731)) (i32.const 1230455602))
(assert_return (invoke "run" (i32.const 720635576)) (i32.const 1416460353))
(assert_return (invoke "run" (i32.const -645879045)) (i32.const 1984153762))
(assert_return (invoke "run" (i32.const 2089139981)) (i32.const -1766397204))
(assert_return (invoke "run" (i32.const 709445831)) (i32.const 1776285046))
(assert_return (invoke "run" (i32.const -2014138981)) (i32.const -997365502))
(assert_return (invoke "run" (i32.const -1687096823)) (i32.const -2012813456))
(assert_return (invoke "run" (i32.const -1243111636)) (i32.const -306776579))
(assert_return (invoke "run" (i32.const 1637780033)) (i32.const 1737225208))
(assert_return (invoke "run" (i32.const 24756459)) (i32.const 601093842))
(assert_return (invoke "run" (i32.const -1664802649)) (i32.const -1890685034))
(assert_return (invoke "run" (i32.const -293401010)) (i32.const 1255264919))
(assert_return (invoke "run" (i32.const -1502667178)) (i32.const 705216687))
(assert_return (invoke "run" (i32.const -1226800653)) (i32.const -86322710))
(assert_return (invoke "run" (i32.const -1757072907)) (i32.const 2042403268))
(assert_return (invoke "run" (i32.const 4540511)) (i32.const 99338590))
(assert_return (invoke "run" (i32.const -1054883537)) (i32.const 1515785390))
(assert_return (invoke "run" (i32.const 425828633)) (i32.const -602428736))
(assert_return (invoke "run" (i32.const -1033424703)) (i32.const 1787733880))
(assert_return (invoke "run" (i32.const 939629153)) (i32.const -1786963624))
(assert_return (invoke "run" (i32.const 2118348428)) (i32.const -805296739))
(assert_return (invoke "run" (i32.const -1647021066)) (i32.const 92830095))
(assert_return (invoke "run" (i32.const 1354855238)) (i32.const -51647457))
(assert_return (invoke "run" (i32.const -1176714398)) (i32.const -1891747837))
(assert_return (invoke "run" (i32.const 475958334)) (i32.const 1296187207))
(assert_return (invoke "run" (i32.const 2105521849)) (i32.const 1053396256))
(assert_return (invoke "run" (i32.const 1867303604)) (i32.const 1621933429))
(assert_return (invoke "run" (i32.const -538309071)) (i32.const -1807113048))
(assert_return (invoke "run" (i32.const -2088291172)) (i32.const -658683603))
(assert_return (invoke "run" (i32.const 1069356176)) (i32.const 1100815593))
(assert_return (invoke "run" (i32.const 1422945128)) (i32.const -486066127))
(assert_return (invoke "run" (i32.const -2042067724)) (i32.const -53055051))
(assert_return (invoke "run" (i32.const -180877676)) (i32.const -1279808619))
(assert_return (invoke "run" (i32.const -1074322742)) (i32.const 1428772827))
(assert_return (invoke "run" (i32.const -999146328)) (i32.const 180654193))