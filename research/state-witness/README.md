# K：Wasmの復元状態を非破壊に識別する検査器

現在の入口は[研究判断](status.md)、整理した[日本語草稿](paper-draft.md)、[残るギャップ](research-gap.md)。[package v3](../../artifacts/state-witness-import-v3.zip)は79 binary fileの再生成と直接反例の再生を別directoryで確認した。[既知worklist比較](guard-import-worklist-results.md)と[実ffmpegの制御対照](post-start-live-results.md)はその後の追加成果である。以下の追補は経緯であり、古いpackage番号や用途の記述は最新版の範囲と区別する。

[現在の研究判断と未達事項](status.md)。[hostの必須上書きと部分書込み](guard-import-may-results.md)を区別し、別array式・BFS・一般SMT・2engineで検査した。[再現package v2](../../artifacts/state-witness-import-v2.zip)も新directoryで動作確認済み。

最新の厳しい比較は[一般SMTとの同じ条件合成課題](guard-import-generic-results.md)と[ffmpeg.wasmの起動後到達検査](post-start-results.md)。一般対照も全条件を生成し、既知の実装改善で速度差が縮んだ。ffmpegの7,320 dropは起動時専用であり、起動後の自然な復元不具合の例にはならなかった。**限定した解析器は動作するが、修士研究の主成果として十分な独自性・自然な用途はまだ確立していない。**

[実アプリ由来corpusの静的調査](coverage-results.md)を追加した。242本の完了分に明示的dropはなく、Kの自然な用途での有効性は未実証という判断を維持する。

現在の入口は[契約を指定した診断CLI](quickstart.md)。[観測範囲とtrap後protocolの比較](guard-protocol-results.md)、[実復元器への公開観測診断](guard-external-results.md)、[日本語草稿](paper-draft.md)へ進む。原理の新規性と限定した実装上の成果を分けている。

[公開storeへhostが書ける契約](guard-environment-results.md)を追加した。初期条件だけの閉包では不十分になる元APIの反例と、576契約の条件合成を実装した。339初期storeは外部書込みによって一致から反例へ変わった。Spacerも新しい576具体状態queryを全て解けたため、既存汎用solverへの判定能力の優位は主張しない。[別原理案の棄却理由](alternative-screening.md)も保存した。

さらに[元entry内でhost importを呼ぶ実験](guard-import-entry-results.md)でも、同じhost呼出し列・同じtrap結果なのに公開memoryが異なる復元を確認した。その後、[同期void importの限定解析](guard-import-results.md)を追加し、256契約を2engine・別array式・具体BFSで照合した。元fixtureの指定された継続部分も解析できたが、復元器のPCやstackの対応を自動証明するものではない。

[小さな再現zip](../../artifacts/state-witness-minimal-v1.zip)は公開host書込みの2engine対照と44義務を新directoryで再現済み。後から追加したimport拡張はこのv1 packageに含まれない。

[汎用CHC/Spacer比較](guard-chc-results.md)では全156具体状態queryを既存solverも解いた。「Kにしか解けない」とは主張できない。[混合resourceの前向き検査](guard-holdout-results.md)では96 module・576契約・2,304 storeが2 engineと整合した。共通trap後の書込みで初期一致条件が壊れる小例も、元exportだけで再現した。

2026-10-24。特許目的を終了し、修士研究向けにJと異なる原理を実装した。**動作と限定した検査効果は確認、新規性は未確立。** [実測・採否](results.md)、[先行研究](prior-art.md)、[生成規則・意味条件](algorithm.md)、[事前計画](plan.md)を参照。

最新の[修士研究としての差分評価](novelty-analysis.md)。[記号的memory条件合成](guard-results.md)に加えて[tableへ拡張](guard-table-results.md)し、公式67状態対中55対を受理した。[反例抽出](guard-witness-results.md)では393列を2engineで再現し、具体BFSと最短長が一致した。130条件の固定点各層を別のarray式による667義務で照合した。一般的なpredicate transformer、等式抽象、反例復元は既知であり、Wasmの限定した復元差への適用として位置付ける。

393列は全store契約に対する反例である。[観測範囲の監査](guard-observation-audit.md)では、元return/trap差96、元公開memory差234、追加observerだけのprivate store差63に分かれた。最後の63は元の関数APIでは区別できない。[準備費用込み性能](guard-cost-results.md)と、状態数上限への[依存関係削減](guard-projection-results.md)も実測した。

