# 実験記録

2026-10-24。全て自作例。実測値と未達事項を分ける。

|検査|実測|
|---|---|
|[初期probe](../../results/fuel-observer/probe-v1/results.json)|7例、元/raw/O3、32,256値・event照合、108,928予算付き呼出し、不一致0|
|[実guardと適応予算](../../results/fuel-observer/guard-audit-v2/results.json)|3方式×raw/O3×4公開policy、326,784呼出し、393,990同履歴会計照合、128,688費用被覆照合、不一致0|
|[Wasmtime50.0.1](../../results/fuel-observer/cross-engine-v1/results.json)|7例×2binary×3方式、12,288境界予算呼出しでV8の全観測と一致|
|[経路集約](../../results/fuel-observer/merge-audit-v1/results.json)|30生成例、1,920返値照合、18,560予算付き呼出し、26,200費用被覆照合、不一致0|
|[誤った方式](../../results/fuel-observer/negative-controls-v1/results.json)|実Wasm opcode計測による秘密依存返金40/0、公開前の将来出力依存課金による成功/停止の差を確認|
|[境界と拒否](../../results/fuel-observer/subset-audit-v1/results.json)|signed marker、再入、極端予算等23条件、標準validationに通る非対応Wasm8種の拒否を確認|

これら件数を独立したアプリ数として合算しない。通常成功の一致は全入力同値の証明ではない。会計保護は公開履歴のprefixで照合し、最終出力が違うから過去の差を無視する評価にしない。

## 予約額と進捗

各例のsecret=0/1について最終的に拘束した論理額。wholeも安全だが、全額を入口で要求する。depthはイベント回数だけで上界を選び、observerは既に公開したid/payload列で選ぶ。

|例|whole|depth (0/1)|observer (0/1)|解釈|
|---|---:|---:|---:|---|
|early-split|90|90/90|26/90|公開後に低費用群を確定して返金可能|
|hidden-tail|126|126/126|126/126|公開情報で区別できず改善なし|
|two-release|209|209/209|97/209|二つの公開境界で過剰予約低減|
|uneven-word|85|76/85|34/85|異なる公開語の終了費用を区別|
|compensate|90|90/90|90/90|既存の累積予約から追加改善なし|
|correlated|158|158/158|158/158|述語相関を失い、正確な手書き上界94より過大|
|no-event|79|79/79|79/79|公開途中点がなく改善なし|

各初期予算0～whole+1、16 secret classの試験集合では、early-splitの完了数はdepth32に対しobserver104、two-releaseは32に対し928、uneven-wordは104に対し440。この比を実運用の成功率とは解釈しない。手書き履歴予約は最初の6例のうちcorrelated以外でobserverと一致した。

## 性能

[25 fresh process](../../results/fuel-observer/performance-v3/results.json)、[全測定](../../results/fuel-observer/performance-v3/raw.json)。5方式×5process、順序seed2026102413、各例warmup3,000、10,000call×11反復。全方式O3、ログ出力を無効化。値はprocess中央値の中央値、ns/call。Node24.15.0/V8 13.6.233.17、Windows。IQR、CPU、RSS/heap/maxRSSをrawへ保存。

|例|original|入口だけのwhole-host|depth|observer|
|---|---:|---:|---:|---:|
|early-split|33.80|28.86|181.82|182.81|
|hidden-tail|38.77|41.84|227.68|223.78|
|two-release|48.15|48.83|331.54|331.40|
|uneven-word|37.84|42.22|278.13|276.58|
|compensate|43.31|45.36|201.09|200.86|
|correlated|38.85|43.59|209.53|199.91|
|no-event|33.05|36.27|69.31|69.55|

中間会計は入口だけの検査より高費用。短い処理ではguard境界の費用が支配する。whole-hostがoriginalより速い標本もあり、小さい時間差を機構上の高速化と解釈しない。RSS等は7例を含むprocess全体で、個別guestのmemoryではない。

v1は整数overflow拒否の追加前。v2はguard正当性検査を同時実行していたため、性能の主値から除外した。v3は修正後のguardを単独で測定した値。これらを独立標本として足さない。既存結果directoryは上書きせず保存する。

元binary274～840 Bに入口marker10 Bを加える。O3後240～714 B。初期変換時間40～59msはWABT subprocessを含む単回値。sidecarも必要でありbinaryのみの増分で全配布量を表さない。

## 第二版の解析量

24小例で、集約版と列挙版の全履歴上界・生成binaryが一致した。追加の16/24/32分岐の6例は列挙版の4096行上限で拒否され、集約版は完了した。32分岐の2例は構文上2^32経路を1又は4行に表し、変換約48/53ms、sidecar686/3411 B。2^32本を実行したという意味ではない。秘密条件の相関を捨てた抽象経路の数である。小例の時間比は0.80～1.48程度と揺れ、一貫した高速化とはしない。公開語が多数なら集約版も指数増加する。

