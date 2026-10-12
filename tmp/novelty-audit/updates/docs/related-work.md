# 先行研究との比較と新規性の確認範囲

確認日：2026-10-11。追跡監査の結論は**現状を新アルゴリズムとして採用しない**。
候補作成時の調査に、下記の直接的な先行例が不足していた。詳細は [新規性監査](novelty-audit.md) と [検索記録](novelty-search-log.md)。
検索に出なかったことを、先行例が存在しない証明とはしない。

| 一次資料 | 既存の内容 | 今回との関係 |
|---|---|---|
| [Fukushimaほか、2006](https://www.jstage.jst.go.jp/article/ipsjdc/2/0/2_0_498/_pdf) §4.1 | 行列とベクトルで複数変数を同時符号化 | 今回の `Av+b` の直接的な先行例。剰余環の条件は区別する |
| [Slicing Obfuscations、2007](https://www.cs.auckland.ac.nz/~cthombor/Pubs/drm0127-majumdar.pdf) §5.3 | 領域ごとに別符号化、境界の復号・符号化の式を合成 | **今回の領域別切替という中核にも先行例がある** |
| [Tigress EncodeData](https://tigress.wtf/encodeData.html) | 奇数係数を使う整数のアフィン符号化等 | 符号化そのものは既存。本案の新規要素と主張しない |
| [Slicing Obfuscations: Design, Correctness, and Evaluation](https://www.cs.auckland.ac.nz/~cthombor/Pubs/drm0127-majumdar.pdf) §4.3 | 他変数との線形結合で依存を作る変数符号化 | 2変数を混ぜること自体も既存。重要な重複候補 |
| [Oxford RR-10-02](https://www.cs.ox.ac.uk/files/2936/RR-10-02.pdf) §2.3 | 変換・復元関数によるデータ難読化の正当化と局所適用 | E・Dを使う正しさの考え方は既存。本案の代数的根拠と関連する |
| [WASMixer arXiv v1](https://arxiv.org/html/2308.03123v1) | Wasmのデータ・命令・制御構造の変換 | 構造化制御を扱う点は共通。今回の多値境界案との全面的な非重複は未確定 |
| [WASMixer公開実装](https://github.com/security-pride/WASMixer) | 名前・メモリ・alias disruption・平坦化等の公開説明 | 今回は任意バイナリ変換やメモリ暗号化を実装しない。全ソースの重複監査は未実施 |
| [Cryptic Bytes arXiv v1](https://arxiv.org/html/2403.15197v1#S4.SS2) | Tigress、LLVM、wasm-mutateの複数段階の変換 | NOPや単純置換の追加を新規とせず、比較条件を分ける根拠 |
| [WebAssembly multi-value提案](https://github.com/WebAssembly/multi-value/blob/master/proposals/multi-value/Overview.md) | block/ifの結果型、loopの入力型に従う多値転送 | 機能自体は既存。提案のラベル型を実装の根拠として使う |

## 現時点で検証したい差

Wasmの多値境界を使い、複数整数の表現を領域ごとに切り替えた場合に、
同じ表現を全域で使う既存的な符号化と比べて、復元の負担と実行コストがどう変わるか。
これは候補提示時の研究仮説であり、「既存研究にないアルゴリズムを発明した」という結果ではない。
追跡監査で中核の重複が判明した。限定した入出力解析でも領域別切替の問い合わせ数の利点は示されなかった。
変数符号化・SSA/phi・領域別符号化・白箱実装の先行例と重なる可能性が高い。

## 検索の記録

Web検索で以下を含む語を確認した。検索結果の概要だけで新規性を判定せず、上表の一次資料を参照した。

- WebAssembly obfuscation multi value block parameters encoding
- WebAssembly obfuscation stack encoding branch parameters
- obfuscation control-flow affine encoding
- WebAssembly obfuscation multi-value encoding
- obfuscation SSA variable encoding

対象は上表に限る。WASMixer刊行版の全比較、全実装のコード調査、引用・被引用の網羅調査、
特許の網羅調査は未完了。最新の公開プロジェクトを含めた完全調査とも称しない。

## 新規性を主張する前の作業

1. 既存の領域別・SSAの変数符号化と本案を変換規則単位で照合する。
2. multi-valueを使うだけの対照と、表現切替だけの対照を追加する。
3. 既存最適化・簡約器で元の式を復元できるか測る。
4. 小さな既知プログラム以外への適用条件と正しさを確認する。

この結果、差が実装上の工夫だけなら、Wasm向け適用・評価研究として位置付ける。
単純な再命名や既存手法の組合せだけで新規性を保証しない。
