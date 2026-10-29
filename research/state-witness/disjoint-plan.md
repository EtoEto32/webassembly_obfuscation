# moduleを分けた追加検査（実行前）

2026-10-24。context-v3とcontext-controls-v1の解析器を固定する。spec-v4の受理moduleのうち、cut-inputs-v1の14元moduleを除いたものを使う。非空passive segmentを持つ45 module・67 segmentで、fresh状態と一つだけdropした状態を比較する。選択数はmetadataのみから数え、今回の分類結果はまだ見ていない。

この公式corpusは以前のinstrumentation検査で実行済みなので、完全に未知の独立データとは呼ばない。context classifierの調整に使ったmoduleとは分離する。実製品の故障でなく、意図的な寿命差の感度/適用範囲実験である。

- original binaryでdef-use certificateを生成する。新しい結果に合わせた規則変更はしない。
- probeを追加し、初期state差が選択したsegment寿命だけであることを確認する。
- 元WASTのinteger引数のAPI呼出しを順番に実行し、最初の返却値/成功/trap差を元APIの証拠とする。比較途中で追加observerを呼んでも元guest stateを変えないことは既存検査に依存する。
- privateなmemory/table変化だけではAPI反例に数えない。ここでの契約は元関数exportへの呼出し結果の列とする。
- 見つからなかったものを同値としない。静的十分条件、具体的反例、保留、未対応を分ける。
- 同一内容binaryはhashで別途集約し、同じmoduleの複数segmentを独立bugと数えない。
- NodeとWasmtimeで同じ呼出し列の返却値/成功/trap分類を再現する。Wasmtimeでcanonical function identityを完全再検証したという主張はしない。

成功条件は、分類規則の対象範囲と保留数を隠さず示せること、および静的に証明可能とした状態対からAPI反例が出ないこと。新規性や優越性の成功条件ではない。

追加段階（disjoint-v1実行後、closure実行前）：14反例/24静的条件/29保留だった。保留理由は17 read-before-drop、6 loop、6 call_indirect。context-v3で既に固定した有限API profileを変更せず、full observerを使う状態再構成adapterを作り、そのモデルを適用する。結果を見てprofileを拡張しない。private stateが途中で異なるだけならAPI反例とせず保留する。上限128状態対。module分離と既存corpus使用という制限を維持する。
