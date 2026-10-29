# S: 指定した参照関係を持つWasm GCヒープの構築

2026-10-27。**動作する限定プロトタイプはできたが、修士研究の主テーマとしての新規性・効用は未確立。** 単純なDFSによる二段階構築も同じ515要求を生成した。新しい難読化方式の完成を意味しない。

実 `.wasm` の型を読み、JSONで指定した有限個のオブジェクト・フィールド・別名関係を持つテストモジュールを作る。入力モジュールの元の関数を実行する汎用ハーネスではない。

- [実装前の仮説](plan.md)
- [定式化・疑似コード・条件](algorithm.md)
- [先行研究との対比](prior-art.md)
- [実測と限界](results.md)
- [採否と次の研究判断](research-note.md)

## 環境

Windows、Python 3.9、Node 24.15.0 / V8 13.6、Wasmtime Python 50.0.1、SpiderMonkey 150.0.1。型読取器はR案のwasmparser 0.227.1を再利用する。公開アプリの静的プロファイルだけはwasmparser 0.262.0を使う。Cargo.lockを保存した。Python packageは `.tools/import-alias-quotient-python`、SpiderMonkeyは `.tools/spidermonkey-150.0.1/js.exe` に配置している。

新環境では同じ版のツールを用意し、`realize.py` が呼ぶRの `witness.py` と `experiment.py` のツール配置を合わせる。初回のRust依存取得時は下の `--offline` を外す。NodeはPATH上に置く。

## 再現

リポジトリのルートで実行する。各出力先は存在しない新規ディレクトリを指定する。

```powershell
$env:CARGO_HOME = Join-Path (Get-Location) '.tools/wasm-migrate-cargo'
cargo build --manifest-path research/gc-witness/checker/Cargo.toml --release --locked --offline --target-dir .tools/gc-witness-target
cargo build --manifest-path research/gc-realization/inspector/Cargo.toml --release --locked --offline --target-dir .tools/gc-realization-target
python research/gc-realization/experiment.py results/gc-realization/fresh-screen
python research/gc-realization/controls.py results/gc-realization/fresh-controls
python research/gc-realization/benchmark.py results/gc-realization/fresh-performance
python research/gc-realization/corpus.py results/gc-realization/dart-corpus-v1 results/gc-realization/fresh-corpus
```

上記の個別実験は保存済みの主結果ディレクトリで完走した。`audit.py` は既存の主結果 `screen-v1` / `performance-v4` とmanifestを監査する。

```powershell
python research/gc-realization/audit.py results/gc-realization/fresh-audit
```

CLIの最小例（`types-2.wasm` はnonnull mutable自己参照array）:

```powershell
python research/gc-realization/realize.py results/gc-realization/screen-v1/types-2.wasm research/gc-realization/examples/self-array.json results/gc-realization/example.wat
```

出力WATをWasmtimeの `wat2wasm` 等で変換し、export `run` を呼ぶと成功時に1を返す。`--mode dfs-staged` / `all-deps` / `null-patch` で比較方式を選べる。未対応、構築不能、予算超過は理由を表示してexit 2。型は元のtype sectionを保持するが、関数コード等は新しいテストモジュールへ置き換える。

## データと取得範囲

主結果は `results/gc-realization/{screen-v1,controls-v2,performance-v4,corpus-v2,audit-v1}`。中間失敗・測定法の修正前結果も削除していない。詳細な採用理由はresults.mdに記載する。

公開GCコーパスはmkustermann/wasm_gc_benchmarksのcommit `13951e126bd27d7560795b063e970cf5a96113ed` の12本、13,799,003 bytes。6設定それぞれの最適化前後であり、12独立アプリではない。Git blob SHA-1とSHA-256を記録した。ダウンロードしたアプリを実行せず、静的検査だけを行った。

保存済みtree metadataから同じbinaryを取得し直せる。`fetch.py` は一部URLがmainを指すため、最新取得を過去の同じsnapshotと混同しない。

```powershell
python research/gc-realization/fetch-corpus.py results/gc-realization/priors-v2/dart-tree.json results/gc-realization/fresh-dart-corpus
```

外部参照が取得できない場合も、保存したmanifest・snapshot・実測値を参照できる。既存の根元READMEと論文本文は変更していない。
