# GC生成器の実行到達性を分けて測る

2026-10-27。R/Sで入力を構築できても、実生成器のGCアクセスがほとんど増えなかった原因を調べた。**新しいfuzzerや難読化アルゴリズムを完成したとは主張しない。** [実装前計画](plan.md)、[実測](results.md)、[先行性と次の判断](next-decision.md)。

公式無改変wasm-smith 0.262のdefault/no-trapsを4型shape×64seedで比較する。型検証、関数への到達、命令直前、命令直後を区別し、計数器なしの実行も併記する。出力は実 `.wasm`。型shapeとseedは既存R実験の保存物を使う。

## 再現

Windows、Python 3.9、Wasmtime Python 50.0.1、Rust、Node 24.15.0、SpiderMonkey 150.0.1。Rust依存はCargo.lockに固定。公式wasm-smith crateは[既存Rの再現手順](../gc-witness/smith-reproduction.md)で取得した無改変コピーを参照する。計数器はwasmparser/wasm-encoder 0.227.1、生成器は0.262.0。

```powershell
$env:CARGO_HOME = Join-Path (Get-Location) '.tools/wasm-migrate-cargo'
cargo build --manifest-path research/gc-execution-gap/driver/Cargo.toml --release --locked --offline --target-dir .tools/gc-execution-gap-target
cargo build --manifest-path research/gc-execution-gap/instrument/Cargo.toml --release --locked --offline --target-dir .tools/gc-execution-gap-instrument-target
python research/gc-execution-gap/probe.py results/gc-execution-gap/fresh-probe
python research/gc-execution-gap/analyze.py results/gc-execution-gap/fresh-probe results/gc-execution-gap/fresh-analysis
```

初回の依存取得時はofflineを外す。出力先は新規ディレクトリを使う。Python packageは `.tools/import-alias-quotient-python`、SpiderMonkeyは `.tools/spidermonkey-150.0.1/js.exe`、NodeはPATH上。異なる環境では `probe.py` と既存Rのtool pathを調整する。

`probe-v1` / `analysis-v1` で両コマンドは完走した。502生成物、882組の計数あり/なし、1,764呼出し。校正は5形×2入力×2計数方式×3engineの60呼出し。生成器defaultの251binaryと5生成失敗は以前の無改変対照に一致した。

## 計数器の範囲

この計数器はimports/startがない、export sectionを持つ検証済み小moduleを対象とする。入力サイズは1 MiB以下。元の関数・global indexを保ち、末尾に関数entryとsiteごとの直前/直後counterを追加する。全global export値を実行後に読む。

追跡対象は `Struct*`、`Array*`、`RefCast*` 命令である。保存JSONの `all_gc` / `site_run_all_gc` はこの**追跡対象集合**を指す歴史的なフィールド名であり、ref.eq、ref.test、i31、br_on_cast等を含む全GC命令の網羅測定ではない。target accessは元shapeの型と同値な型へのstruct/array get/set（packed getを含む）。array.lenは型indexがないためtarget accessには含めない。

array.new等の長さに31 maskを適用したbounded版を両比較に使う。これは任意の元プログラムの意味保存変換ではない。計数器自体もfuel・stack・最適化に影響するので、無計数版との違いを結果へ残す。

一次資料は `priors-v2` に保存。著者公開MAD-EYE PDFは文字抽出が崩れたため、Popplerで3〜5ページを描画して確認した。外部公開・投稿・upstreamへの報告は行っていない。
