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
(assert_return (invoke "run" (i32.const -2125947188)) (i32.const 1986226909))
(assert_return (invoke "run" (i32.const 886513954)) (i32.const 1923666627))
(assert_return (invoke "run" (i32.const -355755751)) (i32.const 1180488384))
(assert_return (invoke "run" (i32.const 1985950617)) (i32.const 350974528))
(assert_return (invoke "run" (i32.const -694720438)) (i32.const 1031111771))
(assert_return (invoke "run" (i32.const -1633466769)) (i32.const -273866770))
(assert_return (invoke "run" (i32.const 439023076)) (i32.const -573173851))
(assert_return (invoke "run" (i32.const -1675105818)) (i32.const 2115236735))
(assert_return (invoke "run" (i32.const -1737768465)) (i32.const 1647406190))
(assert_return (invoke "run" (i32.const 1815921605)) (i32.const -722860076))
(assert_return (invoke "run" (i32.const 680987066)) (i32.const 1686665995))
(assert_return (invoke "run" (i32.const 1614896409)) (i32.const -1616650560))
(assert_return (invoke "run" (i32.const 552618487)) (i32.const 2102164326))
(assert_return (invoke "run" (i32.const 621217670)) (i32.const -11089057))
(assert_return (invoke "run" (i32.const -800040551)) (i32.const -580456384))
(assert_return (invoke "run" (i32.const 482357819)) (i32.const -1960990750))
(assert_return (invoke "run" (i32.const -777169429)) (i32.const 494854098))
(assert_return (invoke "run" (i32.const -697391315)) (i32.const -1331528628))
(assert_return (invoke "run" (i32.const -1400161921)) (i32.const -992632002))
(assert_return (invoke "run" (i32.const -1793960829)) (i32.const 236681914))
(assert_return (invoke "run" (i32.const 1006588506)) (i32.const -669038869))
(assert_return (invoke "run" (i32.const -386003786)) (i32.const -1286920625))
(assert_return (invoke "run" (i32.const -2035066740)) (i32.const -705898595))
(assert_return (invoke "run" (i32.const 1429441206)) (i32.const 843019343))
(assert_return (invoke "run" (i32.const 1913521919)) (i32.const 1454670782))
(assert_return (invoke "run" (i32.const 2132685114)) (i32.const 309213579))
(assert_return (invoke "run" (i32.const 154434754)) (i32.const 76407459))
(assert_return (invoke "run" (i32.const -1743784140)) (i32.const 1181977845))
(assert_return (invoke "run" (i32.const 1935980271)) (i32.const -1919628946))
(assert_return (invoke "run" (i32.const -1090755237)) (i32.const 1313989314))
(assert_return (invoke "run" (i32.const -1424817594)) (i32.const -633638113))
(assert_return (invoke "run" (i32.const 775295385)) (i32.const 1084520512))
(assert_return (invoke "run" (i32.const 909194684)) (i32.const 736887181))
(assert_return (invoke "run" (i32.const 1720194964)) (i32.const 1875625109))
(assert_return (invoke "run" (i32.const -771942849)) (i32.const -1137815042))
(assert_return (invoke "run" (i32.const 1082957442)) (i32.const -1691546269))
(assert_return (invoke "run" (i32.const 1609349603)) (i32.const 554082010))
(assert_return (invoke "run" (i32.const 485558460)) (i32.const -640547699))
(assert_return (invoke "run" (i32.const 1224787706)) (i32.const 691798347))
(assert_return (invoke "run" (i32.const 625879175)) (i32.const -855642058))
(assert_return (invoke "run" (i32.const 290219995)) (i32.const 1571865666))
(assert_return (invoke "run" (i32.const 1782989615)) (i32.const 872007342))
(assert_return (invoke "run" (i32.const -1318475554)) (i32.const 418587175))
(assert_return (invoke "run" (i32.const 958982726)) (i32.const 1042639647))
(assert_return (invoke "run" (i32.const -1388821619)) (i32.const -2114691988))
(assert_return (invoke "run" (i32.const 1578804594)) (i32.const 1384896851))
(assert_return (invoke "run" (i32.const 629681576)) (i32.const 1284420977))
(assert_return (invoke "run" (i32.const 1800359106)) (i32.const 299414179))
(assert_return (invoke "run" (i32.const -1621606161)) (i32.const -1260002450))
(assert_return (invoke "run" (i32.const 497840859)) (i32.const -195904702))
(assert_return (invoke "run" (i32.const 982892974)) (i32.const -1455877705))
(assert_return (invoke "run" (i32.const 1165694446)) (i32.const 101741303))
(assert_return (invoke "run" (i32.const 1805166404)) (i32.const 1140698821))
(assert_return (invoke "run" (i32.const -2088860128)) (i32.const -889598279))
(assert_return (invoke "run" (i32.const -2089474372)) (i32.const -1821545843))
(assert_return (invoke "run" (i32.const 1015921763)) (i32.const 904930394))
(assert_return (invoke "run" (i32.const 1998157020)) (i32.const -571002771))
(assert_return (invoke "run" (i32.const 1830069196)) (i32.const -170070051))
(assert_return (invoke "run" (i32.const 1706590248)) (i32.const -1936215311))
(assert_return (invoke "run" (i32.const 1289109081)) (i32.const 2084394496))
(assert_return (invoke "run" (i32.const 396437902)) (i32.const 1134692055))
(assert_return (invoke "run" (i32.const 2027523122)) (i32.const -808670189))
(assert_return (invoke "run" (i32.const 172680372)) (i32.const -991232139))
(assert_return (invoke "run" (i32.const -115182060)) (i32.const 2139087381))
(assert_return (invoke "run" (i32.const -2122733441)) (i32.const 773423678))
(assert_return (invoke "run" (i32.const -906714482)) (i32.const 1800232919))
(assert_return (invoke "run" (i32.const 567300227)) (i32.const -2088698182))
(assert_return (invoke "run" (i32.const -1851402506)) (i32.const 183303311))
(assert_return (invoke "run" (i32.const -1069990018)) (i32.const -930206585))
(assert_return (invoke "run" (i32.const -544236028)) (i32.const -1980103035))
(assert_return (invoke "run" (i32.const -767605569)) (i32.const 1004589950))
(assert_return (invoke "run" (i32.const 144240215)) (i32.const 1610560006))
(assert_return (invoke "run" (i32.const -189620332)) (i32.const -611386219))
(assert_return (invoke "run" (i32.const 1888196109)) (i32.const -1447622164))
(assert_return (invoke "run" (i32.const -1643086561)) (i32.const -429908194))
(assert_return (invoke "run" (i32.const -1447622647)) (i32.const 1284199792))
(assert_return (invoke "run" (i32.const -1070726212)) (i32.const -931524723))
(assert_return (invoke "run" (i32.const -1076411060)) (i32.const -144649635))
(assert_return (invoke "run" (i32.const -1725156306)) (i32.const -1580183241))
(assert_return (invoke "run" (i32.const 1397937778)) (i32.const -1114510765))
(assert_return (invoke "run" (i32.const 1602900463)) (i32.const -1702396818))
(assert_return (invoke "run" (i32.const 1012161657)) (i32.const 1789158112))
(assert_return (invoke "run" (i32.const 1865898136)) (i32.const 466122081))
(assert_return (invoke "run" (i32.const 257647942)) (i32.const 1325766175))
(assert_return (invoke "run" (i32.const -1671037200)) (i32.const -1685423735))
(assert_return (invoke "run" (i32.const -1197765934)) (i32.const -1006414093))
(assert_return (invoke "run" (i32.const 2119847088)) (i32.const 1198448457))
(assert_return (invoke "run" (i32.const 630402221)) (i32.const 1518625996))
(assert_return (invoke "run" (i32.const -206398835)) (i32.const -1621778580))
(assert_return (invoke "run" (i32.const 315300252)) (i32.const 5131821))
(assert_return (invoke "run" (i32.const -1613629924)) (i32.const 2073519533))
(assert_return (invoke "run" (i32.const 1095156634)) (i32.const 1615050539))
(assert_return (invoke "run" (i32.const 432170971)) (i32.const 1579861058))
(assert_return (invoke "run" (i32.const -1572480628)) (i32.const -1408869219))
(assert_return (invoke "run" (i32.const -1240489770)) (i32.const -745840593))
(assert_return (invoke "run" (i32.const -490985941)) (i32.const -2006500846))
(assert_return (invoke "run" (i32.const 1206962271)) (i32.const -1605023394))
(assert_return (invoke "run" (i32.const 1001410524)) (i32.const 1811900269))
(assert_return (invoke "run" (i32.const 1707199260)) (i32.const -495335763))
(assert_return (invoke "run" (i32.const 350464899)) (i32.const -1833496134))