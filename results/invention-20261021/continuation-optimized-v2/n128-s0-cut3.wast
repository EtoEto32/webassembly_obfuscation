(module
 (type $0 (func (param i32) (result i32)))
 (type $1 (cont $0))
 (type $2 (func (result i32 (ref $1))))
 (tag $tag$0 (type $0) (param i32) (result i32))
 (export "run" (func $1))
 (func $0 (param $0 i32) (result i32)
  (i32.sub
   (i32.mul
    (i32.xor
     (i32.sub
      (i32.xor
       (i32.sub
        (i32.mul
         (i32.xor
          (i32.mul
           (i32.add
            (i32.mul
             (suspend $tag$0
              (i32.add
               (i32.xor
                (i32.sub
                 (i32.xor
                  (i32.sub
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
                             (i32.mul
                              (i32.xor
                               (i32.sub
                                (i32.mul
                                 (i32.xor
                                  (i32.mul
                                   (i32.add
                                    (i32.mul
                                     (i32.xor
                                      (i32.sub
                                       (i32.xor
                                        (i32.add
                                         (i32.xor
                                          (i32.mul
                                           (i32.sub
                                            (i32.xor
                                             (i32.mul
                                              (i32.add
                                               (i32.xor
                                                (i32.mul
                                                 (i32.xor
                                                  (i32.add
                                                   (i32.xor
                                                    (i32.sub
                                                     (i32.mul
                                                      (i32.xor
                                                       (local.get $0)
                                                       (i32.const -916281357)
                                                      )
                                                      (i32.const 105522927)
                                                     )
                                                     (i32.const 2092832990)
                                                    )
                                                    (i32.const 1398200373)
                                                   )
                                                   (i32.const 1187926990)
                                                  )
                                                  (i32.const -1115366506)
                                                 )
                                                 (i32.const -1680863929)
                                                )
                                                (i32.const 1362733542)
                                               )
                                               (i32.const 1524397849)
                                              )
                                              (i32.const 1724528401)
                                             )
                                             (i32.const 1199644010)
                                            )
                                            (i32.const 952439417)
                                           )
                                           (i32.const 835094879)
                                          )
                                          (i32.const -1098189841)
                                         )
                                         (i32.const 1908418210)
                                        )
                                        (i32.const -652239398)
                                       )
                                       (i32.const 403575380)
                                      )
                                      (i32.const -1265133464)
                                     )
                                     (i32.const 241355563)
                                    )
                                    (i32.const 1555272235)
                                   )
                                   (i32.const 357387035)
                                  )
                                  (i32.const -1021086625)
                                 )
                                 (i32.const 1307262395)
                                )
                                (i32.const 179941406)
                               )
                               (i32.const -1117384748)
                              )
                              (i32.const -340290105)
                             )
                             (i32.const 1439814647)
                            )
                            (i32.const -589580971)
                           )
                           (i32.const 383015144)
                          )
                          (i32.const -728907737)
                         )
                         (i32.const 878079986)
                        )
                        (i32.const 813827519)
                       )
                       (i32.const -1373621295)
                      )
                      (i32.const 1669003632)
                     )
                     (i32.const -533442295)
                    )
                    (i32.const -35348265)
                   )
                   (i32.const 806747316)
                  )
                  (i32.const 913641402)
                 )
                 (i32.const 377462705)
                )
                (i32.const -1722060845)
               )
               (i32.const 625845245)
              )
             )
             (i32.const -667333309)
            )
            (i32.const 773100918)
           )
           (i32.const 1304937859)
          )
          (i32.const -2101169997)
         )
         (i32.const 1792939973)
        )
        (i32.const 1949548209)
       )
       (i32.const -824209873)
      )
      (i32.const 81524208)
     )
     (i32.const -51722228)
    )
    (i32.const 1272178459)
   )
   (i32.const 1453778579)
  )
 )
 (func $1 (param $0 i32) (result i32)
  (local $1 i32)
  (local $2 (ref $1))
  (local $scratch (tuple i32 (ref $1)))
  (local $scratch_4 i32)
  (resume $1
   (i32.xor
    (i32.add
     (i32.xor
      (i32.sub
       (i32.xor
        (i32.add
         (i32.xor
          (i32.sub
           (i32.xor
            (i32.add
             (i32.mul
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
              (i32.const 1922440705)
             )
             (i32.const 1517299295)
            )
            (i32.const 961414185)
           )
           (i32.const 738513968)
          )
          (i32.const 1637294445)
         )
         (i32.const 1664357377)
        )
        (i32.const -1610117940)
       )
       (i32.const 126846742)
      )
      (i32.const 195066198)
     )
     (i32.const 1063828218)
    )
    (i32.const -99822529)
   )
   (local.get $2)
  )
 )
)


