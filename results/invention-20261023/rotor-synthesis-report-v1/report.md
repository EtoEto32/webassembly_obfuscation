# 切替グラフ合成：実測と判断

2026-10-23。既知のrotor計算と有限仕様合成を超える新規性は未確立。実装・検査済みだが、今回の候補は主案に採用しない。研究全体の完了ではない。

|関数|方式|O3 bytes|実行中央値ns|解析本体ms|
|---|---|---:|---:|---:|
|and3|plain|45|1.0461|対象外|
|and3|rotor|375|96.4008|0.0184|
|and3|native|183|12.2723|0.8099|
|and3|tight|183|6.3303|0.5163|
|and3|recovered|45|1.0424|対象外|
|majority3|plain|54|1.1675|対象外|
|majority3|rotor|383|97.3064|0.0225|
|majority3|native|179|14.1855|0.8431|
|majority3|tight|179|11.0100|0.7142|
|majority3|recovered|54|1.1714|対象外|
|mux3|plain|51|1.1085|対象外|
|mux3|rotor|383|95.7775|0.0205|
|mux3|native|190|10.2545|0.8329|
|mux3|tight|190|6.0089|0.4641|
|mux3|recovered|51|1.1218|対象外|

解析本体は単回診断値で、read/compileを除く。rotorは8入力を全数追跡、native/tightは実命令からのBDD記号実行なので、両者の時間差を保護強度の比と表現しない。共通評価器の別BDD解析も全6条件を回復。

|検査|呼出し|不一致|
|---|---:|---:|
|共通評価器、元、回復|115,992|0|
|直接命令化、削減、回復|115,992|0|
|共通評価器の別BDD回復|28,998|0|

呼出しの入力は重複・方式間再使用を含む。各binary4,833呼出し。48主binaryと6追加回復binary。byte再現18、WABT72呼出し。拒否対照6件。4switchの全体合成は3/3成功、変換は181〜265msでsolver・WABT起動込み単回。xor3の別制約5switch10stepはInt20秒timeout、BitVec14.64秒UNSAT。後者は一般的不可能性を意味しない。

45fresh process×7batch、全315batch10ms以上。warmup16,384、20ms校正、同一Wasm内loop/入力更新。Node24.15/V8 13.6.233.17-node.48、Windows、i9-11900K、WABT1.0.42、Binaryen133、Python3.9、Z34.13.3。raw.jsonにprocess中央値、RSS、checksum、生batchを保存。tightのlinear memory0、rotor65,536byte。

読み方・生成規則・意味保存の範囲・先行研究・再現コマンドはresearch/rotor-synthesis/README.mdとprior-art.md。ソースsnapshotは下記sources/。ツールはrepoの.toolsに別途必要。
