# 剰余表現の移植規則：実測結果

新発明の成功とは扱わない。oddは全条件で誤答し、正しいrepair/alignedは既知の構成。aligned全6条件はraw/O3とも元とbyte一致するWasmへ回復した。

正24条件101,208呼出しは値・trapとも一致。別WABTの正192・負48呼出しとlocal.tee回帰16呼出しも検査した。30本byte再生成、回復6本の元byte一致、8拒否対照、縮小幅524,256比較、6射影補題UNSATを保存した。同じ3人工式の派生条件であり、広いアプリケーション集合の評価や全入力の実装証明ではない。

|式|版|O3 core byte|実行中央値ns|元の時間倍率|process最大RSS KiB|
|---|---|---:|---:|---:|---:|
|add|plain|41|1.083|1.000|35868|
|add|repair|188|7.512|6.934|36140|
|add|aligned|115|2.987|2.757|36024|
|add|recovered|41|1.089|1.005|35856|
|multiply|plain|41|0.966|1.000|35776|
|multiply|repair|188|7.715|7.987|36244|
|multiply|aligned|115|3.092|3.201|35892|
|multiply|recovered|41|0.991|1.026|35872|
|polynomial|plain|57|1.281|1.000|35980|
|polynomial|repair|466|19.537|15.245|36108|
|polynomial|aligned|215|5.914|4.615|36068|
|polynomial|recovered|57|1.277|0.996|35856|

36 fresh process・252 batch。warmup16,384、20msへcalibration、全batchは10ms以上。wrapperをO3済みcoreに追加しWasm内で計時、Nodeは`--no-liftoff --no-wasm-lazy-compilation`。process中央値とbatch範囲はsummary.json、全batchはruntime側raw.json。RSSはNode全体であり保護の追加メモリとは断定しない。linear memoryは全条件0。無効なoddは性能比較から除いた。

変換35.80–38.64ms、回復36.56–39.45msは各条件1回の読取・出力・validation込み診断値。性能差の有意性検定・他CPU測定は行っていない。NotDec等の実逆コンパイラやrepairの自動解除は測定していない。

[設計と再現手順](../../../research/residue-wrap/README.md)。snapshotとSHA-256を本reportと各測定directoryに保存した。snapshotは実験後の凍結で、過去の実行開始時刻の暗号学的証明ではない。v1は射影器のlocal.tee処理不足による部分失敗として残し、保護成功に数えない。現形式の生成物から射影が回復できたことと、全てのRNS変換が解除可能なことは異なる。
