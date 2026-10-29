# 全計算を行列式へ移す候補の検査

2026-10-22。**実装・実験を完了したが、主発明には採用しない。** 動的codecの逆変換がそのまま見えるという前案の弱点を避け、入力依存の混合を生成時に展開した。しかし、混合手順を求めず全行列式を記号計算すれば、全18解析条件を短い式へ回復できた。行列式表現と多項式係数の行・列混合には直接的な先行技術がある。

- [事前計画](plan.md)、[アルゴリズムと意味保存](algorithm.md)、[先行技術との照合](prior-art.md)、[論文追補](paper-note.md)
- [比較表](../../results/invention-20261022/unit-minor-report-v1/comparison.md)、[JSON](../../results/invention-20261022/unit-minor-report-v1/report.json)、[CSV](../../results/invention-20261022/unit-minor-report-v1/comparison.csv)
- [正当性](../../results/invention-20261022/unit-minor-v2/checks.json)、[回復結果](../../results/invention-20261022/unit-minor-v2/analysis.json)
- [モデル](../../results/invention-20261022/unit-minor-audit-v1/model.json)、[別実行器](../../results/invention-20261022/unit-minor-audit-v1/interpreter.json)、[再生成](../../results/invention-20261022/unit-minor-audit-v1/replay.json)、[拒否対照](../../results/invention-20261022/unit-minor-audit-v1/controls.json)

## 実測

3種の小さな3引数算術式を、5次または6次の行列に変換した。実アプリ3本ではない。混合なし・定数混合・入力依存多項式混合をraw/O3で比較した。境界直積1,000個と固定乱数4,096個、計5,096入力を使用した。

正42条件・214,032呼出しで不一致・追加trapは0。符号を反転する負6条件は全て反例を得た。別WABT実行器の336呼出し、42本のbyte一致再生成、小語長全列挙と32bit乱数の計7,488モデルケースも通過した。profile外入力2件・改変kernel6件・rank不足1件を拒否した。最後のケースは元kernelが実際にtrapすることも確認した。

解析側は8通りの入力parityについてrank条件を検査してから、係数表の行列式をdivision-freeに展開した。全18条件を3・4・17項の等価式へ回復。6つの多項式混合条件でも元ソース、seed、混合操作列は不要だった。原ソースの構文そのものを回復したという意味ではない。

主性能測定は45 fresh Node process・405batch。O3多項式混合の実行は約569–1,021ns/回、元式の約508–965倍、同じ操作列の定数混合の約2.85–3.09倍。解析本体は約5.62–13.00msで定数混合の約8.06–15.24倍、読取・証明と本体の中央値を足した比は約1.36–1.77倍だった。**解析費用の増加は確認できた**が、既知構成から独立した新規性や実用的優位は示せていない。

行列式版の非公開linear memoryは128KiB、元式・回復式は0。Node最大RSSは35,624–36,204KiBでJIT等を含む。変換は1条件あたり約39.8–52.6msの単回測定。通常式の約1nsは共通Wasm loopとJITの結果で、API呼出し速度ではない。25/405batchは10ms未満であり、process間の範囲も比較表に示す。CPU固定、同コスト調整、実アプリ、大規模式、汎用逆コンパイラ・人間の分析時間は未評価。

## 再現

Windows、Python3.9、Node24.15、WABT1.0.42、Binaryen133。追加Python/Node package不要。toolはrootの`.tools/wabt-1.0.42/bin`と`.tools/binaryen-version_133/bin`を使う。共通のWAT parserは`research/connectivity-elimination/prototype.py`から読み込む。rootから、未作成の出力先を指定する。

```powershell
python -X utf8 research/unit-minor/run.py results/unit-minor-new/main
python -X utf8 research/unit-minor/audit.py results/unit-minor-new/main results/unit-minor-new/audit
python -X utf8 research/unit-minor/performance.py results/unit-minor-new/main results/unit-minor-new/runtime
python -X utf8 research/unit-minor/report.py results/unit-minor-new/main results/unit-minor-new/audit results/unit-minor-new/runtime results/unit-minor-new/report
```

既存の適合する実Wasmへの変換と回復は次のCLIでも行える。入力profileは[algorithm.md](algorithm.md)を参照。

```powershell
python -X utf8 research/unit-minor/prototype.py source.wasm results/new-polynomial.wasm --mode polynomial
python -X utf8 research/unit-minor/recover.py results/new-polynomial.wasm results/new-recovered.wasm
```

## 修正履歴と範囲

main-v1の有限試験は通過したが、回復器が任意の改変係数表に対してtrap不在を検査していなかった。全parityのrank証明を加えmain-v2を主結果にし、rank不足の負対照を追加した。同じ入力のv1件数を加算しない。

runtime-v1は通常版と回復版の162batch全てが10ms未満だった。上限を2^20→2^24、warmupを1,024→16,384へ変えてruntime-v2を主結果にした。v1も保存し、主結果へ合算しない。

この方式はWasmの整数意味を使うが、Wasmだけに固有の原理ではない。解析成功を理由に「難読化ではない」とはしない。具体的な先行記載と、限定例での保護費用を根拠に主発明への採用を見送る。有限環残差方式の以前の構成的提案は保持する。
