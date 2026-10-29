# Lの初期実験：失効は動くが主研究への採用は留保

2026-10-25。Kとは別の安全性課題を実装した。**今のLを新しい失効原理、または修士の主テーマとして十分な新規アルゴリズムと主張する根拠はない。** 静的な参照可能関数の選別と既知の失効guardでも同じ契約を実現でき、wrapper分離の普遍的な費用優位は得られなかった。

## 正当性と失効契約

[probe-v4](../../results/failure-revocation/probe-v4/summary.json)は6つの参照経路×正常/trap/host例外×5方式、各engine 90 instantiation。Node 24.15.0/V8 13.6とWasmtime Python 50.0.1で各900回の後続呼出しを実行し、全行の観測が一致した。WABT 1.0.42でも変換後をvalidateした。

- active element、table.set、passive element/table.init、hostへ直接渡すfuncref、imported global、factoryが返すfuncrefを使った。
- 各初期化中にhostへ保存した関数で1回再入した。全90条件で結果42、memory counter 1。初期化中の合法なcallbackを一律禁止していない。
- 失敗後はhostからの直接呼出しと別Wasm moduleからの間接呼出しを行った。entry / address / refsは、各engineで合計360回をtrapで拒否し、元関数のmemory counterを増やさなかった。
- originalとtable/globalだけのrollbackでは、hostが既に保持した参照から240回/engine実行できた。これはWasmの仕様通りで、engineバグとしない。
- 正常時は全5方式の結果がoriginalと一致。Nodeではexport・factory・保存参照のJS identityも一致した。Wasmtime Pythonのobject wrapper identityを同じ指標として使っていない。

入力は人工的な18 module。180 instantiationや1,800後続呼出しを、独立した180事例の発見とは数えない。全入力証明・第三者application・並行失効・継続中断の検査はしていない。

## 強い対照との費用比較

[performance-v1](../../results/failure-revocation/performance-v1/summary.json): 4形状×4方式×2engine×3 fresh process = **96 process**。12 warmup、各11測定、guest内200,000反復。表は各process中央値の中央値、ms。全checksumが方式間・engine間で一致した。

|engine / 形状|original|全入口entry|参照可能入口address|wrapper refs|
|---|---:|---:|---:|---:|
|Node / direct-private|1.524|1.575|1.577|1.575|
|Node / direct-address|1.576|1.577|1.572|1.585|
|Node / indirect|2.162|2.511|2.711|2.496|
|Node / mixed|1.578|1.615|1.607|1.599|
|Wasmtime / direct-private|1.607|1.600|1.586|1.612|
|Wasmtime / direct-address|1.601|1.625|1.612|1.616|
|Wasmtime / indirect|2.272|2.260|2.285|3.199|
|Wasmtime / mixed|1.751|1.810|1.718|2.030|

Wasmtime indirectではrefsはaddressの約1.40倍、mixedで約1.18倍かかった。Node indirectの単回系列ではrefsがaddressより速いが、entryは同等に近い。entryとaddressの同一binaryでもNodeの測定中央値に差があるため、tiering・実行順・ばらつきから一般化しない。小さいdirect差も優位とは扱わない。

originalは296–391byte、addressは330–481byte、refsは340–555byte。追加型は不要で、参照可能関数ごとのwrapperが増える。変換時間は0.175–0.230ms/小moduleの単回診断値で、統計的な性能評価ではない。peak process memoryはNode約37.6–38.0MiB、Wasmtime/Python約24.5–25.7MiB。これはguest metadataだけの消費量ではない。全測定・IQR・setup時間をJSONへ保存した。

## 既存研究との差と採否

- 初期化が失敗しても関数参照が残り得ることは、[Wasmtimeの公式ArchitectureのInstantiation節](https://docs.wasmtime.dev/contributing-architecture.html)に既に明記されている。単なる不具合発見として新規性を主張できない。
- Jean-Baptiste Arnaud / Stéphane Ducasse / Marcus Denker / Camille Teruel, **Handles: Behavior-propagating first class references for dynamically-typed languages**, *Science of Computer Programming* 98 Part 3, 318–338, 2015, [DOI 10.1016/j.scico.2014.07.011](https://doi.org/10.1016/j.scico.2014.07.011)。査読誌。著者PDFのAbstract、§2.3、§8のmembrane比較を実際に確認。動的参照への失効の伝播を扱い、境界でのwrapperと実行中への伝播を区別している。Lは同じ原理の限定実装に近い。論文の全形式体系・全評価は読了していない。
- Miller / Yee / Shapiroの2003年資料も失効そのものが既知である根拠。現時点ではAbstractとHandlesからの引用関係までで、元論文全文の再現はしていない。
- Wasmで関数参照の生成箇所が列挙できる点、raw functionを外へ出さずdirect callを維持する変換、失敗したinstanceだけへの適用は具体的な構成差である。ただし参照入口のinterpositionとして説明できる。**構成差があることと新規な研究貢献が確立したことを分ける。**

主テーマへ進めるには、共有Store/共有tableを必要とする第三者workflowで、独立Store破棄やaddress guardでは満たせない具体的条件、または新しい保証と検証方法が必要。現時点で自然な必要例は未確認。wrapperを細工して小benchmarkだけ速くする方向には進めない。

## 実装の境界

Core Wasm 2相当＋tail calls。GC/EH/threads/memory64/multi-memory/typed function references/stack switchingはvalidatorで拒否する。同期、単一thread、hostが元binaryを検証・変換し、fresh gateを失敗直後に閉じる契約。custom sectionはすべて除去する。JS function.name、stack trace、debug metadata、実行時間、engineの資源限界まで保存する変換ではない。

既に発生したmemory/I/O効果は巻き戻さず、保持済みMemoryやTableそのものの権限も取り消さない。外部import関数はその元の権限を持ち続ける。Wasm moduleを全く実行できなくする一般的な取消しと混同しない。

最初のv1/v2は[性能計画](performance-plan.md)に記載した試験実装の問題で停止。v3/v4が成功記録。失敗したディレクトリを消して成功だけに見せていない。
