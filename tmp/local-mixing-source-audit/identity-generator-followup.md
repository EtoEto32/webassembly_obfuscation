# 恒等回路からゲート実装を生成する案の追加照合

## 1. 状態
2026-10-12。Inconclusive、研究目標の状態はactive（継続中）。前回の作業は進捗なし。今回の作業は未読だった著者資料から具体的な既知生成手順を確認し、以下の案をStage 1で除外した。

## 2. 達成事項
単なる「局所混合」という要旨レベルの共通性から、恒等回路生成と先頭ゲートの条件付けという具体的手順の比較へ進めた。

## 3. 未達成事項
独立した新規原理、変換器、SHA-256全体への新方式適用、攻撃上の優位性は未達。

## 4. 検討した生成規則
候補案は、同じ可逆関数を実装する二つの回路A,Bを生成し、J=A;inverse(B)を作る。Jの先頭が自己逆ゲートgなら、その先頭を除いた残りRをgの代わりに使う、というもの。

逐次実行表記 `g;R` に対応する関数はR∘g。Jが恒等ならR∘g=id、したがってR=g⁻¹=gである。正当性はAとBが**全対象状態で同値**であり、gが自己逆であることに依存する。標本一致だけでは恒等性を保証できない。一般の非自己逆ゲートではR=g⁻¹となるため、同じ置換規則を適用できない。

## 5. 新たに確認した一次資料
Ran Canetti et al., Simons Obfuscation Workshop, June 2025. [Author slides, PDF](https://simons.berkeley.edu/sites/default/files/2025-07/CRY25-2%20Slides_Ran%20Canetti.pdf), linked from the [official talk page](https://simons.berkeley.edu/talks/ran-canetti-boston-university-2025-06-23). Inspected PDF text pages 12 and 19–21 (one-based). The slides specify growth followed by fixed-size local replacements. They also construct identity circuits using two obfuscations of one random circuit, rejection-sample a chosen first gate, remove it, and combine generated gate blocks. The general construction is conditional on RIO and SCP assumptions. Mixing connectivity and convergence remain questions; these slides are not a complete security proof.

The ePrint PDF returned 403. This audit therefore extends the inspected source scope to the author slides, **not** to the full paper. Search terms: `"Towards general-purpose program obfuscation via local mixing" pdf Canetti`, `"local mixing" "Canetti" arxiv`.

|必須比較項目|判断|
|---|---|
|数学的原理|候補の恒等回路生成・先頭ゲート除去は資料中の具体手順と重複|
|表現体系|可逆回路上の既知構成を採用したもの|
|状態変換|新しい符号化・更新規則は定義していない|
|依存関係|ゲート境界を混ぜるという一般的意図だけでは差分にならない|
|困難性の原因|意味保存の代数だけでは復元困難性を導けない|
|一般化可能性|WasmやSHAへの移植は可能性であり、独立性の根拠にはしない|

## 6. 再利用
同ディレクトリREADMEの要旨・OSS確認はC（設計資料）。今回の公開スライドもC。既存OSSのテスト結果を、この理論構成の安全性検証へ流用しない。

## 7. 実装・検証
新しい変換器や実験は実装していない。新規性を欠くと判明した手順を再実装しないという目標§4.2の判断。第4節の式は手書きの検討用仕様であり、WAT生成物ではない。

## 8. 攻撃比較
未実施。資料の仮定を実験で確認したとは扱わない。

## 9. 性能・サイズ・最適化
未測定。

## 10. 判断の変更
これまでの記録では局所置換と非線形表現の重複は具体化できていたが、この恒等回路からのゲート生成手順は未確認だった。今回、これを独立した新生成原理とみなす余地を除外した。恒等回路の生成法を別の既知手法に替えるだけでは、この判定を覆さない。一方、すべての将来の可逆回路変換が新規性を欠くという判定ではない。

## 11. Before/After
Beforeは自己逆ゲートg、想定Afterは上記R。実装前に重複が確定したため、実行可能Afterは生成していない。

## 12. 記録・追跡
本ファイルを既存監査への追記資料として保存。取得範囲と失敗したURLを明記した。既存READMEは当時の確認範囲として保持する。今回の検索で見つかったECCC TR26-091は別のメタ計算量論の研究であり、この具体手順の根拠には使用しない。

## 13. 限界
これは候補の採用・不採用の判断を更新する文献確認であり、新しい難読化成果ではない。理論仮定の真偽、実用コスト、Wasmでの耐性は未確認。CSEC原稿・データセット・既存実験は変更していない。
