# 実測

2026-10-24、Node24.15.0/V8 13.6、Windows。全て制御した自作fixture。製品の脆弱性を報告したものではない。

[主試験v4](../../results/waiter-identity/probe-v4/results.json): n=1..6の全278分割＋n=8/16/32/64の12条件、計290条件。904実memoryの全byte hashが検査前後で一致した。全cloneを別wrapperにした278条件中272では===だけで実体関係を復元できない。全byteが等しい独立memoryも正しく分離した。

実2memory Wasmの4条件で、alias時だけstoreの結果を他importから読めることを確認。clone aliasで=== guardは受理し、提案と正しいregistryは拒否する。これは不正なguardの局所例で、エンジンの欠陥ではない。

非shared/零長/unaligned/OOBを拒否。外部waiter混入は判定不能となり、その外部waiterも通知されるため、静止期間が必要という限界を実証した。

[干渉反例](../../results/waiter-identity/interference-v1/results.json)では、この検出を一般化できないことを確認した。独立A/BのうちAに外部waiterを1つ登録し、Aへの通知件数2に対し、Bの所有waiterを別workerから通知する。5試行全てで実際の分割[0,1]を[0,0]と誤分類し、全byte hashは不変だった。通知件数の一致は排他の証明にならない。非alias要求だけのguardに使う場合、この反例は余分な拒否を生む。誤受理を実証した試験ではなく、一般の敵対的干渉に対する健全性も主張しない。

[境界監査](../../results/waiter-identity/boundary-v1/results.json): 11条件。own buffer shadowで旧版の誤分割を再現し、修正版は同一と判定。偽物memory拒否、別realm、grow後、offset0/4/65532、入力list変更、3worker往復が通過。

v1はWABTへ既に既定有効のmulti-memoryの未対応flagを渡し、compile前に失敗。v2は初期成功、v3は不要cleanup通知を除いた版、v4はbrand確認・捕捉配列・代表所属の確認を加えた版。件数を版をまたいで合算しない。

## 性能

[性能v2](../../results/waiter-identity/performance-v2/results.json)、[全測定](../../results/waiter-identity/performance-v2/raw.json)。3方式×5fresh process=15。各条件3warmup、9反復、process中央値の中央値。単位ms/分割。memory作成・clone・registryの初期構築は測定外。RSS/heap/maxRSSは全12条件を含むprocess値。v1は境界修正前の値であり主値へ足さない。

|n|実体数k|batch|代表とのpairwise|正しいregistry|
|---:|---:|---:|---:|---:|
|8|1|0.0269|0.0666|0.0019|
|8|8|0.0467|0.2110|0.0017|
|32|4|0.0428|0.5012|0.0010|
|32|32|0.1417|3.5877|0.0011|
|64|1|0.0484|0.2887|0.0015|
|64|64|0.2119|13.7237|0.0026|

batchは正しいpairwiseより短時間だったが、registryより大幅に遅い。64独立memoryでは64登録+64通知、pairwiseでは4032登録+4032通知。hostが来歴を信頼して保持できないwrapper集合に限る位置づけである。極短標本の時間差や速度倍率を一般サービスの改善率としない。

## 並行書込みと未書込み位置

[計画](concurrent-plan.md)、[v1](../../results/waiter-identity/concurrent-v1/results.json)、[主v2](../../results/waiter-identity/concurrent-v2/results.json)。Wasm自身がatomic加算するworkerを動かし、n=8/32/64、k=1/2/4で各100回を測った。v1の失敗を受けて未書込み位置対照を追加したv2が主値で、合算しない。

|v2方式|判定成功/900|判定不能/900|成功中に書込み変化を観測|
|---|---:|---:|---:|
|更新位置、試行上限1|26|874|23|
|更新位置、試行上限64|87|813|80|
|静的に選んだ未書込み位置、試行上限1|900|0|895|

成功した分割は全てoracleと一致。判定不能は全て登録再試行上限だった。全27条件で終了後の書込み数と値、その他65,532byteの不変を確認した。1workerが1–4実体へ書く制御したmicrobenchmarkであり、一般の進捗保証・実アプリでの受理率ではない。並行試験中の時間は独立した性能比較へ混ぜない。

