# Typed relay measurements

Timings are medians; analysis excludes WABT parse/validation. Runtime includes the JS call loop.

|model|mode|opt|bytes|runtime ns/call|analysis ms|helpers|calls/ref/tail|
|---|---|---|---:|---:|---:|---:|---|
|rolling|plain|raw|121|73.5|0.0513|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|rolling|plain|O2|112|72.6|0.0496|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|rolling|plain|O3|112|72.3|0.0475|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|rolling|ref|raw|206|111.4|0.0906|4|{'call': 0, 'return_call': 0, 'call_ref': 8, 'return_call_ref': 0}|
|rolling|ref|O2|111|72.8|0.0502|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|rolling|ref|O3|111|76.2|0.0482|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|rolling|tail1|raw|218|164.0|0.0989|5|{'call': 8, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 1}|
|rolling|tail1|O2|111|72.3|0.051|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|rolling|tail1|O3|111|74.9|0.052|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|rolling|tail4|raw|254|163.4|0.1126|8|{'call': 8, 'return_call': 3, 'call_ref': 0, 'return_call_ref': 1}|
|rolling|tail4|O2|111|72.6|0.0479|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|rolling|tail4|O3|111|74.5|0.0478|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|rolling|tail8|raw|302|619.8|0.1248|12|{'call': 8, 'return_call': 7, 'call_ref': 0, 'return_call_ref': 1}|
|rolling|tail8|O2|111|73.8|0.048|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|rolling|tail8|O3|111|72.8|0.0472|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|rolling|call4|raw|254|162.9|0.1148|8|{'call': 11, 'return_call': 0, 'call_ref': 1, 'return_call_ref': 0}|
|rolling|call4|O2|111|74.1|0.0547|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|rolling|call4|O3|111|72.6|0.0555|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|dual|plain|raw|131|48.1|0.0597|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|dual|plain|O2|122|47.9|0.0589|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|dual|plain|O3|121|48.8|0.0547|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|dual|ref|raw|232|138.0|0.0994|5|{'call': 0, 'return_call': 0, 'call_ref': 10, 'return_call_ref': 0}|
|dual|ref|O2|121|47.9|0.0545|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|dual|ref|O3|116|48.1|0.0525|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|dual|tail1|raw|244|611.4|0.108|6|{'call': 10, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 1}|
|dual|tail1|O2|121|49.6|0.0549|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|dual|tail1|O3|116|49.7|0.0517|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|dual|tail4|raw|280|623.9|0.1216|9|{'call': 10, 'return_call': 3, 'call_ref': 0, 'return_call_ref': 1}|
|dual|tail4|O2|121|48.0|0.0577|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|dual|tail4|O3|116|49.0|0.0562|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|dual|tail8|raw|328|803.8|0.1313|13|{'call': 10, 'return_call': 7, 'call_ref': 0, 'return_call_ref': 1}|
|dual|tail8|O2|121|47.6|0.0548|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|dual|tail8|O3|116|48.5|0.0514|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|dual|call4|raw|280|612.6|0.119|9|{'call': 13, 'return_call': 0, 'call_ref': 1, 'return_call_ref': 0}|
|dual|call4|O2|121|48.3|0.0574|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|dual|call4|O3|116|48.1|0.0522|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|update|plain|raw|146|46.2|0.1075|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|update|plain|O2|138|45.9|0.0599|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|update|plain|O3|137|45.9|0.0603|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|update|ref|raw|251|133.5|0.1101|5|{'call': 0, 'return_call': 0, 'call_ref': 11, 'return_call_ref': 0}|
|update|ref|O2|138|48.0|0.0603|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|update|ref|O3|137|45.8|0.0648|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|update|tail1|raw|263|544.3|0.1201|6|{'call': 11, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 1}|
|update|tail1|O2|138|46.0|0.0628|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|update|tail1|O3|137|45.9|0.0617|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|update|tail4|raw|299|546.4|0.1269|9|{'call': 11, 'return_call': 3, 'call_ref': 0, 'return_call_ref': 1}|
|update|tail4|O2|138|47.8|0.0642|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|update|tail4|O3|137|46.4|0.0604|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|update|tail8|raw|347|699.0|0.1397|13|{'call': 11, 'return_call': 7, 'call_ref': 0, 'return_call_ref': 1}|
|update|tail8|O2|138|46.2|0.0611|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|update|tail8|O3|137|45.4|0.0597|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|update|call4|raw|299|545.6|0.1417|9|{'call': 14, 'return_call': 0, 'call_ref': 1, 'return_call_ref': 0}|
|update|call4|O2|138|45.9|0.0605|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|update|call4|O3|137|45.6|0.0646|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
