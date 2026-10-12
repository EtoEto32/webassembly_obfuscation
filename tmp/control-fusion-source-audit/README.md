# 制御を含む演算統合: 著者コードとの照合

2026-10-12。前段: `../semantic-fusion-audit/README.md`。

## 判断の更新

H3を「条件式を演算に取り込む」「仮想命令に分岐を含める」という説明だけで新しい難読化アルゴリズムとは判断できない。ただし、LOKIのIRがIteを表現できることから、その変換器全体がIteを扱うと推論してはいけない。追加確認で後段のSemanticRewriter::eval_op_3はIteに対してunreachable!()となっていた。前処理を含む全経路の対応状況は未確認。後者に対応する仮想命令はTigress公式説明にある。
ただし、これはLOKIが一般CFGをそのまま統合すること、Tigressが任意のループ全体を一つのsuperoperatorにすることを確認したという意味ではない。具体的なCFG横断融合規則は依然未定義で、H3は採用しない。

今回の進捗は、LOKIについてREADME確認から**固定コミットの関連コードの確認**へ進めたこと。コードは取得して読んだだけで、ビルド・実行していない。新しい実験成功数はない。

## 固定した著者実装

リポジトリ: https://github.com/RUB-SysSec/loki

コミット: `a3b5717d9cd7a8f8b6cbf92399de59554c4cc55c`

GitHub API `git/trees/main?recursive=1` の応答でコミットを取得後、その固定URLから必要なファイルだけ取得した。取得元URLとSHA-256はsource-manifest.jsonに保存。sourcesには未変更のコピーと上流LICENSEを保存している。
著者コードを独自実装として扱わない。今後再利用・配布する際は上流ライセンス条件を引き継ぐ。

## 確認できた規則と限界

|ファイル・関数|今回確認したこと|ここから断定しないこと|
|---|---|---|
|superoptimizer.rs / replace_expr_var|変数の出現をその右辺の式で置換する。右辺がis_memory_opに該当すれば置換しない|一般の副作用解析や全種類のtrap保存をしているとは断定しない|
|同 / check_expr_constraints|変数・定数の種類数と式の長さに制約を置く|この数を増やすだけで新規性が生じるとは扱わない|
|同 / superoptimize_expression、derive_random_variable|代入対応表を参照し、制約内で展開候補を反復して選ぶ|CFGの到達条件までこの表が表現しているとは言わない|
|同 / find_used|最後の代入とメモリ操作を起点に利用変数を追う|メモリ意味が独立に保護されている、とは推論しない|
|semantics_builder.rs / from_assignment|単一出力と制約された入力変数・定数を持つSemanticsBlockへ変換する|複数出力化だけを未開拓の保護原理と扱わない|
|ssa.rs / eval_op_3|Iteを式として扱う|一般の分岐CFGを扱う実装と同一視しない|
|semantics_builder.rs / SemanticRewriter::eval_op_3|Iteはunreachable!()になっている|IRの表現能力と変換パイプラインの対応能力を混同しない。前処理で消える可能性を未確認のため、ユーザー入力で必ず失敗するとは言わない|
|linearized_expressions.rs / is_memory_op|式のopをLoad、Store、Alloc、Memと照合する|部分式を再帰的に全走査する判定ではない。呼出し文脈を無視して安全性を断言しない|

主にsuperoptimizer.rs全体の変換処理、semantics_builder.rsのfrom_assignmentとSemanticRewriter、ssa.rsの式分解とeval_op_3、linearized_expressions.rsのis_memory_opを確認した。プロジェクト全体の監査ではない。

## 著者評価との対応

experiments/experiment_13_superoperators/README.mdも取得した。MBAを無効にしてsuperoperatorを有効にする比較手順と、handler抽出後の合成評価を確認した。
これは独立要素を外す比較が既に用意されている根拠であり、こちらでその実験を再現済みという意味ではない。READMEの小規模再現条件と論文本体の規模には違いが明記されているため、将来比較する場合は条件を固定して報告する。

## Tigress公式説明

[Virtualize](https://tigress.wtf/virtualize.html) のInstruction Set Architecture Generation、VirtualizeConditionalKinds、superoperator例を確認。仮想ISAにはbranchIfTrue、switch等があり、複数命令の統合とstack/registerの混在が説明されている。
掲載された10命令統合例はmemory/stack/register操作の例であり、任意の条件分岐やループを跨ぐ統合の証明として使わない。説明ページには実装されていない選択肢もある。Tigress本体は今回実行していない。

## 次の候補に要求する具体性

これまでの棄却理由を踏まえ、未実装機能のリストから新規性を推測しない。新候補には次の設計表を実装前に埋める。

- 保護する対象: 内部の計算式、制御の対応、データ位置のいずれかと、復元成功の基準。
- 変換規則: 元IRから変換IRへの写像。通常の式展開や可逆符号化から異なる操作を特定する。
- 観測: バイナリ、選択入力、トレース、内部状態のうち解析者に何を許すか。
- 正しさ: 出力だけでなくtrap順序・メモリ更新・終了性のどれを保存するか。
- 近接方式との差: LOKIの式統合、Tigressの仮想ISA、既知の状態符号化のそれぞれで代用できない理由。
- 反証: 変換情報の抽出、トレース分割、式合成のどの結果で案を捨てるか。

前段H3のような「制御と値をまとめる」という説明だけでは、この表の変換規則と差分が埋まらないため、試作へ進めない。
次は合成・仮想化の境界を利用する案だけに固定せず、Wasm固有の構造化制御の変換と復元の先行研究を再確認し、具体的な規則から候補を設計する。単にサンプル数を増やす作業には戻らない。

## 保存物と再確認

source-manifest.json内のファイルをSHA-256照合することで、今回読んだ版を再確認できる。sourcesは上流から取得したコードで、実行不要。
Windows保護設定、外部プール、CSEC原稿には触れていない。新規性と有効性を支持する採用候補は未確定。研究目標は未達成。