## Native fuelへの接続の予備検査

[計数probe](../../results/fuel-observer/native-fuel-probe-v1/results.json)はWasmtime Python50.0.1、consume_fuel有効、7例×16入力×元/raw/O3で336値を確認した。十分なfuelを与えた時の消費計測は224条件で論理費用を超えた。一方、論理費用だけを設定した呼出しではtrapを観測しなかった。計数点・検査粒度の違いを含むため、これを費用同一性やruntimeの欠陥の証拠にはしない。

[接続試験](../../results/fuel-observer/native-bridge-v1/results.json)ではraw変換binaryについて、予約差分を実fuelにも加減する方式を試した。全予算0～whole+1、16入力、初期補正0/4の両条件、計27,232呼出しで公開台帳と参照モデルの不一致0、native trap0、負のfuel調整0だった。**補正4の必要性は支持されなかった**。この小例で一致したことは一般のnative fuel被覆の証明ではない。O3では公開markerを越える純粋計算の移動も観測しており、元命令費用との対応は別途必要。固定版compiler sourceの根拠は未取得である。

再現：`python research/fuel-observer/native-fuel-probe.py SOURCE NEW_OUTPUT`、`python research/fuel-observer/native-bridge.py SOURCE NEW_OUTPUT`。SOURCEは初期probeの出力。DLLと依存版はcross-engineと同じ。予備接続の成功を論文の一般native保護の主張に加えない。

[短い境界の追加試験](../../results/fuel-observer/native-boundary-v1/results.json)は、marker数0/1/2/4/8/16/32、秘密依存xor数0/1/4/16、公開の有無の56fixture、raw/O3、補正0/4、全予算で25,024呼出し。公開台帳の不一致0、native trap0、budget停止24,128、正常終了896だった。markerなしの公開有無は同一内容なので、56の全てを別アルゴリズムとは数えない。豊富なfuelで測る消費はsource総費用より最大5大きく、接続成功から費用単位の一致を導けない。反証を探したがこの集合では接続失敗を得なかった。補正4の必要性・一般的native被覆の証明にはならない。[事前計画](native-boundary-plan.md)。

## 公開データ由来の分類器

[追加計画](classifier-plan.md)、[原データと出典](data/README.md)、[分類器結果](../../results/fuel-observer/classifier-v1/results.json)。UCI Irisの1datasetから、自作Gini trainerで深さ2/3/4/5の4木を生成した。4件の第三者製品ではない。4特徴をuint8へpackし、予測classだけを公開する。各木で150元入力、16corner、2048random、閾値近傍を検査し、元/raw/O3とguardによる71,232値・event照合、129,600予算付き呼出し、146,376公開prefix会計照合を通過した。

|最大深さ|whole/depthの150件合計額|observerの合計額|減少率|class0の額|class1/2の額|
|---:|---:|---:|---:|---:|---:|
|2|3300|2900|12.1%|14|22|
|3|4500|3700|17.8%|14|30|
|4|5700|4500|21.1%|14|38|
|5|6900|5300|23.2%|14|46|

150入力×全整数初期予算の集合では、各木の完了数depth300→observer450。入口で最大のmarker到達費用を要求するため大幅な入口緩和ではなく、公開後の残り3単位を最大classへ合わせ続ける必要がなくなった結果である。予約節約・返金はCPU時間の節約ではない。holdout45件の予測一致は42/43/43/43であり、分類精度は本方式の貢献ではない。

[独立symbolic検査v2](../../results/fuel-observer/classifier-symbolic-v2/results.json): 生成器のpath/envelope計算を使わない有限bitvector実行で全20経路がSAT、source→raw targetの値/event不一致条件20件がUNSAT、費用被覆違反0。各履歴のbound/terminalBoundを1減らす28改変すべてにSAT反例。対象は全32bit引数対を表現する限定モデルで、Z3 4.13.3と共有WAT syntax readerを信頼する。エンジン、JS guard、追加O3を含む全系の数学的証明ではない。v1はmodule境界チェック追加前、v2が主値であり合算しない。

[性能](../../results/fuel-observer/classifier-performance-v1/results.json): 25fresh process、3,000warmup、10,000呼出し×11、150実データを反復、全O3。process中央値の中央値ns/callは、original29.11/36.60/32.72/35.14、whole-host28.58/37.75/36.30/38.14、observer167.33/202.36/190.94/201.54。短い分類器ではhost会計が支配し、速度優位はない。source124–234B、raw+10B、O3 target120–216B、sidecar1813–1824B、変換単回41.8–42.4ms。全測定・メモリ値・機種はraw.jsonへ保存した。
