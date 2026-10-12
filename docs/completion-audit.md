# 予備実験の完了条件の確認

監査日：2026-10-06

## 目的に対する成果

|要件|状態|証拠|
|---|---|---|
|先行研究と公開候補の網羅的探索|完了|docs/literature-review.md、docs/search-log.csv、experiments/dataset-registry.jsonの25候補|
|公開配布物の版・取得元・ハッシュの記録と固定|完了|experiments/archive-registry.json、data/catalog、各receipt|
|明示された利用条件の確認|完了|results/catalog/license-metadata-audit.json。利用条件の記載がない場合や、第三者のバイナリにも適用されるか不明な場合も記録|
|安全な静的取得・解析|完了|未知Wasmと取得スクリプトを実行せず、入れ子アーカイブとTARをストリーム走査|
|公開範囲の全数解析|完了|18データセット、109,846件の配布ファイル、70,564 SHA、保留0。results/corpus/summary.json|
|重複とファイルの数え方の確認|完了|results/corpus/dataset-overlap.csv、Cryptic Bytesの元プログラム22本、MineSweeperの配布ファイル4,429件に対し、異なるSHAは36種類|
|解析失敗の偏りの評価|完了|results/provenance/wasmizer-failure-summary.json|
|クリプトジャッキング関連の難読化候補分析|完了|WasmMalの候補率は条件によって15.74～51.37%。SEISMIC計測コードは悪性ラベル121件・良性ラベル3件で確認。個別確認は35件|
|年ごとの変化を分析できるかの確認|完了|results/provenance/observation-dates-partial.json。各ファイルの観測日が不足しているため推定できない|
|再現可能なコード・表・図|完了|scripts、results/corpus、results/sensitivity、results/provenance|
|日本語予備実験報告|完了|docs/pilot-report.md|
|CSEC論文草稿|完了|paper/main.tex、paper/references.bib|

## 整合性確認

全18ユニットテスト、感度分析の整合性検証、Python構文検査に合格した。最終的なデータセット集計には未処理のファイルがなく、cohort-summary.csvに記録した配布ファイル数の合計は109,846でsummary.jsonと一致する。論文は引用10件と参考文献10件が一致し、LaTeXの各環境のbegin/end数と波括弧数も整合する。

この監査時点では、ローカル環境にplatexがないため、PDFの生成は行えていない。著者名と所属も投稿者による記入が必要である。これらは投稿準備の作業であり、研究結果の未完了を意味するものではない。

## 結果からいえる範囲

本研究では、公開されているクリプトジャッキング関連データセットを対象に、構造指標や生成された変換版、重複、解析失敗の扱いによって測定結果がどの程度変わるかを示す。実環境全体での難読化の割合、採掘機能だけに基づく悪性利用の自動判定、検知を回避する効果、年ごとの変化は結論に含めない。第三者バイナリの再配布権が確認できない配布物は、ハッシュと解析結果を公開対象とし、バイナリ自体を再配布しない。
