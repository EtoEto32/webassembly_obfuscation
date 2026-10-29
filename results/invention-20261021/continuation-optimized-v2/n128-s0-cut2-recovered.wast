(module
 (type $0 (func (param i32) (result i32)))
 (export "run" (func $0))
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
                                         (i32.const 1945639587)
                                        )
                                        (i32.const 1085542029)
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
)


(assert_return (invoke "run" (i32.const 0)) (i32.const -2066237316))
(assert_return (invoke "run" (i32.const 1)) (i32.const 117642133))
(assert_return (invoke "run" (i32.const -1)) (i32.const -667706965))
(assert_return (invoke "run" (i32.const 2147483647)) (i32.const 1479776683))
(assert_return (invoke "run" (i32.const -2147483648)) (i32.const 81246332))
(assert_return (invoke "run" (i32.const 191856078)) (i32.const 1783772458))
(assert_return (invoke "run" (i32.const -880674720)) (i32.const 691215964))
(assert_return (invoke "run" (i32.const -518953054)) (i32.const -1404853562))
(assert_return (invoke "run" (i32.const 1096380661)) (i32.const -2090843151))
(assert_return (invoke "run" (i32.const -878381362)) (i32.const -1767818198))
(assert_return (invoke "run" (i32.const -725179333)) (i32.const 1265433967))
(assert_return (invoke "run" (i32.const -858097194)) (i32.const 160417474))
(assert_return (invoke "run" (i32.const -853727512)) (i32.const -1911301388))
(assert_return (invoke "run" (i32.const 1348460140)) (i32.const 474195616))
(assert_return (invoke "run" (i32.const -1359947844)) (i32.const 1563493936))
(assert_return (invoke "run" (i32.const 1541714424)) (i32.const 997251268))
(assert_return (invoke "run" (i32.const 1120183079)) (i32.const 1792839523))
(assert_return (invoke "run" (i32.const 1254697373)) (i32.const 1950821385))
(assert_return (invoke "run" (i32.const 78014144)) (i32.const -151510084))
(assert_return (invoke "run" (i32.const -672459120)) (i32.const -261357428))
(assert_return (invoke "run" (i32.const -349625879)) (i32.const 1796492397))
(assert_return (invoke "run" (i32.const -1543891491)) (i32.const -760414263))
(assert_return (invoke "run" (i32.const -1112855162)) (i32.const -90935182))
(assert_return (invoke "run" (i32.const -1071399922)) (i32.const 775526378))
(assert_return (invoke "run" (i32.const 1704248356)) (i32.const 1101458280))
(assert_return (invoke "run" (i32.const 371850471)) (i32.const 924657827))
(assert_return (invoke "run" (i32.const 1588660276)) (i32.const -1737771016))
(assert_return (invoke "run" (i32.const -574447297)) (i32.const -621620373))
(assert_return (invoke "run" (i32.const -91190909)) (i32.const 4430535))
(assert_return (invoke "run" (i32.const -1601525049)) (i32.const -155493501))
(assert_return (invoke "run" (i32.const 211033703)) (i32.const -844675037))
(assert_return (invoke "run" (i32.const 1922445203)) (i32.const 1279305815))
(assert_return (invoke "run" (i32.const -193442779)) (i32.const -76633695))
(assert_return (invoke "run" (i32.const -663275126)) (i32.const -486492290))
(assert_return (invoke "run" (i32.const 561061211)) (i32.const 1176684943))
(assert_return (invoke "run" (i32.const 1036472653)) (i32.const -1492348935))
(assert_return (invoke "run" (i32.const -1806837244)) (i32.const -1949817784))
(assert_return (invoke "run" (i32.const -1612768948)) (i32.const -1433346048))
(assert_return (invoke "run" (i32.const -1688840708)) (i32.const 1454583792))
(assert_return (invoke "run" (i32.const -1645121983)) (i32.const 562445141))
(assert_return (invoke "run" (i32.const -1666004687)) (i32.const 1321161605))
(assert_return (invoke "run" (i32.const -1575770300)) (i32.const 668873736))
(assert_return (invoke "run" (i32.const -1617282116)) (i32.const -1335350736))
(assert_return (invoke "run" (i32.const -268047820)) (i32.const 338210296))
(assert_return (invoke "run" (i32.const -1543229133)) (i32.const -1711814153))
(assert_return (invoke "run" (i32.const -1476446758)) (i32.const -200064434))
(assert_return (invoke "run" (i32.const -492457406)) (i32.const -450883354))
(assert_return (invoke "run" (i32.const 813035205)) (i32.const 314460481))
(assert_return (invoke "run" (i32.const -525606924)) (i32.const -227408328))
(assert_return (invoke "run" (i32.const -1411490716)) (i32.const 1214148392))
(assert_return (invoke "run" (i32.const 1738790782)) (i32.const 307001370))
(assert_return (invoke "run" (i32.const -1892058443)) (i32.const 1678685489))
(assert_return (invoke "run" (i32.const 1467199843)) (i32.const -527739609))
(assert_return (invoke "run" (i32.const -560672970)) (i32.const -801303646))
(assert_return (invoke "run" (i32.const -347603284)) (i32.const 1841587552))
(assert_return (invoke "run" (i32.const 2144597228)) (i32.const -216697056))
(assert_return (invoke "run" (i32.const -4922213)) (i32.const -1393713329))
(assert_return (invoke "run" (i32.const 687795111)) (i32.const 715998179))
(assert_return (invoke "run" (i32.const 1752469322)) (i32.const -969640770))
(assert_return (invoke "run" (i32.const -355349344)) (i32.const -518673636))
(assert_return (invoke "run" (i32.const 924326297)) (i32.const 226515613))
(assert_return (invoke "run" (i32.const 700130815)) (i32.const -1679395925))
(assert_return (invoke "run" (i32.const 190406104)) (i32.const -496209628))
(assert_return (invoke "run" (i32.const 2084439620)) (i32.const -1108595448))
(assert_return (invoke "run" (i32.const 1453675215)) (i32.const 312254075))
(assert_return (invoke "run" (i32.const 335185967)) (i32.const 692238299))
(assert_return (invoke "run" (i32.const -1280401189)) (i32.const -1029927153))
(assert_return (invoke "run" (i32.const -210171262)) (i32.const 789015974))
(assert_return (invoke "run" (i32.const 215732323)) (i32.const -437853657))
(assert_return (invoke "run" (i32.const 1938612517)) (i32.const -1408618335))
(assert_return (invoke "run" (i32.const -771112028)) (i32.const -390673176))
(assert_return (invoke "run" (i32.const 2111427111)) (i32.const -1916180381))
(assert_return (invoke "run" (i32.const 1259299952)) (i32.const -809545620))
(assert_return (invoke "run" (i32.const -369937383)) (i32.const 771754781))
(assert_return (invoke "run" (i32.const -1503776280)) (i32.const 1088214004))
(assert_return (invoke "run" (i32.const -665418015)) (i32.const 2084736629))
(assert_return (invoke "run" (i32.const 682148930)) (i32.const 355589862))
(assert_return (invoke "run" (i32.const 961417003)) (i32.const 972676127))
(assert_return (invoke "run" (i32.const -1256680405)) (i32.const 366411551))
(assert_return (invoke "run" (i32.const -1640414136)) (i32.const -1766080812))
(assert_return (invoke "run" (i32.const 1117517264)) (i32.const 793315660))
(assert_return (invoke "run" (i32.const -1668567640)) (i32.const -1784576716))
(assert_return (invoke "run" (i32.const 1736707127)) (i32.const -1239518605))
(assert_return (invoke "run" (i32.const -1826629413)) (i32.const 2117986063))
(assert_return (invoke "run" (i32.const 1336026147)) (i32.const 2051604071))
(assert_return (invoke "run" (i32.const 1884391963)) (i32.const 1948580047))
(assert_return (invoke "run" (i32.const 979172660)) (i32.const -1809076488))
(assert_return (invoke "run" (i32.const -706993851)) (i32.const -1246646847))
(assert_return (invoke "run" (i32.const -1005225416)) (i32.const 506030980))
(assert_return (invoke "run" (i32.const 1982208657)) (i32.const 891689701))
(assert_return (invoke "run" (i32.const 460277817)) (i32.const -1530174531))
(assert_return (invoke "run" (i32.const 1537498210)) (i32.const 218152710))
(assert_return (invoke "run" (i32.const -549375351)) (i32.const -227061875))
(assert_return (invoke "run" (i32.const 702192207)) (i32.const 310722043))
(assert_return (invoke "run" (i32.const -779422393)) (i32.const 141257219))
(assert_return (invoke "run" (i32.const 1211479112)) (i32.const 2032692948))
(assert_return (invoke "run" (i32.const -500720673)) (i32.const -1297174261))
(assert_return (invoke "run" (i32.const -651949071)) (i32.const 2018401477))
(assert_return (invoke "run" (i32.const -1551438685)) (i32.const -1255201561))
(assert_return (invoke "run" (i32.const 1310469700)) (i32.const 2074998024))
(assert_return (invoke "run" (i32.const -1887616313)) (i32.const -1130409085))
(assert_return (invoke "run" (i32.const 1941133135)) (i32.const -682436357))
(assert_return (invoke "run" (i32.const -2031331074)) (i32.const -1759813222))
(assert_return (invoke "run" (i32.const 867426245)) (i32.const 179908673))
(assert_return (invoke "run" (i32.const 1941211410)) (i32.const -927288906))