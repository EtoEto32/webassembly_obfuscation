# Typed relay measurements

Timings are medians; analysis excludes WABT parse/validation. Runtime includes the JS call loop.

|model|mode|opt|bytes|runtime ns/call|analysis ms|helpers|calls/ref/tail|
|---|---|---|---:|---:|---:|---:|---|
|rolling|plain|raw|121|72.0|0.0536|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|rolling|plain|O2|112|72.5|0.0477|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|rolling|plain|O3|112|72.5|0.049|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|rolling|ref|raw|206|112.4|0.0899|4|{'call': 0, 'return_call': 0, 'call_ref': 8, 'return_call_ref': 0}|
|rolling|ref|O2|111|72.7|0.0472|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|rolling|ref|O3|111|73.0|0.0479|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|rolling|tail1|raw|218|163.2|0.0987|5|{'call': 8, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 1}|
|rolling|tail1|O2|111|72.9|0.0462|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|rolling|tail1|O3|111|73.0|0.0511|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|rolling|tail4|raw|254|164.1|0.1134|8|{'call': 8, 'return_call': 3, 'call_ref': 0, 'return_call_ref': 1}|
|rolling|tail4|O2|111|73.3|0.0499|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|rolling|tail4|O3|111|75.0|0.0497|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|rolling|tail8|raw|302|612.6|0.1228|12|{'call': 8, 'return_call': 7, 'call_ref': 0, 'return_call_ref': 1}|
|rolling|tail8|O2|111|72.8|0.0503|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|rolling|tail8|O3|111|73.3|0.0516|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|rolling|call4|raw|254|164.4|0.1128|8|{'call': 11, 'return_call': 0, 'call_ref': 1, 'return_call_ref': 0}|
|rolling|call4|O2|111|73.7|0.0489|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|rolling|call4|O3|111|72.8|0.0474|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|dual|plain|raw|131|47.4|0.0555|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|dual|plain|O2|122|49.5|0.0544|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|dual|plain|O3|121|47.6|0.0536|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|dual|ref|raw|232|136.8|0.0981|5|{'call': 0, 'return_call': 0, 'call_ref': 10, 'return_call_ref': 0}|
|dual|ref|O2|121|48.0|0.0547|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|dual|ref|O3|116|48.3|0.056|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|dual|tail1|raw|244|613.2|0.1181|6|{'call': 10, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 1}|
|dual|tail1|O2|121|48.9|0.0574|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|dual|tail1|O3|116|50.6|0.0525|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|dual|tail4|raw|280|634.0|0.1192|9|{'call': 10, 'return_call': 3, 'call_ref': 0, 'return_call_ref': 1}|
|dual|tail4|O2|121|48.0|0.0548|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|dual|tail4|O3|116|48.7|0.0523|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|dual|tail8|raw|328|805.3|0.1325|13|{'call': 10, 'return_call': 7, 'call_ref': 0, 'return_call_ref': 1}|
|dual|tail8|O2|121|49.6|0.0563|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|dual|tail8|O3|116|47.2|0.0542|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|dual|call4|raw|280|613.4|0.1241|9|{'call': 13, 'return_call': 0, 'call_ref': 1, 'return_call_ref': 0}|
|dual|call4|O2|121|48.0|0.058|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|dual|call4|O3|116|48.8|0.055|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|update|plain|raw|146|46.8|0.0651|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|update|plain|O2|138|46.2|0.0624|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|update|plain|O3|137|45.4|0.0604|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|update|ref|raw|251|138.9|0.1068|5|{'call': 0, 'return_call': 0, 'call_ref': 11, 'return_call_ref': 0}|
|update|ref|O2|138|46.8|0.0636|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|update|ref|O3|137|46.6|0.0622|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|update|tail1|raw|263|547.2|0.1153|6|{'call': 11, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 1}|
|update|tail1|O2|138|46.2|0.0613|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|update|tail1|O3|137|46.0|0.0602|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|update|tail4|raw|299|545.0|0.1498|9|{'call': 11, 'return_call': 3, 'call_ref': 0, 'return_call_ref': 1}|
|update|tail4|O2|138|46.4|0.0644|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|update|tail4|O3|137|46.2|0.0599|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|update|tail8|raw|347|698.4|0.14|13|{'call': 11, 'return_call': 7, 'call_ref': 0, 'return_call_ref': 1}|
|update|tail8|O2|138|46.0|0.061|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|update|tail8|O3|137|46.2|0.0603|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|update|call4|raw|299|545.8|0.127|9|{'call': 14, 'return_call': 0, 'call_ref': 1, 'return_call_ref': 0}|
|update|call4|O2|138|46.3|0.0615|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
|update|call4|O3|137|45.5|0.0608|0|{'call': 0, 'return_call': 0, 'call_ref': 0, 'return_call_ref': 0}|
