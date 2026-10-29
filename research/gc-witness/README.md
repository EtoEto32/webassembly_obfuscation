# R: 非null GC値の構築証拠を生成する限定プロトタイプ

[設計](algorithm.md)、[事前仮説](plan.md)、[先行技術との差](prior-art.md)、[実測と厳格判定](results.md)。**修士主テーマとしての新規性は未確立。** 既存型を変更せず、再帰型の空arrayやfunction参照を使って非null値と有限のアクセスpathを生成する。

2026-10-27追補: [実wasm-smithの強い対照と2,022入力呼出し](smith-results.md)を追加。最小修正で構築成功が増え、入力深さ探索での新規accessは1生成物・深さ1で十分だった。主テーマへの昇格を支える独自効果は得られていない。[追加試験の再現](smith-reproduction.md)。

根元README・既存論文本文は変更していない。新しい難読化方式の完成を主張するものではない。

## 環境と再現

Windows、Python3.9、Node24.15.0、Rust、wasmparser/wasm-encoder0.227.1、Wasmtime Python50.0.1、Binaryen133、SpiderMonkey150.0.1。依存Rust版はchecker/Cargo.lock。Python packageは既存の `.tools/import-alias-quotient-python`、engine/toolは実験環境に記載したworkspace配置を使用する。第三者の新環境では同じ版を用意しwitness.py/experiment.pyのtool pathを合わせる。

repo rootから:

```powershell
$env:CARGO_HOME = Join-Path (Get-Location) '.tools/wasm-migrate-cargo'
cargo build --manifest-path research/gc-witness/checker/Cargo.toml --release --offline --locked --target-dir .tools/gc-witness-target
python research/gc-witness/reproduce.py results/gc-witness/fresh-reproduction
```

初回にRust依存がない場合はofflineを外して取得する。一括scriptは、生成と3engine検査、負の対照、実Binaryen生成、counter付き実行、反復benchmarkを順に実行する。出力先は新規directoryに限定する。各構成scriptは今回個別に完走しており、一括wrapper自体の追加完走は未実施。

実binaryからWAT witnessを作るCLI:

```powershell
python research/gc-witness/witness.py results/gc-witness/screen-v1/self-array-types.wasm --target 0 --path '["e","e"]' --output results/gc-witness/example.wat
```

出力は同じ型sectionを持つテストmodule。元binaryのコードを動かす汎用API harnessではない。tree/memo/worklistは`--mode`で切り替える。非対応・構築不能・予算超過はexit2で理由を返す。

保存物監査:

```powershell
python research/gc-witness/audit.py results/gc-witness/fresh-audit
```

主dataはscreen-v1、controls-v1、binaryen-v1、binaryen-exec-v1、performance-v1、audit-v1。初期source取得失敗もpriors-v1として保存。各結果のsource snapshotは当時のコードであり、再実行はrepo側のscriptから行う。
