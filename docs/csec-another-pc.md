# CSEC研究を別PCで再開する手順

**2026-10-29 更新:** RQ1とRQ2は[独立した2リポジトリへ移行](../CSEC-PROJECTS.md)した。現在の研究を別PCで再開する場合は，分離先のREADMEを使う。以下は統合時点を復元するための過去の手順として保持する。

2026-10-29。対象は、既存成果を保持しながら難読化前後の性能・出力を評価し、その結果からコード正規化の可能性と課題を検討するCSEC研究である。新しい難読化アルゴリズムを探索する別テーマの入口は [HANDOFF.md](../HANDOFF.md) にある。

## リポジトリの取得

GitとPythonを用意し、PowerShellで次を実行する。Windowsではパスが深くなるため、短い場所にcloneする。下記は実行時のカレントディレクトリの下に新しいフォルダーを作る。

```powershell
git -c core.longpaths=true clone --single-branch --branch codex/research-artifacts-20261013 https://github.com/EtoEto32/webassembly_obfuscation.git
Set-Location -LiteralPath webassembly_obfuscation
git config core.longpaths true
python scripts/restore_handoff.py
```

最新研究は `codex/research-artifacts-20261013` ブランチにある。通常のcloneで選ばれる `main` と取り違えない。すでに別PCで取得済みの場合は、作業中の変更を保存したうえで対象ブランチを選び、`git pull --ff-only` で更新する。

復元スクリプトは標準ライブラリで動作する。Python 3.12を用意すれば、CSEC追加評価で用いたホスト側Pythonの系列にも合わせられる。インストール済みPythonの版は `python --version` で確認する。

## 成果物の復元範囲

コード・研究ノート・通常のログ/JSON・提出用PDFはGitで管理している。ignore対象の実験Wasm/WAT、大容量の生成表、取得元metadata等は、`handoff/snapshot-20261027/` の19分割アーカイブに保存している。合計圧縮サイズは785,795,039バイト、復元対象は101,805ファイル・4,525,465,734バイトである。CSEC以外の研究成果も含む。

上記の `restore_handoff.py` は分割・アーカイブ全体・各ファイルのSHA-256を検証し、リポジトリ内の元の相対配置へ復元する。既存の異なるファイルは上書きしない。一致しない場合は元の変更を保持し、新しいclone先で復元する。検証だけなら `python scripts/restore_handoff.py --verify-only` を使う。

取得済みの大容量元データ約226 GB、`.tools/`・`.venv/`・`.tf/` 等のインストール済み環境、認証情報は、このGit引き継ぎには含まれない。必要な入力は別途保存したNASのプロジェクト全体バックアップから復元するか、[既存の再取得手順](reproduction.md)と登録済み取得元・ハッシュを参照する。NASのパスワードをリポジトリに記録しない。

## CSEC研究の読む順序

| 内容 | 入口 |
| --- | --- |
| 現在の8ページ原稿 | [TeX](../paper/main.tex)、[原稿の説明](../paper/README.md) |
| そのまま確認できる配布版 | [PDF](../deliverables/csec-20261027/main.pdf)、[ソースZIP](../deliverables/csec-20261027/csec-source.zip)、[SHA-256記録](../deliverables/csec-20261027/manifest.json) |
| 性能評価から正規化検討への流れ | [追加評価の統合報告](followup-research-report-20261016.md) |
| 出力・JIT条件・速度・動的実行箇所 | [性能評価報告](followup-performance-results-20261016.md) |
| 正規化後の出力照合・対応付け評価と限界 | [正規化比較報告](followup-normalization-results-20261016.md) |
| 固定入力・計画・隔離実行・監査の手順 | [追加評価の再現手順](followup-reproduction-20261016.md) |

追加評価の計画・生ログ・集計・図表・監査・失敗記録は `results/followup-evaluation-20261016/`、実行用ホストコードは `experiments/runtime-reference/`、準備・起動・監査・集計用コードは `scripts/` にある。従来の成果も保持し、別PCでの測定値を過去の値と混ぜない。有限入力での出力一致や命令数の減少だけから、一般的な意味保存や解析容易性を断定しない。

## 原稿編集と追加実験

原稿編集は `paper/main.tex` を起点にする。TeX Live等で `platex`・`pbibtex`・`dvipdfmx` を使える状態にして、リポジトリルートから次を実行する。

```powershell
powershell -File .\paper\build.ps1
```

`deliverables/csec-20261027/` は保存済み配布版で、原稿のビルドによって自動更新されない。編集後の成果は `paper/main.pdf` と比較する。

追加実験は [再現手順](followup-reproduction-20261016.md) の資産照合と実行条件を確認してから進める。ホスト側Python・Node・WABT/Binaryenと、計時に用いたコンテナ内Node/V8の版を区別する。既存計画はDockerイメージIDを固定しており、GitのcloneやNASのプロジェクトフォルダー復元だけではDockerイメージは移らない。同じイメージが必要なら元PCで `docker image save`、移行先で `docker image load` を行ってIDを照合する。Dockerfileの再buildで同一環境になるとは限らない。

既存の計画・ランナーは入力等のSHAを照合する。古いスクリプトや記録に残るユーザー固有の絶対パスは、移行先に合わせて確認する。元の計画を無断で書き換えて同じ測定条件と扱わない。再測定は保存済みの結果を上書きしない実験用コピーで行い、CPUや実行環境が違えば条件の異なる追試として記録する。新PCでの実験実行や全環境の動作確認は、今回のGit引き継ぎでは行っていない。
