# 副情報による退避量削減の実測

同じ符号化表現Bを維持して、全trap prefixの修復に必要な入口保存情報を減らす生成器を実装した。最小性はnestedな副情報・線形な共有保存という限定モデル。coded side-informationとの近接性があり、独立した新難読化・特許性は未確立。

|構造|basis入口値|side入口値|side temporary|basis ns|side ns|side/basis|side/plain|
|---|---:|---:|---:|---:|---:|---:|---:|
|swap16|4|1|4|8.055|7.697|0.956|3.489|
|rotate32|32|4|31|59.394|51.209|0.862|9.587|
|ladder64|10|1|10|36.815|36.977|1.004|14.556|

入口保持量は2seedとも一致、性能はseed211070のみ。rotate32は約13.8%時間短縮。swap16はprocess分散が重なるため明確な高速化とは言えず、ladder64は約0.4%増。宣言local総数とcode sizeは増加。入口の独立byte値をi32 localへ格納しているため、総メモリ削減やstack最小化とは主張しない。

正42条件37,184呼出し、期待trap19,152で不一致0。全64KiB physical memoryとdigestを各回検査。bad12条件は全て反例。既存回復器を変更せずbasis12、side12を元sourceとbyte一致するWasmへ回復した。別WABT294呼出し・168trap・最終memory1,652点が一致。54本byte再現、3未対応拒否を検査した。

小モデル6,048問題を全16subspaceの最小値と比較し一致、145,152状態prefix比較も一致。追加の4次元1,000問題を全67subspaceと比較し一致。全入力についての実装の機械証明ではない。

27 fresh process・189 batch、warmup32,768、15msへcalibration、全batch10ms以上。別Wasm moduleからvarying safe failを渡す。正常終了のみ、状態を繰り返し更新する固定copy列、3process中央値の中央値。Node全体RSSは測定したが、CPU register/stack使用は未測定。linear memoryは全条件1page。CPU affinityなし。transform/recoveryは各条件1回の診断値。

[再現手順](../../../research/side-save/README.md)と[算法・交換論証](../../../research/side-save/algorithm.md)。各入力folderとreportにsource snapshotとSHA-256を凍結した。snapshotは実験後で、実験開始時刻の暗号学的証明ではない。改良は工学的な部品として保持し、追加の解析耐性を示したとは扱わない。
