# Signed interaction revision: measurement

|fixture|mode|ns/call|process median range|optimized bytes|linear memory B|
|---|---|---:|---|---:|---:|
|fork|plain|1.026|0.989–1.063|66|0|
|fork|dag|128.139|123.347–128.252|446|65536|
|fork|dag-recovered|1.927|1.864–1.956|94|0|
|fork|interaction|215.645|214.352–227.836|662|65536|
|fork|interaction-recovered|0.987|0.985–0.993|49|0|
|chain|plain|1.023|0.994–1.045|64|0|
|chain|dag|133.674|133.630–134.191|458|65536|
|chain|dag-recovered|1.712|1.666–1.720|88|0|
|chain|interaction|244.136|241.681–245.761|722|65536|
|chain|interaction-recovered|1.080|1.061–1.106|58|0|
|ordered|plain|1.159|1.142–1.159|64|0|
|ordered|dag|98.242|97.264–101.905|429|65536|
|ordered|dag-recovered|1.902|1.895–2.296|94|0|
|ordered|interaction|283.713|279.249–283.799|782|65536|
|ordered|interaction-recovered|1.353|1.315–1.360|72|0|

These are tiny 2-input-bit kernels: only four meaningful external inputs each. This is a mechanism screen, not evidence of protection against I/O learning.
The same dynamic stopping rule is used for dag and interaction. 45 fresh processes, seven batches each, warmup 16384, 20ms calibration target; CPU affinity/frequency not fixed.
