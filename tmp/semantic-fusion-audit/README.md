# 演算統合候補の先行研究照合

2026-10-12。前回の `../bulk-layout-wasm/README.md` の棄却後に実施。目的は、すぐ復元できる表現変更の試作を繰り返すことを避け、意味の再構成を対象とした候補の重複を先に調べること。論文原稿ではなく作業記録。

## 今回の判断

|案|保護対象・変換|近い既存研究|判断|
|---|---|---|---|
|H1: 複数演算を依存関係に沿って統合|中間操作の意味を、単独出力の式の中へ展開し、個別の小さな式としての合成を難しくする|LOKI §4.5|中核が直接重複。Wasm multi-valueや別の式生成器へ置換するだけでは採用しない|
|H2: 浮動小数点を高精度・整数表現へ移してMBA化|演算の表現と数値の対応を変える|FLOB §2.3、§3|浮動小数点へ広げるという方向自体に先行例。具体的に異なる規則も優位性もなく、現段階で実装に進めない|
|H3: ループや分岐を残して演算統合|制御を含む意味再構成を対象にする構想|LOKI §5、Tigress Virtualize|実装制約の違いだけでは新規性にならない。変換規則未定義のため研究候補として未採用|

H1/H2に新しいアルゴリズムが不可能という判断ではない。ここでの粗い案に既存方式との差がない、という判断。H3について検索に一致が少ないことを根拠に有望・新規とは扱わない。

## 確認した一次資料

### LOKI — USENIX Security 2022

[論文本文](https://www.usenix.org/system/files/sec22-schloegel.pdf)、[著者実装](https://github.com/RUB-SysSec/loki)。本文§4.4末尾、§4.5、§5の実装説明を確認。独立した複数出力を束ねるだけの方式と、SSA上の依存を用いた統合を区別している。したがって「依存した演算を一つにまとめる」をこちら固有の規則にしない。
§5のprototypeは制御フロー処理を簡略化しているが、著者は原理上の限界とは位置付けていない。単にループを扱う移植を新方式とは判断しない。
実装のREADMEとloki/READMEの構成・依存関係を確認した段階。コード本体の監査・実行・再現実験は未実施。mainの文書を参照し、コミット固定は未実施。著者の性能値を今回の環境の実測値として使用しない。

### FLOB — arXiv:2607.17603v1, 2026

[著者プレプリント](https://arxiv.org/html/2607.17603v1)。§2.3、§3冒頭、§3.1のAlgorithm 1とArithmetic Operationsを確認。数値とビット表現の違い、丸め、より高精度の表現への移行を扱う。この方向を未開拓とみなすことはできない。
本監査では査読済みとは確認していない。著者コードも未確認。一般のWasm命令列について、各段階の丸め、符号付きゼロ、NaNの観測まで同一にする規則が必要であり、本文の高水準説明だけからすべて対応済みとは断定しない。同様に、記述上の疑問だけで著者実装のバグとも断定しない。

### QSynth — BAR 2020

[著者公開PDF](https://profs.scienze.univr.it/~ceccato/papers/2020/bar2020.pdf)。§III-C Expression abstract syntax tree computation周辺のメモリ状態とbackward slicingの定義を確認。参照・メモリを増やせば既存の式再構成の対象から外れる、という前提は置かない。本文全体の監査・実装実行は未実施。

### Tigress Virtualize

[公式文書](https://tigress.wtf/virtualize.html)。検索結果で型付きAST・CFGからの変換とsuperoperatorsの説明を確認。今回の本文全体・実装監査は未実施。制御フローを含む仮想化の直接的な比較対象として残す。

### 実装として見つかったが効果を未確認の資料

[fortress-wasm RESEARCH.md](https://github.com/lkeld/fortress-wasm/blob/main/RESEARCH.md)の検索抜粋は、stack/control-flow operationの融合を掲げている。著者説明の存在と、SMT等に対する効果が実証済みであることは別。この監査では評価コード・実測を確認しておらず、強さの根拠には使わない。

## 次の案を実装へ進める条件

1. 解析者にバイナリ全体、任意入力、ローカル計測を許したとき、何の復元を保護するか一つに定める。未対応命令で解析器が止まることを成功にしない。
2. 変換規則を式・手順で記述し、LOKIの依存展開、既知の状態符号化、仮想化との違いを操作単位で対応付ける。
3. その違いが解析者の成功条件をどう変えるかを示す。式が長い、出力が多い、型が新しいだけでは通さない。
4. 最も近い方式と同じ処理を変換し、復元成功率とコストを比べられる実験を先に定義する。値だけを比較する対照と、制御まで比較する候補を混在させない。
5. 正しさ条件は追加コストと分ける。浮動小数点なら各命令の丸めと観測可能ビット、整数なら幅とoverflow、制御ならtrap・終了性を明記する。
6. 文献の実装が未対応というだけでは採用しない。アルゴリズムとしての差が示せなければ「適用実装の拡張」と分類する。

次の作業はH3の一般的な移植を作ることではなく、制御と値の依存を統合する具体的な規則に先行例があるかを、Tigressの命令統合範囲・LOKIの変換コードと照合すること。その照合で規則を具体化できなければH3も見送る。新規性があると結論できる候補は現時点でない。

## 調査ログ

検索日2026-10-12。以下の検索から上の一次資料へ進んだ。第三者の要約に記された成功率・新規性の主張は採用していない。

- LOKI harden code obfuscation synthesis superoperators USENIX 2022 paper
- WebAssembly obfuscation superoperators synthesis equality saturation
- obfuscation multi output synthesis coupled operations data flow MBA
- code obfuscation multi output superoperators data flow dependencies
- obfuscation floating point integer mixed domain arithmetic synthesis
- site:github.com/RUB-SysSec/loki superoperator（検索時は語句全体を引用したため有効性が低かった。網羅的検索とは扱わない）
- obfuscation loop-carried synthesis
- obfuscation rounding WebAssembly
- obfuscation stateful superoperators
- obfuscation superoperators control flow synthesis
- obfuscation semantic fusion loops

新しいWasmは生成していないため、この記録に実験成功数・バイナリSHAはない。前回までの結果は変更しない。研究全体の目標は未完了。
