# Signed interaction revision: measurement

|fixture|mode|ns/call|process median range|optimized bytes|linear memory B|
|---|---|---:|---|---:|---:|
|fork|plain|1.015|0.991–1.052|66|0|
|fork|dag|127.529|127.504–132.876|446|65536|
|fork|dag-recovered|1.866|1.864–1.923|94|0|
|fork|interaction|240.649|240.465–247.767|674|65536|
|fork|interaction-recovered|1.637|1.626–1.639|86|0|
|chain|plain|0.994|0.990–0.996|64|0|
|chain|dag|133.399|132.000–134.476|458|65536|
|chain|dag-recovered|1.711|1.661–1.713|88|0|
|chain|interaction|272.978|266.424–275.093|741|65536|
|chain|interaction-recovered|1.069|1.048–1.081|58|0|
|ordered|plain|1.129|1.122–1.157|64|0|
|ordered|dag|97.371|97.216–98.061|429|65536|
|ordered|dag-recovered|1.905|1.899–1.977|94|0|
|ordered|interaction|241.221|234.183–251.276|686|65536|
|ordered|interaction-recovered|1.971|1.955–1.980|100|0|

These are tiny 2-input-bit kernels: only four meaningful external inputs each. This is a mechanism screen, not evidence of protection against I/O learning.
The same dynamic stopping rule is used for dag and interaction. 45 fresh processes, seven batches each, warmup 16384, 20ms calibration target; CPU affinity/frequency not fixed.
