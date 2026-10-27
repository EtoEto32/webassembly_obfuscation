# 実験結果と採否

2026-10-19。正当性と実装の再現性は支持されたが、主特許候補としての独立した新規性と保護上の優位性は未確立。全件回復されたことだけを棄却理由にしない。自然配置に対する追加解析費用が小さく、実行費用と先行性を合わせて、今回の具体案を不採用と判断する。

## 正当性

主系列はN=4/8/16、更新則3種、plain/scalar/vector/mixed、raw/O3の72条件。vector/mixedの36条件には回復版も生成した。3系列×3段数の合成問題であり、9つの独立した実アプリケーションではない。係数は各条件1seed、レーン配置は1seedのみ。

192入力は境界値64件とランダム128件。境界のTは0,1,2,3,4,7,8,15,16,17,31,128,16384,16385,−1,INT_MAX。ランダムTは128未満。各条件の元・対象、該当時は回復版を実行した。

|検査|結果|証拠|
|---|---|---|
|Node差分|34,560呼出し、期待trap2,160、不一致0|[主検査](../../results/invention-20261019/temporal-lanes-v4/checks.json)|
|別実行器|Binaryen wasm-shell、108本・756照合、全通過|[記録](../../results/invention-20261019/temporal-lanes-verify-v1/summary.json)|
|抽象モデル|1/2bit、4段、T=0..4、全初期値・全入力列、263,376比較、不一致0|[モデル](../../results/invention-20261019/temporal-lanes-model-v1/summary.json)|
|意図的誤変換|停止maskのphaseを除いた9条件すべてに反例|[負例](../../results/invention-20261019/temporal-lanes-v4/negative.json)|
|対象範囲の拒否|memory公開・guard変更・入力変更・途中storeの4つを拒否|上記モデル|
|回復器の拒否|誤stop・誤predecessorの2つを拒否|上記モデル|

Nodeでは返り値/trapに加え、観測用にmemoryをexportした版の64KiB全域を毎回照合する。連続呼出しのtrap後にも前回状態が保存されることを検査する。Binaryenは返り値/trapのみ。WABT validationも実施した。縮小モデルは32bit実装全体の証明ではない。

## 解析課題と結果

配布バイナリと公開方式を与え、元の段順・係数・更新則を回復し、逐次Wasmを生成する課題。元ソースと生成seedは解析入力にしない。主解析は36/36を回復し、出力は元バイナリとbyte一致した。7反復の中央値で、回復本体0.205–0.928ms、WABT reader25.45–28.51ms。mixed/vectorの回復本体比0.894–1.089、reader込み比0.916–1.053で、追加の保護優位性は確認できない。[解析生データ](../../results/invention-20261019/temporal-lanes-performance-v1/analysis.json)、[比較](../../results/invention-20261019/temporal-lanes-report-v1/attack-ratios.json)。

phase値を隠すだけで改善するかを反証するため、mask値を順序推定へ渡さず、predecessorグラフから再構成した。こちらも36/36で元とbyte一致し、252解析の条件別中央値は0.183–0.886msだった。この結果に追加のWasm呼出し数は計上しない。[追加解析](../../results/invention-20261019/temporal-lanes-graph-v1/records.json)。

段順の回復は直列の依存鎖を辿れば足り、異なる論理時刻の全組合せを探索する必要がない。O3後も全36条件に期待数N/4のbitselectが残ったが、構文の残存は保護効果の証拠ではない。[命令集計](../../results/invention-20261019/temporal-lanes-report-v1/census.json)。

専用解析器の初回開発時間、人間の解析時間、一般の逆コンパイラとの競争は測っていない。NotDec/JEB等は今回実行しておらず、非対応やクラッシュを成果に数えない。全てのpipelinedプログラムが容易に回復できるという一般化もしない。

## 実行費用とアブレーション

O3の36モジュール、T=8/256、各3回の新規Node processで計216process。順序はseed191026でランダム化。各processは20,000回warmup後、2,000呼出し×9batchを測定し、batch中央値、さらに3processの中央値を採用した。値はJS呼出し・入力LCG・checksumを含むns/callで、一呼出しはT×Nの論理段更新を行う。同じN/系列/Tのchecksum一致も監査する。

T=256の実測。byteはO3版。

|段数|系列|plain ns|vector ns|mixed ns|mixed/plain|plain→mixed byte|
|---:|---:|---:|---:|---:|---:|---:|
|4|0|317.35|837.65|837.15|2.638|253→322|
|4|1|421.40|879.35|869.75|2.064|265→324|
|4|2|408.85|726.50|723.85|1.770|265→326|
|8|0|585.80|1229.30|1277.25|2.180|408→540|
|8|1|749.65|1250.30|1280.90|1.709|432→542|
|8|2|788.60|1232.50|1274.40|1.616|433→548|
|16|0|1335.60|2356.20|2438.55|1.826|719→964|
|16|1|1685.50|2388.25|2409.90|1.430|766→970|
|16|2|2044.95|2351.15|2511.85|1.228|766→980|

T=8を含む全18対でmixed/plain時間比1.228–3.732、mixed/vector比0.980–1.068、scalar/mixed比0.739–1.297。時間変更・SIMD化・レーン混在を段階的に外す対照であり、WASMixer等との同コスト比較ではない。混在を加えてもバイナリサイズは自然配置と同じだった。[全対照表](../../results/invention-20261019/temporal-lanes-report-v1/pairs.csv)、[生測定](../../results/invention-20261019/temporal-lanes-performance-v1/native.json)。

全版のlinear memoryは64KiB。追加はtyped localsであり、実行器のregister spillやstackの実使用量は個別測定していない。process peak RSS中央値は39,892–40,420KiBでNode本体を含む。mixed変換時間はreader・生成・compileを含む単発58.996–92.673ms。変換時間の反復分散は未測定。実行の3process中央値の最大/最小比は最大1.319で、細かい速度差の断定を避ける。Python解析msをV8実行nsで割った値を保護強度とはしない。

## 実装不備と主系列の区別

- `probe-v1`は小規模確認用で、主系列へ加算しない。
- `v1`は61条件完了後、O3のstandalone stack値を後続の引数なしlocal.setが消費する形にreaderが対応できず中断した。Wasm対象の解析耐性ではなく解析実装の不備。
- `v2`は全条件を完走。その後、maskとpredecessorの検査を強化したため、最終主系列にはしない。後の抽出器でも36条件を再確認した。
- `v3`は同一shuffleがrotate展開内に複数出現することを誤って拒否した。構造的に同一のshuffleを重複除去して修正した。
- `v4`は修正と検査強化後の主系列。新規出力先で再実行した結果と216本のhashを[監査](../../results/invention-20261019/temporal-lanes-audit-v1/summary.json)で照合する。

## 次の判断

位相定数の表現変更だけでは依存鎖による回復を防げない。次の候補は、単に時間境界・lane番号・固定表現を隠す変更ではなく、公開意味から得られるこの正規化の費用をどこで増やせるかを先に検査する。一般の依存グラフへ広げるだけでもtopological orderが得られるため、それだけを新規性や解析耐性とはしない。研究全体の新規で有効な主発明は未達。