限定checkerは4種の許可binaryを受理し、valid Wasmであるwait32/wait64/notify/到達不能notify/host import/memory exportの6種を拒否した。単一共有memoryと数値runに限定し、検査済み同一byte列をworkerで使う。局所checkerだけで隠れた外部actorの不存在は証明しない。

この結果は、登録後のbyte更新がqueueを起こさないことと、通常の保守的な書込み範囲解析で登録競合を避けられることを支持する。Hの主特許採用判断を覆す新しい同期原理を示したものではない。

[範囲監査](../../results/waiter-identity/footprint-v1/results.json): 43実binaryで全memoryを生成recipeに基づく別oracleと比較し一致。21件は範囲外trap、41件で選ばれたcellの不変を確認。動的baseと定数式のwrapを解析しない2件は候補なしへ保守化した。負のi32 base、最大memarg offset、unaligned ordinary store、page末端、2storeを含む。任意binaryの形式証明ではない。

## 独立JSエンジン

[NodeとSpiderMonkeyの共通試験](../../results/waiter-identity/cross-engine-v1/results.json)では、同じpartition.cjsと290条件を実行し、全分割・登録数・通知数が一致した。各engineで904実体、59,244,544byteを直接比較し不変。実2memory Wasmの4条件、grow1条件、拒否3条件、buffer shadow1条件も一致した。前のNode試験の条件を繰り返したものなので、独立した新規fixture数へ足さない。

SpiderMonkey150.0.1の公式win64 shellを使用し、配布SHA512SUMSと一致、zip SHA256は`0be17b72f35f4db97e0fb7a33aa951f21b94cda22db4530e5409d9b07a8baa5c`。由来と各binary hashは結果に保存。shellにはstructuredCloneがないため公式shellのserialize/deserialize（共有許可）を使う。shellのsetTimeoutはdelay0限定・clearTimeoutなしなので、adapterはbatch timerを無効化し、30秒のprocess上限と未完了promise検査を用いた。**deadline挙動・browser配置・並行workerをSpiderMonkeyで確認した試験ではない**。

## 通知件数と解決列による一括復元

[事前計画](ordinal-plan.md)、[2engine試験](../../results/waiter-identity/ordinal-cross-v1/results.json)。ordinal版にも同じ290条件を適用し、各engineで904実体・59,244,544byte不変、実Wasm4条件・grow1・拒否3・shadow1が一致した。前述のshell制約は同じである。

[順序前提の小模型](../../results/waiter-identity/ordinal-order-v1/results.json)では、2種類の4要素分割について全24到着順を列挙した。どちらも正分類4、誤分類4、拒否16。誤分類は意図的に順序前提を破った入力であり、実エンジンの欠陥や発生率ではない。

[性能](../../results/waiter-identity/ordinal-performance-v1/results.json)は4方式×5fresh process、各条件20warmupと31標本×20分割。process中央値の中央値、単位ms。旧性能v2の追加標本として合算しない。single-deadlineは群別awaitを保ちtimerだけを一つにした対照。registryはMapによる正しい事前登録済みID、初期構築は測定外。

|n|k|群別timer|単一timer・群別await|順序利用|registry|
|---:|---:|---:|---:|---:|---:|
|8|1|0.013090|0.011750|0.014560|0.000620|
|8|4|0.017245|0.014525|0.010335|0.000530|
|8|8|0.027965|0.022160|0.010345|0.000610|
|16|1|0.015505|0.015115|0.015665|0.000550|
|16|4|0.023295|0.020020|0.017080|0.000565|
|16|16|0.048885|0.041065|0.017060|0.000755|
|32|1|0.023000|0.022435|0.027090|0.000810|
|32|4|0.029555|0.027965|0.025815|0.000805|
|32|32|0.097655|0.081190|0.029405|0.001280|
|64|1|0.044165|0.043415|0.048270|0.001395|
|64|4|0.051395|0.049115|0.047845|0.001460|
|64|64|0.203670|0.161705|0.054230|0.002275|

ordinalはk=nで単一timer対照より約2.14–2.98倍速い一方、k=1で約1.04–1.24倍遅い。全条件でregistryには劣る。タイマー数を揃えても多数の群でawaitを減らす効果は残った。新しい隔離保証や敵対的干渉耐性を示す結果ではない。
