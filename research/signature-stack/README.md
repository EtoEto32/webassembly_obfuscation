# P：Wasm検証用のsignature区間スタック

2026-10-26。**動く研究プロトタイプはできたが、新しい修士主テーマへの採用は保留**。同一型列の展開を省ける一方、単純な配列キャッシュでも効果の大半が出る。型列を分割して積むだけで幅依存の照合が残る。実プログラムの高速化も未実証。

- [事前計画](plan.md)、[強い比較対象](strong-baseline-plan.md)、[最悪ケース反証](fragmented-plan.md)
- [アルゴリズム・正当性の条件](algorithm.md)
- [先行技術と新規性判断](prior-art.md)
- [実測結果](results.md)、[日本語研究ノートと主テーマ判定](research-note.md)

## 実装の範囲

Wasmバイナリを読み、numeric function bodyの型検証を行う。バイナリを書き換えず、実行もしない。`flat`、`cached`、`segment`は同じ構文解析・制御フロー処理を使う。型宣言・関数宣言・export/start等のmetadataはwasmparser 0.227.1に委譲する。function bodyの標準validatorは自作kernelの中では呼ばない。比較用`stock`は0.227.1、`stock-current`は2026年10月の0.262.0による全体検証。

対象はi32/i64/f32/f64/v128、block/loop/if、多値、direct call、branch、local、select、限定numeric演算。対応演算は`checker/src/main.rs`のdecodeを参照。GC/reference subtyping、EH、memory/table/global操作、indirect call等は未対応。function import以外のimportと、memory等のsection自体も初版ではunsupported。v128の一般演算にも未対応。

`valid` / `invalid` / `unsupported` / `resource_limit`を分離する。input 4 MiB、local数50,000という研究用上限がある。stockが返すinvalidには**指定feature setで無効**な場合も含む。Wasm全般で不正なbinaryという意味に拡大しない。unsupportedはvalidの代用にしない。

## 再現

実測環境：Intel Core i9-11900K（16 logical processors）、Windows（PowerShell OS報告26200、Python platform報告26100）、Python 3.9.0、Node 24.15.0 / V8 13.6.233.17、WABT 1.0.42、Python wasmtime 50.0.1（WAT変換のみ）、Rust 1.97 nightly。Cargo.lockを保存した。共有PC上の測定でありCPU固定・隔離はしていない。取得元の違いを含む環境記録は`results/signature-stack/environment.json`に保存した。

リポジトリrootのPowerShellから：

```powershell
$env:CARGO_HOME = Join-Path (Get-Location) '.tools/wasm-migrate-cargo'
cargo build --manifest-path research/signature-stack/checker/Cargo.toml --release --locked --offline --target-dir .tools/signature-stack-target
.tools/signature-stack-target/release/signature-stack.exe check INPUT.wasm
.tools/signature-stack-target/release/signature-stack.exe bench INPUT.wasm segment 11
.tools/signature-stack-target/release/signature-stack.exe profile INPUT.wasm
python research/signature-stack/experiment.py results/signature-stack/reproduce-correctness
python research/signature-stack/benchmark.py results/signature-stack/reproduce-performance
python research/signature-stack/spec-check.py results/signature-stack/spec-source-v2 results/signature-stack/reproduce-spec
python research/signature-stack/corpus.py results/signature-stack/reproduce-corpus
python research/signature-stack/fragmented.py results/signature-stack/reproduce-fragmented
python research/signature-stack/audit.py results/signature-stack/audit-v1.json
```

各再現先は未存在のdirectoryを指定する。キャッシュがない環境では`--offline`を外して固定版の依存を取得し、`experiment.py`のツール配置を調整する。第三者にはPythonのwasmtime、Node、WABT、Rustと公開入力が必要。公開入力URL・commit・hashは各manifestとcorpus provenanceに保存した。

`check`は複数ファイルの判定をJSON Linesで返し、判定がinvalidでもプロセスは正常終了する。終了コードだけで受理してはならない。運用サービス用のセキュリティ境界として使う段階ではない。

`profile`は現在の標準validatorで受理したmoduleのdirect call・block/loop/ifの型幅を数える**機会調査**であり、自作kernelによる全機能の検証や実行時間予測ではない。

## 記録の対応

確定比較は`performance-v2`の40条件×4方式×3process = 480 process。各processはwarmup 5回、calibration 5回、最大512回のbatchを11回測る。batchは10 msを目標とするが上限に達した小例ではそれ未満になる。sampleは1validationあたりの秒へ戻し、process内中央値→3processの中央値で集計する。kernelだけでなく解析・intern・検証込みend-to-endも保存。

`correctness-v3`、`performance-v2`、`spec-check-v2`、`corpus-v1`、`fragmented-v1`にはソース、Cargo.lock、当時の実行ファイルのsnapshotがある。v1/v2の初期correctnessとperformance-v1は探索履歴。初期manifestのmutable source hashは現在のソース一致を意味せず、その版の完全再現性を主張しない。

測定済みJSONの`compared_cells_upper_bound`は**比較対象sliceの長さの合計**であり、実際の比較命令数の上限ではない。Bottom-aware fallbackでは再走査する。この誤解を避けるため現行CLIでは`comparison_span_cells`へ改名した。計算内容は同じで、過去ログは変更していない。
