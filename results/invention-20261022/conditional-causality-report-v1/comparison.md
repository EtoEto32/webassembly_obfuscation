# 条件別の循環する共有演算：比較

時刻2026-10-22。時間はns/call、3 process中央値の中央値。1–5 ns付近の小差を速度優位と解釈しない。

|fixture|演算数/固定schedule長|plain|ordered VM|cyclic|cyclic回復|cyclic/plain|cyclic/ordered|
|---|---:|---:|---:|---:|---:|---:|---:|
|reverse4|4/7|1.960|10.162|16.129|1.967|8.231|1.587|
|permuted8|8/11|3.112|18.380|24.354|3.257|7.826|1.325|
|permuted12|12/19|5.328|27.163|42.650|5.245|8.006|1.570|

|fixture|plain O3 bytes|ordered O3 bytes|cyclic O3 bytes|回復 O3 bytes|
|---|---:|---:|---:|---:|
|reverse4|211|366|356|211|
|permuted8|381|544|518|381|
|permuted12|536|719|693|536|

両VMはprivate linear memory 65,536 bytesとn個のtable entryを追加する。直接版・回復版のlinear memoryは0。回復O3の6本はそれぞれ対応するplain O3とbyte一致。プロセスRSSはNode全体の測定。

主30条件（異なるbinary 21本）、126000通常呼出し、12288任意初期状態probe。回復12条件、helper同値SMT 96、記号合成順24条件、WABT 120呼出し。

通常VMからの追加費用は約33–59%。scheduleの共有による10–26 bytesの縮小はあるが、元版より大きく、保護費用上の優位は示されない。
