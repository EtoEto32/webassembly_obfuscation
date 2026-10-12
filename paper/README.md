# CSEC研究報告の原稿

## 2026年10月11日の追記

利用者の「じゃあ論文も反映していいよ」により原稿を更新した。題目と考察は「解析支援手法の検討」とし、局所正規化と読み取り専用の式比較を候補として扱う。対策の完成、速度向上、検知改善は主張しない。

既存13件の評価に加え、SWAMPED由来の72条件・23SHA・各6反復（138回）を反映した。同じSHAは測定を共有し、公表5入力の独立期待値と追加12入力の比較を区別する。短入力の順序依存と原因未特定も記した。根拠は `docs/countermeasure-experiment-report.md` と `results/countermeasures/runtime-runs/execute-120f528e37424ec6806047c933011eec/summary.json`。旧3反復の表・図はその条件を維持する。

同じmain.texを編集し、内蔵コンパイラの環境エラー後に既存TeX Liveでmain.pdfを更新した。参考文献込み8ページで、全ページ表示確認済み。根拠は `results/mining-methods/current-compilation.json`。以前の対策ゴールにおける論文未変更監査は、その記録時点の履歴である。

2026年10月8日時点の記録である。編集対象は`main.tex`、参考文献は`references.bib`である。この記録を作成した時点の題目は「公開WebAssembly採掘データセットにおける難読化とハッシュ計算性能の実証分析」である。著者・所属・指導教員は原稿に記入済みで、提出時の表記は本人が確認する。

## 研究の中心

RQ1では、公開された採掘プログラムのファイルで、どの処理がどのように変換されているかを確認する。通常の暗号処理や研究用の計測コードとも区別する。RQ2では、対応するバイナリで正しいハッシュを計算できるか、速度・命令数・サイズがどう変わるかを比較する。

考察では、この二つを結び付ける。例えば、変換箇所が存在しても、測定入力でそこを実行しなければ、その変更を速度差の原因とはしない。設定名だけが分かるファイルと、難読化の仕組みまで確認できたファイルを区別する。ファイル数や数え方を主な貢献にしない。

## 保存済みの実測と確認範囲

ローカルで追加の繰り返し測定を行ったバイナリは13個である。Proof-of-Theftの配布ファイル10件、SWAMPEDの入力ファイル1件、公開コードを使って今回作成した変換版2件を含む。参照テストベクトルとの照合は、限られた入力での確認であり、すべての入力で正しい出力を得られることの証明ではない。

- xmr-wasmの5ファイルは、3秒のウォームアップ後、各30秒以上の測定を3回行った。配布された基準版の速度の中央値は9.11 H/sで、平坦化版は6.18 H/sであった。配布ファイルを作成した際のビルド条件を揃えられていないため、この差が難読化手法によるものとは断定しない。
- webminerpoolhashcnの5ファイルは、各5秒の予備測定を3回行った。cn/0の公表ベクトル照合と、cn/picoの速度・保存済み受理出力の照合を区別する。配布Makefileの設定不一致があり、ディレクトリ名を確認済み手法名とは扱わない。
- SWAMPED入力へのnop挿入・整数定数分割は、同じ条件でWasmバイナリに変換し、各30秒以上の測定を3回行った。速度の中央値の比は0.960と0.973だったが、各測定回の比は1より大きい場合と小さい場合があった。この小さな差を、確実に増えた負荷とは判断しない。

SWAMPED入力と同じSHAのファイルは複数のデータセットに再収録されている。同じファイルや共通の暗号計算部分を、独立した実装で結果が再現された例として数えない。既存の外部プール実験は過去の記録として扱い、新しいローカル実測と分ける。

## 根拠と再現手順

主要ファイルはリポジトリのルートから次の場所にある。

