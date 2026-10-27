# 有限環の4点実行：Wasm試作と定数係数射影

2026-10-19。元入力での直接評価を専用laneに置かず、ずらした4入力の結果から答えを再構成する限定変換を実装した。dynamic版の各入力写像は非単射だが、バイナリから定数係数を追う解析は全30条件をscalarへ回復した。**独立した新規性と十分な保護上の優位性を確立できず、主発明としては不採用。** 研究全体や特許を目指す目標の完了とはしない。

[事前仮説](plan.md)、[設計・疑似コード・正当性・回復](algorithm.md)、[近接研究](prior-art.md)、[実験結果](analysis.md)、[日本語草稿](paper-note.md)。入力写像の非単射性と解析耐性を混同しない。

## 再現

Python3.9、Node24.15.0/V8 13.6.233.17-node.48、WABT1.0.42、Binaryen133、Windows x64。既存ツールは`.tools/wabt-1.0.42/bin`と`.tools/binaryen-version_133/bin`。親配置を変える場合は`WASM_TOOLS_ROOT`を設定する。`prove.py`は`.tools/encoding-synthesis-python`のz3-solver4.13.3を使用し、別配置なら通常Python環境へ同版を導入する。

```powershell
python research/nilpotent-stencil/run.py results/stencil-new
python research/nilpotent-stencil/verify.py results/stencil-new results/stencil-verification
python research/nilpotent-stencil/prove.py results/stencil-new results/stencil-proof
python research/nilpotent-stencil/measure.py results/stencil-new results/stencil-batch
```

既存出力を上書きしないので新規ディレクトリを指定する。`run.py NEW --compare OLD`でbinaryをbyte比較できる。測定は重い処理と並行しない。`run.py`のJS境界を含む時間は診断用で、主性能値には`measure.py`の共通Wasm内部loopを用いる。

```powershell
python research/nilpotent-stencil/prototype.py source.wasm transformed.wasm --mode dynamic
python research/nilpotent-stencil/attack.py transformed.wasm recovered.wasm
```

単一pure i32関数のadd/sub/mul DAGに限定する。既存のlane-demand、output-recurrence、connectivity-eliminationのparser/helperを再利用し、主実験では使用ソースを保存した。NotDec/StackSight本体との比較、任意C/Rustプログラムの保護、特許公報の網羅的調査は完了していない。

全結果は`results/invention-20261019/nilpotent-stencil-*`に保存。`report.py`は保存値から本文を生成し、`audit.py`は保存成果物の整合性を確認する。外部公開、push、出願、課金は行っていない。
