# F実測と採否

2026-10-24。数値の一次資料は下記の固定結果ディレクトリ。バージョン間の再実行を独立試料として足さない。

## 修正版の正当性・予算観測

[release-v6](../../results/fuel-frontier/release-v6/results.json)は49,152回の値・公開出力照合が一致。8つの前処理pipeline中3つを受理、5つを非対応として拒否した。3つは同じ13段mix処理をWAT/Rust opt2/Rust optsから生成したもので、3つの実アプリではない。各々1,024 payload ×秘密0/1を検査し、60 payloadは同じ公開出力、964は異なる公開出力だった。

|pipeline|全体累積予約|区間別最大値の和|各modeの同じ公開出力の予算対|dynamic / lateで観測差あり|whole / segment / frontierで観測差あり|
|---|---:|---:|---:|---:|---:|
|WAT O3 flatten|97|163|9,960|各8,820|各0|
|Rust opt2 O3 flatten|99|167|10,200|各9,000|各0|
|Rust opts O3 flatten|99|167|10,200|各9,000|各0|

差がある観測にはstatus、payload付きevent、課金額、残高を含む。全関数予約wholeも安全である。frontierの利点はより少ない入口予算でも公開prefixを実行できることに限定される。segment比の予約削減40.5～40.7%はCPU時間削減ではない。

[cfg-audit-v1](../../results/fuel-frontier/cfg-audit-v1/results.json): 32生成例、5,120値/event照合、1,280上界照合、8,224予算対が一致。br/br_if、早期return、深いlabel、dead markerを含む。予算対では公開payload/返値を除いた会計射影を比較しており、任意の秘密非干渉を実証した数ではない。

[audit-v1](../../results/fuel-frontier/audit-v1/results.json): 24例の未最適化/最適化48binary、1,152値照合、4,032上界照合、28,800適応policy対が一致。過小予約は実Wasmで反例を確認。carryを捨てる場合と秘密依存の返金は算術模型で反例を示した。相関する別ifでは実最大93に対して静的上界157となる過大評価も保存。

## 性能

[Wasmtime独立照合](../../results/fuel-frontier/wasmtime-check-v1/results.json): Python Wasmtime 50.0.1で3pipeline・7mode・2,688値照合が一致。同じ公開出力の60payloadからseed 2026102411で8個を選び、各有限予算を検査した。whole/segment/frontier/manualは各4,048予算対で差0。dynamic/lateは各3,576対に差が残った。手書き予約も独立oracleから組み立てた正しい安全対照である。任意入力や実時間の非干渉証明ではない。

[release-performance-v1/report.json](../../results/fuel-frontier/release-performance-v1/report.json)、[生測定](../../results/fuel-frontier/release-performance-v1/raw.json)。7mode ×5 fresh process =35 process。乱数seed 2026102409で順序を混ぜ、各例2,000 warmup、5,000call ×9反復。表はprocessごとの中央値の中央値、ns/call。IQRと各標本はJSONに保存。Node 24.15.0、V8 13.6.233.17、Windows、native Binaryen133の追加O3後を測定。

|pipeline|original|dynamic|late|whole|segment|frontier|manual|
|---|---:|---:|---:|---:|---:|---:|---:|
|WAT|55.56|1456.78|1533.94|85.14|95.74|97.56|79.56|
|Rust opt2|53.64|1515.94|1609.70|71.50|85.82|83.40|68.88|
|Rust opts|54.98|1567.12|1530.60|69.72|87.30|86.34|73.58|

manualは独立oracleの最大prefixに従う手書きhost予約。変換器の出力を安全性の根拠として流用しない。余分なWasm→host callを避けるためfrontierより速い。dynamicはopcodeごとのhostcallという高費用の研究用対照であり、実runtimeのnative meterより速いとは主張しない。

WATのoriginal/whole/segment/frontierのbinary sizeは513/536/546/544 B、Rustは504/527/537/535 B。変換時間はrelease-v6の各mode manifest内に記録。RSS・heapUsed・maxRSSはprocess単位で生測定に保存している。各processは3pipelineを測定するため、これは個別Wasmのmemory使用量や削減率ではない。inertなlinear memoryの確保を含む場合もある。

## 否定的結果と実装失敗

- [preopt-v1](../../results/fuel-frontier/preopt-v1/results.json): 初期7自作例の6つは通常O3でifが消えた。初期の大きい削減率を一般化できない。
- [compiler-v2](../../results/fuel-frontier/compiler-v2/manifest.json): 初期Rust18pipelineの12が受理されたが、全12で秘密ifが既に消えていた。
- release-v1～v3は公開値付きWATだけの段階。release-v4は未対応のunfolded returnを誤って扱いIndexErrorで中断し、全体の実験結果を生成していない。失敗を保存し、v5以降は明示的な非対応拒否へ修正。v6では非巡回CFGを追加した。
- 現在もloop、memory操作、一般call等を扱えず、Rust opt0と非flattenの一部は未対応。未対応を安全性成功や解析耐性へ数えない。

## 結論

公開イベント位置を保つ小例では、累積予約により区間別の過剰予約を減らせる。通常最適化に耐える例も得た。しかし強い安全対照を超える速度・安全性、新しい数学的原理、実アプリへの有効性は未確認。特許主案としては保留する。