| 内容 | ファイル |
| --- | --- |
| RQ1と実測した13ファイルの対応 | `results/runtime-mining/cross-dataset/rq1-rq2-runtime-evidence.json` |
| 先行研究の評価範囲と今回の追加点 | `results/runtime-mining/cross-dataset/prior-work/evaluation-comparison.csv` |
| 生ログ・集計・図表の一覧とSHA | `results/runtime-mining/cross-dataset/current-evidence-index.json` |
| 作業全体の完了条件と未完了事項 | `results/runtime-mining/cross-dataset/goal-requirements-audit.txt` |
| 再解析・再開の手順 | `experiments/runtime-reference/reanalysis-guide.txt` |
| 申込用の和英タイトル・概要案 | `experiments/runtime-reference/csec-submission-draft.txt` |

追加候補cryptonight-hashは、内部関数の引数・戻り値など、ABIの一部と制御フロー平坦化を静的に確認した。エクスポートだけを追加した派生版と実行用コードも準備した。ただし、出力・速度は未測定で、上記13バイナリの結果には含めない。`scripts/prepare_cryptonight_repetitions.py` は順序を変えた3回繰り返す測定の計画を生成し、既存ログを検証するだけで、実験を起動しない。この記録時点では、有効な追加ログは0件である。

大学PCで新たにハッシュ計算を実行することは指導教員の許可確認後に限る。保護設定を変更せず、遮断されたファイルを迂回実行しない。新しい評価は報酬を発生させない、ネットワーク無効の隔離されたローカル環境を使う。

## コンパイルと提出前の確認

現在開いている `main.tex` を同じLaTeXエディタで編集する。2026年10月8日、既存の `C:\texlive\2026\bin\windows` をそのPowerShellプロセスのPATHに追加し、`paper/build.ps1` で現在の `main.pdf` を更新した。内蔵コンパイラの `Unable to find standard directories for platform` は、ローカルTeX Liveの利用不可を意味しない。新しいTeX環境の導入は行っていない。

現原稿は参考文献込み8ページで、提出用の6～8ページの範囲を満たす。最終コンパイルのログとPDFを確認し、過去のPDFや点検記録とは区別する。

`scripts/audit_mining_paper.py`は、短縮稿については`audit_compact_mining_paper.py`を使い、現在のRQ、引用・相互参照、図ファイル、主要実測値と現在のビルド結果のSHA・ページ数を確認する。詳細稿用の静的指標点検は同スクリプトに保持する。静的な点検だけでは、PDF自体の確認の代わりにならない。今回のビルドの証拠は `results/mining-methods/current-compilation.json` に保存する。

`build.ps1`、`latexmkrc`、`csec-template.zip`は、既存のビルド・ひな形用ファイルである。提出パッケージの完成や申込完了とは扱わない。

研究上は、元の配布版のビルド条件の再現、実装の共通性の確認、必要な追加の繰り返し測定、難読化の仕組みについて別の評価者による確認が残る。申込案の保存は申込完了を意味せず、申込・投稿の操作は本人が行う。

## 公式スタイルの出典

情報処理学会の公式クラスv4.1のUTF-8版を使用し、研究報告用に `\documentclass[submit,techrep]{ipsj}` を指定している。`ipsj.cls`、`ipsjtech.sty`、`ipsjunsrt.bst` の著作権表示を保持し、ページ数調整のためにクラスやスタイルを変更しない。

公式ZIPは2026年10月6日に取得した。SHA-256は `99A165EA4E7BCCB0AB54A2B9C1F21D19D77744876A20708EE37EC954D00EBC59`。原本と展開物は `vendor/` に保存している。

- [研究報告原稿作成について](https://www.ipsj.or.jp/kenkyukai/genko.html)
- [公式スタイル配布ページ](https://www.ipsj.or.jp/journal/submit/style.html)
- [CSEC115等の募集案内](https://www.ipsj.or.jp/kenkyukai/event/eip114spt65csec115.html)

引用の評価内容は、実際に確認した本文・補足・公開コードの範囲に限定する。WASMixerはarXiv第1版の評価本文を確認したが、ESORICS 2024出版版の評価本文は未確認。先行研究との差の根拠は上記の比較表を参照する。
