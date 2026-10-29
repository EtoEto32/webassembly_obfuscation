# 入力依存の置換列書換え：実装と反証

2026-10-19。実WasmのBoolean式を幅5の置換列へ移し、積を保存する入力依存のHurwitz moveを小表の範囲で選択する試作。既知の幅5計算・固定基底変更・局所表化と比較した。

**主発明には不採用。** 主100本・2,858,240呼出し、追加36本・85,536呼出しで不一致0。しかし主50条件・追加16条件を全て簡潔な等価Boolean計算へ回復できた。元式と回復式の正規ROBDDも一致。逆書換えで元の列を戻す必要がなかった。固定基底変更に対する明確な追加優位性と、独立した新規性は未確立。

主5例のうち `repeated8` は意味的には定数0であり、非定数の保護対象4例と分けて扱う。追加の `active_repeat8` は非定数であることを確認した。小さい合成式であり、実アプリ5本の評価ではない。

- [設計・意味保存・攻撃](algorithm.md)
- [先行研究・特許資料の読了範囲](prior-art.md)
- [比較表・解釈](analysis.md)
- [日本語論文追補](paper-note.md)
- [実験前の計画](plan.md)

## 環境と再現

PowerShell、Python3.9、Node24.15.0/V8 13.6、WABT1.0.42、Binaryen133。Python追加package不要。既存の `.tools/wabt-1.0.42/bin`、`.tools/binaryen-version_133/bin` を使う。`WASM_TOOLS_ROOT`で親directoryを変更可能。共通parser/CLI部品として `research/lane-demand/prototype.py`、`research/output-recurrence/prototype.py`、`research/connectivity-elimination/prototype.py` に依存する。これらもmain実行時に保存した。

repo rootから、存在しない出力先を指定する。

```powershell
python research/hurwitz-support/run.py results/hurwitz-replay
python research/hurwitz-support/verify.py results/hurwitz-replay results/hurwitz-check
python research/hurwitz-support/edge.py results/hurwitz-edge
python research/hurwitz-support/measure.py results/hurwitz-replay results/hurwitz-batch
```

単体変換・適応的解析：

```powershell
python research/hurwitz-support/prototype.py input.wasm transformed.wasm --mode braid
python research/hurwitz-support/attack.py transformed.wasm recovered.wasm
python research/hurwitz-support/attack.py transformed.wasm reduced.wasm --reduce
```

`run.py --compare <previous-folder>` は生成binaryのhashを比較する。保存済み主結果は [hurwitz-support-v3](../../results/invention-20261019/hurwitz-support-v3/summary.json)、[verify-v1](../../results/invention-20261019/hurwitz-support-verify-v1/verification.json)、[edge-v1](../../results/invention-20261019/hurwitz-support-edge-v1/correctness.json)、[batch-v1](../../results/invention-20261019/hurwitz-support-batch-v1/summary.json)。v2/v3の100本がbyte一致。v1は解析器の再帰処理不備による中断、probe-v1は小例の動作確認として保存し、主結果に加算しない。

対象は `run(i32,i32)->i32` の明示的bit抽出とBoolean演算。元のmemory、一般loop、import、除算、float、GC、EHは非対応。変換後は私有のread-only linear memoryを使う。WABT interpreterで別途600呼出しを照合。数学的な積保存の説明はあるが、parser・変換器・compiler全体の機械検証ではない。

主目標である、新規で有効な難読化の発明・特許候補の確立は未完了。公開・push・出願は行っていない。