その区別を解析器に組み込んだ[契約別の二つのstoreの条件合成](guard-contract-results.md)を追加した。新しい39契約を2engineで照合し、301の別array検証義務を確認した。さらに8本の元binaryを検査用exportなしで実行し、到達可能なstateから最大33呼出し後に公開関数の返値が変わる例と、公開前の上書きで差が消える対照を確認した。

binaryへ検査専用observerを追加し、memory bytesだけでは分からないsegmentのdrop状態等を比較する。検査用exportはprivate stateを公開するため、instrumented binaryをそのまま本番へ配布する用途ではない。元APIで確認できた反例と、追加observerでだけ分かるstate差を区別する。

追加成果：[公開wasm-migrateでの復元反例](external-results.md)。無移行対照、plain / observer付き、Node / Wasmtime、二因子の介入、独立再ビルドで確認した。外部実装の限定的な意味保存の反例として扱い、新規な難読化方式の成功や作者確認済み脆弱性とはしない。

[Weaveの正常対照](weave-results.md)も公開sourceをbuildして実行した。32回の復元が2 engineで一致し、既存の寿命再現が働くことを確認した。

さらに[公式testからの中断点生成](cut-results.md)を実装した。14 moduleから17位置を選び、0個/入口/寿命変更後の対照を272変換条件で検査した。4つの元moduleでwasm-migrateの元API差を確認し、Weaveでは一致した。Node/Wasmtimeで同じ分類となった。ただし同じ検査原理の手書き例がWeaveにあり、自動化だけを新原理とは呼ばない。

Python 3.9、Node 24.15、WABT 1.0.42、Binaryen 133、Wasmtime Python 50.0.1。既存の `.tools/wabt-1.0.42/bin`、`.tools/binaryen-version_133/bin`、`.tools/import-alias-quotient-python` を使用し、JのWAT reader/encoderを共有する。自動で依存をinstallしない。

[状態差の元APIへの影響](context-results.md)も追加した。18回の残存segment差を調べ、元programの限定APIモデルでは16回が同じ観測、2回が具体的なAPI反例となった。単なる状態相違の数をbug数に読み替えないための実証であり、復元器全体の正しさや新原理の成立を意味しない。

[開発moduleを除いた追加評価](disjoint-results.md)では45 module・67状態対を検査した。固定した有限APIモデルで同一観測41・反例14・未対応12となり、Node/Wasmtimeで一致した。重複除去後は61対で、未対応6対。人工的な寿命差による分類範囲の検査であり、新規な実製品不具合の件数ではない。

[Wasm-R3-Benchへの適用](r3-results.md)では23取得・11受理。元/名前除去/observer付きの3条件を実行し、両engineで10本が正常終了、1本が同じtrapとなった。条件間のexported memoryも一致した。ただし対象codeにdrop命令がなく、寿命変更をまたぐ復元の実アプリ評価には至っていない。

[参照observerの合成](composition-results.md)では、Weaveのexport wrapperによる照合失敗を再現し、directory方式で対応した。その後の[実アプリreplay比較](r3-weave-results.md)では20変換がvalidationを通り、通常20・復元16条件で一致、4条件は中断未到達だった。元API・state契約とoracle自体の信頼条件は[threat-model.md](threat-model.md)に整理した。directoryも既知の方法で、修正を新原理と数えない。

```powershell
python research/state-witness/prototype.py input.wasm observed.wasm
python research/state-witness/run.py results/state-witness/local-probe
python research/state-witness/cross.py results/state-witness/local-probe results/state-witness/local-cross
python research/state-witness/boundary.py results/state-witness/local-boundary
python research/state-witness/observability.py results/state-witness/local-observability
python research/state-witness/spec-run.py .tools/state-witness-spec results/state-witness/local-spec
python research/state-witness/bench.py results/state-witness/local-probe results/state-witness/local-performance
```

新しい出力先を指定する。`.tools/state-witness-spec` の公開資料取得は [fetch-spec.py](fetch-spec.py)（commit上限日時を固定）を使用した。保存済みprovenanceにある正確なcommitでの再取得を優先する。途中の失敗を含めて `results/state-witness/` に保存し、hash一覧を残している。

full profileは1 memory / 最大4 table / numeric globals / segmentsを検査。Jとの統合用 `--numeric-only` はtable function identityを見ない。shared/imports/start/GCは対象外。停止中、閉じたmodule、trusted test hostが前提である。
