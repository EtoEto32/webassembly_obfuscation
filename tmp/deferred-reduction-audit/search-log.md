# 検索記録

2026-10-12

検索語:
- residue number system delayed modular reduction lazy reduction range arithmetic obfuscation
- compiler delayed modular reduction range analysis integer overflow residue number system

本文確認:
- https://eprint.iacr.org/2017/437.pdf : §1–4（冗長表現、範囲、遅延補正）。本文の後半の実験再現、コード検証はしていない。
- https://eprint.iacr.org/2017/437 : 書誌ページ。
- https://patents.justia.com/patent/11755288 : 公報本文の転載。Detailed Descriptionのpseudo-residue定義、postponed reduction、obfuscating numberの選択、範囲条件を確認。記載された安全性の主張を実験で検証したとは扱わない。

取得不能:
- https://patents.google.com/patent/US11755288B2/en : webツールで取得失敗。上記公報本文を代替参照。

検索結果のみ・判断の根拠にしていない:
- RNS Montgomery reduction algorithms using quadratic residuosity (2018)
- Improvement of a Montgomery Multiplication Algorithm in Single-Base Residue Number System (2026)
- A Multi-layer Recursive Residue Number System (2018)

検索の不在を新規性の証明にしない。今回の判断は遅延補正だけの候補に限定し、RNSを用いた未知の変換全般を否定しない。

前回の研究作業はプロンプト出力のみで実装・実験の進捗なし。今回は既存監査を再読し、関連する一次資料本文を確認して、未確定だった候補の採用・不採用の判断を記録した。新しい実測値なし。利用枠はusedPercent=12、残り88%だった。
