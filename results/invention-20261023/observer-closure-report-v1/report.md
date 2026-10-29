# 観測閉包の実測結果

2026-10-23。主案には不採用。自動閉包の生成自体は動作したが、公開APIから小さい更新を回復できた。

|case|元 ns|full ns|quotient ns|回復 ns|quotient/元|
|---|---:|---:|---:|---:|---:|
|quadratic|1.3888|13.6390|13.5669|1.4047|9.769|
|cubic|2.0153|20.4593|20.2578|1.9848|10.052|
|mixed4|2.7953|14.4445|14.4805|2.8471|5.180|

中央値は各processの7batch中央値を3processで再び中央値にしたもの。coreをO3後、同じWasm loopを追加。回復coreへ追加O3は行わず、V8条件は共通。毎回入力を変え、出力をchecksumへ反映。初期resetは1batchに1回。短い元コードのinlineを含む現実の実装差であり、命令単独のレイテンシではない。

主30条件780,090 API呼出しは全一致。負対照6条件は全て誤答。回復12条件は10step+10reset、追加12条件はresetなし22step・12instance。追試491,520stepは全一致。mainとfreshは同じ3人工kernelであり独立コーパスとして足さない。

小幅42閉包・524,256状態入力対は一致。回復は主・追試それぞれ12件でmod2^31の関数差をNewton係数で証明。WABTの独立実行器は360step・90最終観測で一致。負対照や未対応を保護成功へ数えていない。

|case|元/full/quotient/回復のcore bytes|同じ順のglobal state bytes|
|---|---|---|
|quadratic|108 / 759 / 764 / 109|4 / 20 / 20 / 4|
|cubic|111 / 1084 / 1087 / 115|4 / 24 / 24 / 4|
|mixed4|120 / 816 / 819 / 126|4 / 20 / 20 / 4|

linear memoryは全条件0。global state bytesは宣言したi32の論理的な4byte換算であり、実エンジンのallocationを測った値ではない。whole-process RSSはruntime/raw.json参照。変換・攻撃は条件ごと1回のwall timeで、process起動・WABT処理を含む。中央値の反復測定と混同しない。

変換時間範囲 76.451–80.772ms、reset攻撃 65.212–72.735ms、fresh攻撃 65.694–74.916ms。

精度を削ったquotientとfullの差は小さく、process間・batch間ばらつきが重なる。統計的な速度優位を主張しない。主比較で元より約5.18–10.05倍の実行費用を払っても同じquery攻撃で戻せた。

原理の先行性は research/observer-closure/prior-art.md、成立証明と限界はalgorithm.md。有限環の観測閉包という狭い差分だけから新規性・進歩性を断定しない。公開先行技術の法的な網羅調査、任意Wasmの保護、実アプリでの効果、他のdecompilerの評価は今回未実施。

入力、バイナリ、差分結果、単回時間、性能生値、別実行器ログを参照元に保持し、sha256.jsonに相対パスとhashを固定。sourcesには本集計時のbranchコードと共通helperの複製を収録する。主実験のfresh追加前のソースはmain/sources-pre-freshに保持した。