(assert_return (invoke "run" (i32.const 0)) (i32.const -2066237316))
(assert_return (invoke "run" (i32.const 1)) (i32.const 117642133))
(assert_return (invoke "run" (i32.const -1)) (i32.const -667706965))
(assert_return (invoke "run" (i32.const 2147483647)) (i32.const 1479776683))
(assert_return (invoke "run" (i32.const -2147483648)) (i32.const 81246332))
(assert_return (invoke "run" (i32.const -389434974)) (i32.const 648380614))
(assert_return (invoke "run" (i32.const -1620833623)) (i32.const 1963339949))
(assert_return (invoke "run" (i32.const 887098274)) (i32.const 110917318))
(assert_return (invoke "run" (i32.const -1129671413)) (i32.const 151045631))
(assert_return (invoke "run" (i32.const -1979682468)) (i32.const -1619762480))
(assert_return (invoke "run" (i32.const 929345397)) (i32.const -905733007))
(assert_return (invoke "run" (i32.const 2021885010)) (i32.const -883797642))
(assert_return (invoke "run" (i32.const 1313218691)) (i32.const 641998791))
(assert_return (invoke "run" (i32.const 1557471999)) (i32.const -285149525))
(assert_return (invoke "run" (i32.const -245355468)) (i32.const 1197554680))
(assert_return (invoke "run" (i32.const -1965038393)) (i32.const 301101443))
(assert_return (invoke "run" (i32.const 1674199203)) (i32.const -1333143321))
(assert_return (invoke "run" (i32.const -1450691728)) (i32.const -418216596))
(assert_return (invoke "run" (i32.const -143056550)) (i32.const -664127538))
(assert_return (invoke "run" (i32.const -2034030022)) (i32.const -1381771730))
(assert_return (invoke "run" (i32.const 1445806584)) (i32.const 722102468))
(assert_return (invoke "run" (i32.const -1017744745)) (i32.const 627035347))
(assert_return (invoke "run" (i32.const -545457759)) (i32.const -2095771723))
(assert_return (invoke "run" (i32.const -1855831309)) (i32.const 1944235831))
(assert_return (invoke "run" (i32.const 314142341)) (i32.const 2054563457))
(assert_return (invoke "run" (i32.const 643012599)) (i32.const -134354765))
(assert_return (invoke "run" (i32.const 107505279)) (i32.const -759167957))
(assert_return (invoke "run" (i32.const -765960391)) (i32.const -2106469187))
(assert_return (invoke "run" (i32.const 703755022)) (i32.const 1285031146))
(assert_return (invoke "run" (i32.const -1141672943)) (i32.const 130105957))
(assert_return (invoke "run" (i32.const 1621057998)) (i32.const 714254634))
(assert_return (invoke "run" (i32.const 241714798)) (i32.const 933037770))
(assert_return (invoke "run" (i32.const -1326429521)) (i32.const 27174491))
(assert_return (invoke "run" (i32.const -81831057)) (i32.const 2018977435))
(assert_return (invoke "run" (i32.const -1162190561)) (i32.const -1351755829))
(assert_return (invoke "run" (i32.const -1638451051)) (i32.const 1276595089))
(assert_return (invoke "run" (i32.const 2142072819)) (i32.const 1986384439))
(assert_return (invoke "run" (i32.const -1486650359)) (i32.const -1127768307))
(assert_return (invoke "run" (i32.const -1846654751)) (i32.const 278305909))
(assert_return (invoke "run" (i32.const 1413763732)) (i32.const 1447803096))
(assert_return (invoke "run" (i32.const -1429134353)) (i32.const -141516517))
(assert_return (invoke "run" (i32.const 1095206590)) (i32.const -1962923814))
(assert_return (invoke "run" (i32.const -1100361079)) (i32.const -1297223795))
(assert_return (invoke "run" (i32.const -324566712)) (i32.const 1756266964))
(assert_return (invoke "run" (i32.const 3964285)) (i32.const 650116969))
(assert_return (invoke "run" (i32.const -2139864082)) (i32.const 324396106))
(assert_return (invoke "run" (i32.const 1044354731)) (i32.const 1630476703))
(assert_return (invoke "run" (i32.const 2066216677)) (i32.const 1603583713))
(assert_return (invoke "run" (i32.const 1326405089)) (i32.const -2006798475))
(assert_return (invoke "run" (i32.const -1863901785)) (i32.const 1462348259))
(assert_return (invoke "run" (i32.const 2050945343)) (i32.const 1950245739))
(assert_return (invoke "run" (i32.const -1998335077)) (i32.const -1098957745))
(assert_return (invoke "run" (i32.const 1738082007)) (i32.const -1641540973))
(assert_return (invoke "run" (i32.const -1229692496)) (i32.const 1776736044))
(assert_return (invoke "run" (i32.const 1219474943)) (i32.const 220545963))
(assert_return (invoke "run" (i32.const 1175977576)) (i32.const -1545248140))
(assert_return (invoke "run" (i32.const -1780567116)) (i32.const 168734072))
(assert_return (invoke "run" (i32.const 984528743)) (i32.const -1870012637))
(assert_return (invoke "run" (i32.const -620036914)) (i32.const 1460002346))
(assert_return (invoke "run" (i32.const 568596829)) (i32.const -2049968823))
(assert_return (invoke "run" (i32.const -149293832)) (i32.const 1099144644))
(assert_return (invoke "run" (i32.const -1781621935)) (i32.const 1245835301))
(assert_return (invoke "run" (i32.const -1549074067)) (i32.const 765785625))
(assert_return (invoke "run" (i32.const -1415632668)) (i32.const -467575384))
(assert_return (invoke "run" (i32.const -1140540415)) (i32.const -1554698347))
(assert_return (invoke "run" (i32.const 409916543)) (i32.const 1818404395))
(assert_return (invoke "run" (i32.const 2072281464)) (i32.const -1516140988))
(assert_return (invoke "run" (i32.const 1950133700)) (i32.const 514793096))
(assert_return (invoke "run" (i32.const 1224680579)) (i32.const 1347957703))
(assert_return (invoke "run" (i32.const -1151387104)) (i32.const -1443641700))
(assert_return (invoke "run" (i32.const 1083608238)) (i32.const 1546599050))
(assert_return (invoke "run" (i32.const -1673923244)) (i32.const -844312040))
(assert_return (invoke "run" (i32.const -487971509)) (i32.const 1295597759))
(assert_return (invoke "run" (i32.const 1053522814)) (i32.const 1418152986))
(assert_return (invoke "run" (i32.const 984472055)) (i32.const 1302292147))
(assert_return (invoke "run" (i32.const -70696557)) (i32.const -1522823593))
(assert_return (invoke "run" (i32.const 1177834659)) (i32.const -1370395417))
(assert_return (invoke "run" (i32.const 488849954)) (i32.const 1520053574))
(assert_return (invoke "run" (i32.const -1564685907)) (i32.const -46612007))
(assert_return (invoke "run" (i32.const 12008035)) (i32.const -830699481))
(assert_return (invoke "run" (i32.const 1352986189)) (i32.const 2065822457))
(assert_return (invoke "run" (i32.const -589458622)) (i32.const 1503172582))
(assert_return (invoke "run" (i32.const 1185695602)) (i32.const -796984042))
(assert_return (invoke "run" (i32.const 997838580)) (i32.const -1761530056))
(assert_return (invoke "run" (i32.const 1254011688)) (i32.const -798310732))
(assert_return (invoke "run" (i32.const -2074580898)) (i32.const -578099718))
(assert_return (invoke "run" (i32.const 1263907340)) (i32.const 1228870976))
(assert_return (invoke "run" (i32.const -1995642504)) (i32.const 1691594308))
(assert_return (invoke "run" (i32.const -1384363801)) (i32.const 1822909603))
(assert_return (invoke "run" (i32.const 143913638)) (i32.const -1747361518))
(assert_return (invoke "run" (i32.const -1517158425)) (i32.const -1294486109))
(assert_return (invoke "run" (i32.const 2109691070)) (i32.const 758799066))
(assert_return (invoke "run" (i32.const 1455511959)) (i32.const 1855200723))
(assert_return (invoke "run" (i32.const 311434325)) (i32.const 904103121))
(assert_return (invoke "run" (i32.const -1563770353)) (i32.const -1117778629))
(assert_return (invoke "run" (i32.const -800473717)) (i32.const 1944696447))
(assert_return (invoke "run" (i32.const 323539148)) (i32.const 171251584))
(assert_return (invoke "run" (i32.const 834869975)) (i32.const -728217965))
(assert_return (invoke "run" (i32.const 653651795)) (i32.const 183461271))
(assert_return (invoke "run" (i32.const -390855045)) (i32.const -1144384977))
(assert_return (invoke "run" (i32.const -1613639712)) (i32.const -46632484))
(assert_return (invoke "run" (i32.const 109223448)) (i32.const 464016356))
(assert_return (invoke "run" (i32.const 1511945774)) (i32.const 593219594))
(assert_return (invoke "run" (i32.const 1206433629)) (i32.const -847429815))
(assert_return (invoke "run" (i32.const 1093421365)) (i32.const 1743214513))