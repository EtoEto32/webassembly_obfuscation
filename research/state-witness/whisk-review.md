# Whiskとの対象・実装比較

2026-10-24。著者の公開[Whisk](https://github.com/nokia-steward/web-assembly-self-certifying-compilation-framework)を確認した。元nokia URLはnokia-stewardへ移転している。取得した最新commitは`8c31df0bd7d2d94cfbc22089944f5cabb3a61158`、committer日時2020-10-22T12:35:42Z。2026-10-24以前という上限を付けて取得した。

[文書provenance](../../.tools/whisk-review-v2/provenance.json)と[選択ソースprovenance](../../.tools/whisk-review-v2/extra-provenance.json)へURL・Git blob・SHA256を保存した。README/LICENSE/Makefileと、WHISK.md、関係proof/state型、fully interpreted evaluator、CFG builder等の選択10ファイルを取得した。主要な読了箇所はREADME/WHISK.md、proof_types.mlのproof構造、state_types.mlの状態とarray型、full_sym_eval.mlの命令case・memory size/grow・trap条件である。全repositoryの読了や著者の全評価の再現ではない。

## 既にあるもの

Whiskはsource/targetの状態関係をcertificateとして受け取り、独立validatorとSMTで最適化を検査する。proof型はcheckpoint edge対、refinement map、frontier map、path correspondenceを持つ。call前後に関係を置き、trap条件も検査する。したがって「二つのWasm状態をSMTで関係検証する」はKの新規性にならない。単にZ3へ等式を送る実装も既知である。

Kの現在の入力は同じmoduleと初期segment寿命対、選んだAPI観測/再入契約であり、初期共通storeに対する条件を出力する。WhiskのCLIは最適化passとproofチェックを指定し、内部CFGに対する変換certificateを扱う。今回のソースのfull evaluatorにはMVP命令caseと固定memory容量モデルがあり、bulk init/dropやsegment寿命のcaseは確認できなかった。この版をそのままKのbulk診断入力へ適用できると確認したわけではない。一方、Whiskはloop・制御フロー・局所変数等を扱い、Kより広い部分もある。単純な機能の包含関係や優劣ではない。

## 実行比較ができた範囲

この環境にはWhisk指定のOCaml4.07.1/opam/ocamlbuildがなく、必要な変更版reference interpreterも未buildである。WSLの一覧取得はE_ACCESSDENIED、Dockerの既存daemonへの照会はpipe不在となった。公開資料取得は行えたが、Whisk本体は実行していない。これらは環境・準備の未達であり、Whiskの解析失敗件数ではない。古いtoolchainのglobal installやservice起動は行っていない。

## 代替の直接比較

著者実装の代わりと偽らず、[標準的なCHC/Spacerの比較](guard-chc-plan.md)を別に実装した。同じ具体初期storeからAPI観測差へ到達できるかを解く課題であり、条件合成そのものの比較ではない。これはKの具体判定が汎用モデル検査にも可能かを調べる補助実験である。

WasmVerifierの2026年プレプリントも§5を再確認したが、今回読めた本文にpublic repositoryのリンクを発見できなかった。著者実装は未取得・未実行であり、未対応と断定した件数を作らない。
