# 復号器の商・剰余更新を計算に共用する案

2026-10-21。**成立性検査で棄却した研究候補**。入力値によらない処理順序を保てない必要条件を導き、実Wasmで反例を確認した。修復版は正しく動くが通常のアフィン符号化に戻り、今回の対象では公開I/Oから短い等価式を得られた。成功した発明や特許の核として数えない。

- [事前の仮説と検査計画](plan.md)
- [先行資料と確認した範囲](prior-art.md)
- [成立条件の導出、意味保存、実測値と制限](analysis.md)
- [生成器と公開I/O回復](prototype.py)、[実験](run.py)、[検査器](check.cjs)、[再生成監査](audit.py)

リポジトリ内のツールを使用する。Python 3.9、Node 24.15.0、WABT 1.0.42、Binaryen 133、Windows 10.0.26100で実行した。WABTは `.tools/wabt-1.0.42/bin`、Binaryenは `.tools/binaryen-version_133/bin`。共通のWAT読取・コンパイル処理として `research/isotope-swizzle/prototype.py` と `research/connectivity-elimination/prototype.py` を読む。追加Pythonパッケージは不要。

リポジトリrootで、存在しない出力先を指定する。既存の結果は上書きしない。

```powershell
python research/selector-quotient/run.py results/invention-20261021/selector-quotient-reproduction
python research/selector-quotient/audit.py results/invention-20261021/selector-quotient-reproduction results/invention-20261021/selector-quotient-reproduction-audit
```

実際に実行した出力は [selector-quotient-v1](../../results/invention-20261021/selector-quotient-v1)。`selector-model.json` に全条件と反例、`manifest.json` に32本とhash、`checks.json` に各本の不一致と診断trap、`recovery.json` に公開問い合わせ、`interpreter.json` に別実行器の結果を保存した。[監査](../../results/invention-20261021/selector-quotient-audit-v1/audit.json)は32本のbyte再生成、入力・結果・source hash・tool hashの照合を記録する。

対象は、export `run(i32)->i32` が一つだけあり、`(a*x+b) mod 2^32` を1–15段階入れ子で適用する閉じたWasm。型の異なる関数、追加関数・import・memory・制御分岐等は非対応。任意Wasmの難読化器ではない。生成した `.wasm` に対して、次のCLIも使える。

```powershell
python research/selector-quotient/prototype.py transform results/invention-20261021/selector-quotient-v1/chain3-source.wasm results/invention-20261021/selector-quotient-example.wasm --mode lift
python research/selector-quotient/prototype.py recover results/invention-20261021/selector-quotient-example.wasm results/invention-20261021/selector-quotient-example-recovered.wasm
```

`--mode decoder` は反証対象を生成する。正しい変換として使用しない。共用案の8,320呼出しはすべて不一致または診断用上限trapで、正対象24,960呼出しとは区別する。別実行器96呼出しとbyte再現は新たな独立入力ではない。

今回の進捗は、新しい具体的な仮説の反証と成立限界の記録である。独立した新規性と有用な保護効果を持つ新方式という全体目標は未達。[以前の構成的提案の採用](../../experiments/sha256-fixedpoint/independent-decision.md)を、この候補の失敗で取り消さない。
