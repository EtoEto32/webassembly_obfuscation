# Sの実測と厳格な判定

2026-10-27、Windows上で実施。**限定された構築器として正しく動いた一方、強い対照に対する優位と実アプリへの適用性は得られていない。** 本稿中の数値は保存JSONに基づく。テスト成功を全入力の数学的証明や新規脆弱性発見としない。

## 1. 指定graphの構築と正当性

`results/gc-realization/screen-v1`。13型template、797要求graph。nullable/mutableの各組合せ、array/struct、1〜3nodeの辺選択、2型4nodeの混合、packed整数の境界値を列挙した。別実装の小規模状態探索は5,539状態を訪問し、515要求を実現可能と判定した。これは同じ限定構築規則の独立実装であり、独立した仕様形式化ではない。

|方式|生成成功|構築不能判定|独立探索の可能集合に対する成功|
|---|---:|---:|---:|
|staged（Kahn順序＋seed＋更新）|515|282|515/515|
|dfs-staged（通常DFS＋同じ二段階処理）|515|282|515/515|
|all-deps（全参照を先行依存とする）|249|548|249/515|
|null-patch（未来参照をnullで仮置き）|345|452|345/515|

主binaryは1,624本、意図的に誤る対照2本を加えて1,626本。Node 24.15/V8 13.6、Wasmtime 50.0.1、SpiderMonkey 150.0.1で4,878呼出しを行った。通常出力は全て1、必要な更新を省略した例と別nodeを同一objectにした例は全て0。compile/instantiate/executeのエラーは記録されなかった。元の13型moduleはR readerで検証・再読取し、生成物は3engineが検証・実行した。

追加 `controls-v2` は不正null・不正node ID・129node・immutable cycleの4拒否と、70nodeの深い型依存を3方式×3engineで確認した。9呼出しは全て1。深い型seedの構築を明示stackへ変更した。

stagedとDFSの補助constructor数は515件中12件で異なり、stagedが1個少ない例4件、多い例8件（+1が4件、+2が4件）。一貫した最小割当優位はない。数えているのはコード中のconstructorで、最適化後の物理割当ではない。

## 2. 実GCコーパスへの適用範囲

`dart-corpus-v1` と `corpus-v2`。公開commit `13951e126bd27d7560795b063e970cf5a96113ed` の6設定×最適化前後、12binary、13,799,003 bytes。wasmparser 0.262の別readerでは12/12を検証・静的解析できた。**S/Rの入力readerでは0/12対応**であり、最初に例外処理機能のvalidation gateで拒否された。

独立した型集計では12/12にnonfinalまたはsubtypingもあり、EH許可を一つ切り替えるだけでは現方式の適用範囲に入らない。一部は4096型上限も超える。例えば最適化後list_accessは236型/80 GC型、nonnull参照field 93、そのうちmutable 19、nonfinal GC型12、subtype GC型51だった。これらを実行時alias/cycleの証拠とは扱わない。

ダウンロードしたアプリは実行していない。この実験は静的な適用範囲の検査であり、アプリの入力生成成功率・コードcoverage・bug検出率を測ったものではない。

## 3. 時間・サイズ・メモリ

主値は `performance-v4`。6case（nonnull mutable array ring / immutable chain、各8/16/32node）。各方式3 fresh Python process・3 fresh Node process、合計12 process。生成は3 warmup batch後9測定batch、各60 plan。実行はcaseごとに200 warmup、7 batch×500呼出し。

|指標|staged|dfs-staged|
|---|---:|---:|
|生成時間のprocess中央値の中央値|0.210765 ms/plan|0.223890 ms/plan|
|各process中央値|0.241978 / 0.199673 / 0.210765 ms|0.346162 / 0.223890 / 0.222113 ms|
|Python tracemalloc peak|277,144 bytes|301,197 bytes|
|Node process peak RSSの範囲|41,160〜41,660 KiB|41,256〜41,620 KiB|

生成時間はこの小例での値。9batchを独立processと数えず、この差を一般的・統計的な優位としない。RSSはVM・code・adapter等を含み、guest heap使用量ではない。

|case|生成module / observer bytes（両方式同じ）|staged実行中央値 ns|DFS実行中央値 ns|
|---|---:|---:|---:|
|ring8|271 / 647|583.0|366.8|
|chain8|194 / 632|218.2|220.2|
|ring16|477 / 1,929|495.8|484.0|
|chain16|330 / 1,914|662.8|568.8|
|ring32|895 / 6,611|1,043.4|996.4|
|chain32|604 / 6,596|1,154.8|964.4|

**両方式の6生成module＋6observerは全12組でbyte一致。したがって実行時間の差をアルゴリズム差の効果と説明できない。** JSへ全nodeをmultivalueで返し、別Wasm moduleで全field・同一性を検証し、前呼出しとのroot同一性も確認する。値はJS adapter・検証・GC/JITを含む。物理的な補助objectの割当数や純粋なconstructor性能ではない。

## 4. 監査と初期失敗

`audit-v1/report.json`: 10manifest・1,825file hash、主1,624binaryの再生成、小規模5,539状態の再計算、benchmark24binary再生成、42中央値再計算で不一致0。既存paper/main.texはこの作業中の開始hashを保持。

- priors-v1: DNS取得失敗。v2で回復。
- inspector初回build: wasmparserのsupertypes API名に合わせて修正。未修正版を成功結果に含めない。
- performance-v1: Pythonの同名module衝突で中断。import pathを修正。
- performance-v2: 構築と検証を同じmoduleで行い、objectが外へ出ない。割当が消され得るため主測定から外した。
- performance-v3: 全node外出し・別observerへ修正。v4が明示stack修正後の現版。
- controls-v1: report辞書の重複key引数で中断。v2で修正後完走。

これらは研究コード・測定設計の修正であり、Wasmエンジンの不具合発見数には含めない。timeout/unsupportedを実行成功と数えない。

## 結論として言えること

nonnull mutable cycleと、後書きできないimmutable辺を分けた生成・検査器が動いた。弱い依存方式やnull仮置きだけの方式より生成範囲は広い。しかし普通のDFSによる同じ既知原理が全範囲を再現し、実公開コーパスへの対応は0/12。新しいアルゴリズムの優位、実fuzzerでのcoverage改善、新規bug検出はまだ主張できない。
