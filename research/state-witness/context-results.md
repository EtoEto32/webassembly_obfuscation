# 状態差から元APIの相違へ：残存差の分類

2026-10-24。[仮説と訂正の履歴](context-plan.md)。**新しい難読化・復元原理の発明ではなく、Kの検査結果を過大評価しないための追加解析と実験**である。

## 実測結果

[cut実験](cut-results.md)のdrop後2中断点条件には、wasm-migrate再開後にsegmentだけが異なり、entry結果・guest memory・tableが一致した18回があった。この18回を事後に選んで調べた。10生成case、9つの元moduleに由来し、18独立bugや独立標本ではない。

|判定方法|この18回での結果|解釈|
|---|---|---|
|segmentを含む完全state一致|18相違|完全state復元契約での差|
|実行済みentryと可視guest state|18一致|その一回の処理では差が表れなかった|
|元export呼び出し列、深さ4・有限の引数候補|2反例・16未検出|未検出だけでは同値を証明しない|
|read-before-dropの保守的解析|14十分条件・4保留|任意長API列について、segment差を読む前に消す限定条件|
|限定APIモデルの遷移閉包|16一致・2反例|下記の限定profileと観測契約の下での閉包。一般Wasm証明ではない|

[Node v3](../../results/state-witness/context-v3/results.json)の有限探索は合計5,676列。2反例はいずれも`memory_init/suite.3`の同じ生成caseの別中断点で、元API `test()`を一回呼ぶと片側がtrap、片側が正常終了した。[Wasmtime追試](../../results/state-witness/context-cross-v2/results.json)は全18個の遷移モデルを独立hostで再実行し、16/2の分類と各edgeが一致した。Wasmtimeで5,676列の探索全体を再実行したとは記載しない。

## 最初の説明を棄却した理由

事前には4反例を予測したが、実測は2反例だった。残り2回は`memory_init/suite.3`の別のcut位置で、片側だけにsegment 1が残る。元側は最初の`memory.init 1`でtrapする。復元状態側は既に同じ値のあるmemoryへ同じbytesを書き、segment 1をdropし、その後の空のsegment 3へのinitでtrapする。外部のtrap分類・memoryは同じであり、処理後にはsegment差も消える。

したがって「差のあるstateを読む」ことだけではAPIの相違を意味しない。途中の命令列やtrap箇所は違っても、今回の外部観測が同じ場合がある。最初にcase番号を逆に読んだ説明も[計画](context-plan.md)へ訂正を残した。

## 何を実装したか

`context-analysis.py`は元の`.wasm`から全export関数を解析する。差の残るsegment集合Dを伝播し、dropでDから削除、直接callでcalleeを解析、ifでは枝の和を取る。Dに含まれるsegmentのinitを見つけたら保留する。未対応命令・間接call・再帰も保留する。各APIを初期Dから解析するため、前の呼出しでDが減っていても過小評価しない。

初期の二つのguest storeでmemory/table/globalが対応して等しく、相違がDの寿命だけなら、certifiedなAPI内ではその相違を読まずに実行が進む。dropは差を消すだけなので、API列の長さに関する帰納法が成り立つ。これは手作業の意味論証であり、解析器をproof assistantで検証していない。

この条件で保留したものを含め、元APIが以下の形に限られるときは遷移モデルも構成する。

- 引数なし・戻り値なしで、定数引数のbulk命令とdrop/nopだけからなる有限の関数。
- 単一の`i32.load8_u(local.get 0)`のみの読取りAPI。memory同一性により全i32引数を同じ自己遷移のクラスとして扱う。offset等が付く形を自動で一般化しない。

globals、imports、start、shared memory、間接呼出し、一般loopをこのモデルへ含めない。原segment内容はimmutableで、寿命はdropでしか変わらない。各nodeで実測状態を同じ元binaryの二つのinstanceへ再構成し、全API遷移の正常/trapとmemory/tableを照合する。後続の状態対が完全一致または既出なら閉包となる。上限128に達した場合は保留する。状態対の再構成結果もobserverで照合した。

```text
work := [(left_guest_state, right_guest_state)]
while work has an unseen, unequal pair:
    for each original API action in the accepted finite profile:
        run the action from separately reconstructed instances
        if result or visible guest store differs: emit an API witness
        otherwise add the successor pair to work
if the work list closes: emit the scoped equal-observation model
```

原理は既知のdef-use、有限状態の積、bisimulation型の検査である。Wasm segmentへ適用したことだけで強い新規性とはしない。

## 観測契約と限界

比較対象は**同じ元programにおける二つのguest状態**。wasm-migrateの保存memory、再開selector、Weaveのwrapper状態は除く。したがってこの分類は、変換済み復元器の再入可能性や全APIを証明しない。追加の2反例も、上流の作者確認済みbugへ加算しない。

ホストが観測するのは元exportの値/成功/trap分類とguest memory/tableで、fuel、time、OOM、デバッグstack trace、trapした命令の位置は除く。追加observerやdrop helperは状態の準備・分類専用で、証拠のAPI列には含めない。元のsegment内容をhostが書換える操作もない。table値は本対象で確認した相異なる定数を返す関数のみを再構成しており、任意の参照同値には一般化できない。

全部が同じ小さな公式fixture系列からの探索的結果である。未見実アプリでのprecision/recall、既存fuzzerへの優越、悪意あるengineに対するsoundnessを示していない。16を一律に「既存ツールの誤検出」と呼ぶのも誤りで、完全state復元を要件とすれば18の差はいずれも正当な報告である。

## 追加の解析器検査

[14 controls](../../results/state-witness/context-controls-v1/results.json)は、両枝drop/片枝drop、直接call、引数式内call、先行trap、未使用private関数、間接call、再帰等を含む。13本・19入力条件・各engine 76 API呼出しがNode/Wasmtimeで一致した。再帰controlは解析保留だけを確認して実行しなかった。安全なゼロsource/ゼロ長initやreturnも現解析器が保留する例を残し、保留を不具合に変換しないことを確かめた。

## 再現

既存の[外部依存build](external-results.md)と[cut入力](cut-results.md)を用い、毎回新しい出力directoryを使う。

```powershell
python research/state-witness/context-analysis.py results/state-witness/cut-inputs-v1 results/state-witness/cut-v1 results/state-witness/local-context-inputs
node research/state-witness/context-run.mjs results/state-witness/local-context-inputs results/state-witness/local-context
python research/state-witness/context-cross.py results/state-witness/local-context-inputs results/state-witness/local-context results/state-witness/local-context-cross
python research/state-witness/context-controls.py results/state-witness/local-context-controls
```

残る修士研究候補は、複数の復元契約を混同すると評価結論がどう変わるかをWasmの実装・実測で示す研究である。Jの主要機構やKのprobe/中断点生成を、新発明として復活させる結果ではない。
