# 状態依存係数を用いる有限回の根への下降

2026-10-22。**収束を保証する十分条件の拡張を保持するが、独立した主発明として採用しない。** 今回の生成族は、方式既知の係数射影により全18条件を回復できた。一般収束理論に対する新規性と、追加の難読化効果は未確立である。

## 構成

元計算を依存順序に従うFとして表し、32bit環で `H(v)=v−M(v)(v−F(v))` を同期更新する。Mの対角を常に奇数、上三角部分を常に偶数にすれば、係数関数の合同保存性を仮定せず、どの初期状態からも `32×状態数` 回以内に元の結果へ到達する。保証は[proof.md](proof.md)に記載した。任意の状態依存Mの必要十分分類ではない。

係数内の回転で上位bitを下位bitへ移せることを試した。生成時に残差の括弧を展開し、Fだけを格納する独立した段階は置かない。実際には展開式中の特徴的な係数からFを取り出せた。この失敗は、許容される全ての係数関数に対する解除可能性の証明ではない。

入力は実`.wasm`。現在は単一の副作用のない3引数i32→i32関数、1～12演算ノードを対象にする。add/sub/mul/bitwise/許可された定数shiftなどの限定profileであり、内部状態に依存する右shift・回転を拒否する。外部入力は反復中固定なので、外部入力だけの回転と係数内の回転は扱える。memory・imports・任意の制御フローを持つ汎用Wasmの変換ではない。

| 対照 | 係数 |
|---|---|
| plain | 元の計算 |
| constant | 3I。交差結合を持つ定数行列ではない |
| congruent | 状態xor定数を基に、対角を奇数、上三角を偶数にする |
| rotated | 同じ生成規則に回転を加える |
| bad | 上三角の1要素を奇数にする負対照 |

回転の効果はcongruentとrotatedで比較する。旧bit依存解析器はconstantを含む18条件すべてをcycleとして拒否したため、これを新方式の成功とは数えない。専用攻撃は元ソース・seedを受け取らず、raw/O3の公開binaryから係数を射影し、残差式の再構成・偶奇条件・元依存順序・実行回数を検査してから等価式を出力する。

## 結果

3種類の3演算の式に対し、正42条件・3,048入力・128,016呼出しで不一致・追加trap 0。負6条件すべてで反例。別実行器336呼出し、追加初期値48呼出し、42本のbyte一致再生成も確認した。数学的保証と有限試験は区別する。

回転版のO3実行時間は元式の約425～429倍、合同保存版の約1.038～1.124倍だった。係数射影の本体は約0.72msで全18条件が回復した。回転追加による解析本体の増加は約1.077～1.108倍、読取込みの中央値の和の比は約0.994～1.024倍である。実行費用に見合う追加の保護効果は示せなかった。45 fresh Node process・405batchの全結果は[集計](../../results/invention-20261022/root-descent-report-v1/report.md)にある。

- [先行研究・差分](prior-art.md)、[事前計画](plan.md)、[証明](proof.md)
- [正当性結果](../../results/invention-20261022/root-descent-v2/checks.json)、[回復結果](../../results/invention-20261022/root-descent-v2/analysis.json)
- [小語長モデル](../../results/invention-20261022/root-descent-model-v1/model.json)、[別実行器](../../results/invention-20261022/root-descent-audit-v1/interpreter.json)
- [測定条件](../../results/invention-20261022/root-descent-runtime-v1/protocol.json)、[証拠ファイル照合](../../results/invention-20261022/root-descent-report-v1/provenance.json)

## 再現

Windows、Python3.9、Node24.15、WABT1.0.42、Binaryen133。追加Python package不要。rootの`.tools`と、既存のbit-feedback・unit-minor・stack-cycle・connectivity-eliminationの共通処理を使う。以下はリポジトリrootで実行し、未作成の出力先を指定する。

```powershell
python -X utf8 research/root-descent/model.py results/root-descent-new/model
python -X utf8 research/root-descent/run.py results/root-descent-new/main
python -X utf8 research/root-descent/audit.py results/root-descent-new/main results/root-descent-new/audit
python -X utf8 research/root-descent/performance.py results/root-descent-new/main results/root-descent-new/runtime
python -X utf8 research/root-descent/report.py results/root-descent-new/main results/root-descent-new/audit results/root-descent-new/runtime results/root-descent-new/model results/root-descent-new/report
python -X utf8 research/root-descent/prototype.py source.wasm results/new-rotated.wasm --mode rotated
```

main-v1から回復器の時間を読取と解析本体へ分け、main-v2を主結果にした。同じテスト入力のv1を件数に加算しない。性能runの元tool応答は欠落したが、45測定・18解析群・最終manifestを保存内容とhashで確認した。終了コードを観測したとは記録しない。

次の候補で解く必要があるのは、元式が係数として直接取り出せる問題と、大きい実行費用である。係数の変更や回転数の追加だけを別原理の新発明には数えない。
