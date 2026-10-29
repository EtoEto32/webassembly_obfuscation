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
                        (i32.const 1922440705)
                       )
                       (i32.const 1496543324)
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
(assert_return (invoke "run" (i32.const 773521975)) (i32.const -141988749))
(assert_return (invoke "run" (i32.const -1716193801)) (i32.const -1348627789))
(assert_return (invoke "run" (i32.const 114614587)) (i32.const 1146837103))
(assert_return (invoke "run" (i32.const -1637008865)) (i32.const -1343029557))
(assert_return (invoke "run" (i32.const 1004020129)) (i32.const 1843173301))
(assert_return (invoke "run" (i32.const 948736007)) (i32.const -2018457533))
(assert_return (invoke "run" (i32.const -1798843894)) (i32.const -1192161794))
(assert_return (invoke "run" (i32.const 683733242)) (i32.const 46904430))
(assert_return (invoke "run" (i32.const 440227049)) (i32.const -1977152147))
(assert_return (invoke "run" (i32.const 1782957961)) (i32.const 1976348301))
(assert_return (invoke "run" (i32.const -619310479)) (i32.const -933537979))
(assert_return (invoke "run" (i32.const 1601977789)) (i32.const 303426857))
(assert_return (invoke "run" (i32.const 2136747512)) (i32.const -1771502396))
(assert_return (invoke "run" (i32.const -1294172818)) (i32.const 831147978))
(assert_return (invoke "run" (i32.const -698935491)) (i32.const 640181929))
(assert_return (invoke "run" (i32.const -104925110)) (i32.const 2114238398))
(assert_return (invoke "run" (i32.const 250388734)) (i32.const 316606874))
(assert_return (invoke "run" (i32.const -719888058)) (i32.const -1998814798))
(assert_return (invoke "run" (i32.const -1776526361)) (i32.const -841936477))
(assert_return (invoke "run" (i32.const -1376637540)) (i32.const 1262823568))
(assert_return (invoke "run" (i32.const -857681950)) (i32.const 267363462))
(assert_return (invoke "run" (i32.const -1489345079)) (i32.const -1472133043))
(assert_return (invoke "run" (i32.const -1338013392)) (i32.const -1792552276))
(assert_return (invoke "run" (i32.const 755310313)) (i32.const -1247906963))
(assert_return (invoke "run" (i32.const 1082144711)) (i32.const 262929027))
(assert_return (invoke "run" (i32.const 335363544)) (i32.const -745615068))
(assert_return (invoke "run" (i32.const 2078207936)) (i32.const -1897070916))
(assert_return (invoke "run" (i32.const 2073482500)) (i32.const -1026923192))
(assert_return (invoke "run" (i32.const -1096069255)) (i32.const 2005031293))
(assert_return (invoke "run" (i32.const 213627272)) (i32.const 1620231316))
(assert_return (invoke "run" (i32.const -918544894)) (i32.const -1034080474))
(assert_return (invoke "run" (i32.const 2133906178)) (i32.const -378040794))
(assert_return (invoke "run" (i32.const 576289371)) (i32.const -674787185))
(assert_return (invoke "run" (i32.const -2013872018)) (i32.const 296312010))
(assert_return (invoke "run" (i32.const 322310525)) (i32.const -912944279))
(assert_return (invoke "run" (i32.const 376077593)) (i32.const 599470621))
(assert_return (invoke "run" (i32.const 1913967921)) (i32.const 1838014341))
(assert_return (invoke "run" (i32.const 43425168)) (i32.const 775219596))
(assert_return (invoke "run" (i32.const 398833615)) (i32.const 1081906555))
(assert_return (invoke "run" (i32.const 231461983)) (i32.const 209164171))
(assert_return (invoke "run" (i32.const 265306059)) (i32.const -1778897089))
(assert_return (invoke "run" (i32.const 1201888982)) (i32.const -587684414))
(assert_return (invoke "run" (i32.const -1702829892)) (i32.const -49498832))
(assert_return (invoke "run" (i32.const 384403893)) (i32.const -521760207))
(assert_return (invoke "run" (i32.const -1935835737)) (i32.const -114718237))
(assert_return (invoke "run" (i32.const -2025576837)) (i32.const 955167279))
(assert_return (invoke "run" (i32.const 1410896772)) (i32.const -1164403256))
(assert_return (invoke "run" (i32.const 1823640795)) (i32.const -1258185969))
(assert_return (invoke "run" (i32.const 656930050)) (i32.const -1721019354))
(assert_return (invoke "run" (i32.const 911894276)) (i32.const -880266424))
(assert_return (invoke "run" (i32.const 1475851465)) (i32.const -188402355))
(assert_return (invoke "run" (i32.const 1499294593)) (i32.const -774429931))
(assert_return (invoke "run" (i32.const -281568156)) (i32.const -610947288))
(assert_return (invoke "run" (i32.const -1957965436)) (i32.const -35379256))
(assert_return (invoke "run" (i32.const 429778374)) (i32.const -645303246))
(assert_return (invoke "run" (i32.const 1293215154)) (i32.const 759129814))
(assert_return (invoke "run" (i32.const -1854885319)) (i32.const 1850708413))
(assert_return (invoke "run" (i32.const -900494576)) (i32.const -1785601780))
(assert_return (invoke "run" (i32.const 586959596)) (i32.const 1843722528))
(assert_return (invoke "run" (i32.const 1639066354)) (i32.const -2146347370))
(assert_return (invoke "run" (i32.const 1956070447)) (i32.const 249635803))
(assert_return (invoke "run" (i32.const 1473355256)) (i32.const 616379588))
(assert_return (invoke "run" (i32.const 69238596)) (i32.const -1461810168))
(assert_return (invoke "run" (i32.const 2055408161)) (i32.const -333469643))
(assert_return (invoke "run" (i32.const -1841308676)) (i32.const -725997072))
(assert_return (invoke "run" (i32.const -1732168492)) (i32.const -794770024))
(assert_return (invoke "run" (i32.const -1114224039)) (i32.const -1978096931))
(assert_return (invoke "run" (i32.const -1078023384)) (i32.const -972458316))
(assert_return (invoke "run" (i32.const -773519246)) (i32.const -1265074154))
(assert_return (invoke "run" (i32.const 1595700534)) (i32.const -1542675038))
(assert_return (invoke "run" (i32.const 2022515149)) (i32.const -122280327))
(assert_return (invoke "run" (i32.const 708055043)) (i32.const -379094713))
(assert_return (invoke "run" (i32.const 1999969421)) (i32.const -491572807))
(assert_return (invoke "run" (i32.const 1088306412)) (i32.const -2069143776))
(assert_return (invoke "run" (i32.const 1422482056)) (i32.const 277193620))
(assert_return (invoke "run" (i32.const 1230412564)) (i32.const -1850405544))
(assert_return (invoke "run" (i32.const 588587288)) (i32.const 23460068))
(assert_return (invoke "run" (i32.const 1308834785)) (i32.const 2060370293))
(assert_return (invoke "run" (i32.const -1020222735)) (i32.const -1186558523))
(assert_return (invoke "run" (i32.const -65569990)) (i32.const 467217710))
(assert_return (invoke "run" (i32.const 980416079)) (i32.const 735291899))
(assert_return (invoke "run" (i32.const -2128736939)) (i32.const 729392081))
(assert_return (invoke "run" (i32.const 355603661)) (i32.const 810588025))
(assert_return (invoke "run" (i32.const 1605361788)) (i32.const 1788878448))
(assert_return (invoke "run" (i32.const 801089220)) (i32.const 143353224))
(assert_return (invoke "run" (i32.const -1547759431)) (i32.const 1736992829))
(assert_return (invoke "run" (i32.const -1131127988)) (i32.const -57205248))
(assert_return (invoke "run" (i32.const -162789619)) (i32.const -1292056007))
(assert_return (invoke "run" (i32.const 165276486)) (i32.const 1506248626))
(assert_return (invoke "run" (i32.const 1871772854)) (i32.const 502692642))
(assert_return (invoke "run" (i32.const -383477935)) (i32.const -362951643))
(assert_return (invoke "run" (i32.const -1513701647)) (i32.const 401914309))
(assert_return (invoke "run" (i32.const -342138873)) (i32.const -743958461))
(assert_return (invoke "run" (i32.const 1364651620)) (i32.const -1537997528))
(assert_return (invoke "run" (i32.const 113839622)) (i32.const 362924274))
(assert_return (invoke "run" (i32.const -607600942)) (i32.const -1110404106))
(assert_return (invoke "run" (i32.const 1659585670)) (i32.const -1140865678))
(assert_return (invoke "run" (i32.const -423435050)) (i32.const -995983422))
(assert_return (invoke "run" (i32.const -1532179428)) (i32.const 2061862160))
(assert_return (invoke "run" (i32.const 334149820)) (i32.const -72651472))