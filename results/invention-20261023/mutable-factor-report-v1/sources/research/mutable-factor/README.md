# 接続を二つの可変表で保持する案：初期検査

2026-10-23。実Wasmへの変換、正当性検査、方式既知の解除を実行した。**独立した主特許候補としては不採用。** 対応表を毎回変更しても、二表を合成した接続だけを追えば履歴なしで通常コードへ戻せた。研究全体を成功・完了扱いしない。

[事前計画](plan.md)、[更新規則と解除](algorithm.md)、[先行技術との関係](prior-art.md)、[実測報告](../../results/invention-20261023/mutable-factor-report-v1/report.md)。動的配置交換という一般着想を発明したとは主張しない。

入力は実.wasmだが、固定memory32内のmutable graphを更新・巡回する閉じたprofileだけを受理する。一般のC/C++全体の変換器ではない。plain/fixed/movingと回復版、raw/O3を比較する。主6fixtureは3サイズ×2seedであり、6個の実アプリではない。診断用memory exportは配布版・解除入力に含めない。

## 再現

Windows、Python3.9、Node24.15、WABT1.0.42、Binaryen133。ツールの既定配置は`.tools/wabt-1.0.42/bin`と`.tools/binaryen-version_133/bin`。親の差替えは`WASM_TOOLS_ROOT`。SMTのみ`.tools/encoding-synthesis-python`のz3-solver4.13.3.0を使う。共通helperも使うのでrepo全体を保持する。新しい出力先を指定する。

```powershell
python research/mutable-factor/run.py results/mf-main
python research/mutable-factor/model.py results/mf-model
python research/mutable-factor/audit.py results/mf-main results/mf-audit
python research/mutable-factor/performance.py results/mf-main results/mf-runtime
python research/mutable-factor/report.py results/mf-main results/mf-model results/mf-audit results/mf-runtime results/mf-report

python research/mutable-factor/prototype.py transform results/mf-main/n16-v0-plain-raw.wasm results/mf-example.wasm --mode moving --seed 20261023
python research/mutable-factor/prototype.py recover results/mf-example.wasm results/mf-recovered.wasm
```

回復器は入力binary以外にsource・seed・正解manifestを受け取らない。完全profile照合を含む回復時間を、未知方式の発見時間や人間の解析費用と混同しない。有限テスト通過を全入力の実装同値証明としない。
