# G: import同一性の商によるWasm境界検査の仮説

2026-10-24、実装前固定。Fの課金方式とは別に、hostが同じMemoryを複数importへ渡す場合の境界意味を対象にする。最初は防御・検証用のmetamorphic oracleであり、新特許やruntime脆弱性の発見とは宣言しない。

## 原理と対照

module Mのmemory import indicesに、実object同一性のpartition Pを与える。各memory命令・data segment・exportのindexを同値類の代表へ写し、重複importを除くmodule Q(M,P)を構成する。MにはPに従って同じMemory objectを複数名で渡し、Qには各同値類1個を渡す。初期内容と全呼出し列が同じなら、返値・trap・各物理memory内容・export同一性が対応すべきである。単にindexを違えても同じものを参照するケースを、別runtimeに依存せず比較できる。

強い既存対照は全partitionを同じ意味で手書き検査する方式、通常のruntime差分試験、specのalias例。全importを別objectにする試験との比較だけで新規性を主張しない。memory.copyの重なり、grow後のサイズ、trap前の副作用、active data初期化順を含める。安全性の機構ではなく、隔離の前提と実装を検証する機構。

## 初期範囲

標準memory32、非shared、全memoryがimport、同じlimits、最大4imports、各1～3pages。i32整数、load/store、size/grow、fill/copy/init/dropと限定構造化制御。host function imports、concurrency、memory64、atomic、例外、Componentは後段。実行環境はNode/V8とWABT、通常O3も比較する。バイナリの全index使用箇所を未対応なら拒否する。

## 成功・失敗条件

1. `.wasm`変換を行いWABT validationとNode validationに通す。
2. n=2～4の全partitionとboundary/random入力で元/商の観測を比較する。trapを正常値と分けて記録。
3. 意図的な「異なるindexなら非alias」変換mutantをoracleが検出できるか確認する。mutant検出は実runtimeの脆弱性発見と区別。
4. 既存spec/fuzzerが同じ商oracleを持つなら主発明から除く。Wasm固有の適用だけなら新規性は弱いと記録する。
5. 最大2段階の実装検討後、明確な追加技術効果がなければテスト資産として保存する。

## 初期先行調査

- [Bento公式紹介](https://syssec.informatik.uni-due.de/en/research/research-projects/webassembly-security): Oussama Draissi, Lucas Davi、WWW2026、DOI 10.1145/3774904.3792439。pointer analysisとmulti-memory分割は既知。紹介だけ読了、ACM本文取得は403。輸入aliasへの具体的対応・限界を未読のまま断定しない。
- [WebAssembly multi-memory](https://github.com/WebAssembly/multi-memory/blob/main/proposals/multi-memory/Overview.md): 複数memoryは標準の機構で、発明要素ではない。
- [Wasmtime dummy import生成器](https://raw.githubusercontent.com/bytecodealliance/wasmtime/main/crates/fuzzing/src/oracles/dummy.rs): 取得したmainでは各importにdefault_valueを生成しnameでlinkerへ登録する。このファイルだけからfuzzer全体がaliasを検査しないとは結論しない。
- [Metamorphic Testing for (Graphics) Compilers](https://www.doc.ic.ac.uk/~afd/homepages/papers/pdfs/2016/MET.pdf): 取得した関連節にはalias解析を複雑にする変換の方向が記されている。全本文の比較は未了。metamorphic testing自体は既知。
- [Finding Bugs in WebAssembly Interface Type Binding Generators](https://www.flux.utah.edu/paper/stanley-ase25): Ethan Stanley, Eric Eide、ASE2025、DOI 10.1109/ASE63991.2025.00025。公式要旨のみ読了。binding generatorの差分試験は先行する。

最大のReject理由は、host objectのaliasをmodule indexの置換へ写すという標準的な意味保存変換を新原理と呼んでいるだけになること。新規性があるとすれば自動的な検査契約と有効な縮約規則の部分だが、現時点では未確立。
