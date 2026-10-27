# 型のアクセス言語を増やす仮説の事前検査

2026-10-21。直前の区間は保存成果の確認で、新候補の研究としては no progress。
今回は型回復器の実装から反証可能な機構を選び、実行できる解析基盤を準備する。
有限環残差方式の構成的な限定採用を変更しない。

## 仮説

Wasm memory32 の i32 値にはポインタと数値の区別がない。load/select/loop の
型制約を使い、少数の変数から多数の異なるアクセス経路を作る。型回復器の
決定化で候補集合が増えるなら、暗号・局所復号式とは異なる分析費用を狙える。
ただし NFA の部分集合構成と指数的な状態数は既知であり、それ自体は新規性にしない。

まず次の read-only 制約族を調べる。記号 0/1 は offset 0/4 の32bit load。
q0 --0--> q0, q0 --1--> {q0,q1}, qi --0/1--> q(i+1)。
qn の offset 8 に整数を要求する。これは型制約であり、実行時の非決定性ではない。
標準的な末尾から n 番目の記号を判定する NFA を対照にする。

重要な反証は、型解析が同じ load の行き先を同一形状へ統合して、指数的な
候補を作る前に消す可能性である。NotDec の subset 用コードだけを見て
実ツール全体の指数的負荷を主張しない。

## 実験の範囲と判定

- GrammaTech の公開 Retypd Python 実装を変更せず呼ぶ。NotDec 本体の実行とは分ける。
- 初めは n=1..8。各子プロセス30秒上限。ローカルの研究入力だけを解析する。
- DFA と path-expression の solver、形状 graph、生成制約数と時間を記録する。
- 抽象 NFA の状態数を測定しても、その数を Retypd の実測と混同しない。
- 発生機構が成立した場合にのみ意味保存変換へ進む。成立しなければ前段で棄却し、
  費用の大きい架空の「難読化アルゴリズム」を実装しない。
- この検査だけで元の研究目標を完了しない。世界初・特許性・解析不能を主張しない。

## 確認した一次実装

NotDec commit 0399bf0aec0f26247fee99097cb9442e4414bb0f:
`src/Passes/ConstraintGenerator.cpp` の select/phi/load/store 生成、determinize、
`include/notdec/TypeRecovery/NFAMinimize.h` の集合移動・epsilon閉包を読んだ。
https://github.com/NotDec/NotDec

Retypd commit 8f7f72be9a567731bb82636cc91d70a3551050bf:
`src/solver.py`, `src/graph_solver.py`, `test/test_endtoend.py` を確認。
GPLv3 の原本を `.tools/retypd-source` に保持し、プロジェクト本体へコピーしない。
https://github.com/GrammaTech/retypd

Noonan, Loginov, Cok, *Polymorphic Type Inference for Machine Code*, PLDI 2016。
今回確認した論文範囲は arXiv 要旨・著者・会議情報だけ。本文の計算量を推測しない。
https://arxiv.org/abs/1603.05495

比較候補の事前除外：自己調整木でアクセスを変える一般案には US7975149B2 の
記載がある。今回確認したのは一次検索の概要・splayの説明で、全請求項ではない。
https://patents.google.com/patent/US7975149B2/en

検索語: Retypd type inference determinization exponential type obfuscation;
"obfuscation" "type inference" "exponential"; "type recovery" "determinization"。
検索で同じ案が出なかったことは新規性の根拠にしない。
