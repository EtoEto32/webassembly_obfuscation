# 候補：識別子を持たないオペランド再基底化と残差トランスデューサ融合

2026-10-18。ユーザーの「発明してくれ」という再指示を受け、既存2案の終了監査で止めずに具体的な構成へ進む。本案は新規性・保護効果をまだ認定していない。

## 発明仮説の核

共有kernel K(u,v)=u+v を使う。単一の演算だけなら、加算は(a,b)、XORは(a,b−2(a&b))を渡せばよい。しかしこの恒等式をそのまま置くとMBA簡約で解除できる。新規性候補は恒等式ではなく、**前段の計算Fを含めて残差H=F−anchorを一体で合成し、Fのword値を計算せずに2つのstack値(anchor,H)を生成する構成**である。

第一の構成条件：Fがanchorとは別の入力pivotについて全単射であること。pivotが一度だけ現れ、根までの各演算がadd/sub/xorで、その演算の他方の入力がpivotに依存しなければ十分。Wasmの32bit剰余演算について成り立つ。全入力を独立一様とした場合、(anchor,F−anchor)は全2^64組に同じ頻度で写る。異なるFも同じkernel入力支持集合を持つ。これは局所のkernel入力だけからの処理種別判別を排除する条件であり、公開された呼出し元を含む解析者への安全性ではない。

第二の構成条件：残差を `Fを計算; anchorを引く` と実装しない。Fと減算を最下位bitから進むMealy transducerとして同時にコンパイルする。各add/subノードのcarry/borrowが状態、各入力wordの同じ位置のbitが入力記号となる。Fのwordをassembleせず、Hのbitだけをassembleする。到達不能状態除去・Mealy最小化の後、Wasmのprivate table dataと32反復の共通実行器へ変換する。多値返却で(anchor,H)をそのまま共通加算へ渡す。

```
認識した純粋i32領域Fについて:
  pivotの全単射性を十分条件で検査
  H := F - anchor
  carry/borrowを同時に進めるbit遷移系を構成
  初期状態からの到達集合を計算
  出力bitと遷移先でMealy状態を最小化
  Hだけを組み立てるWasm実行器とprivateな遷移表を生成
  (anchor,H)をmulti-valueでKへ渡す
```

対応範囲はまず4入力、add/sub/xor/and/or、定数0/-1、純粋な式。メモリ副作用・trap・可変シフト・乗算・ループは元領域に含めない。Wasm側の整数幅、32回の反復、多値の型検査を使用する。一般的なオートマトンによる算術計算を新発明とはしない。

## 先行例と差分の監査

- Van den Broeckら、[Obfuscated Integration of Software Protections](https://users.elis.ugent.be/~brdsutte/research/publications/2021IJISvandenbroeck.pdf)の検索取得Fig.4周辺：code factoringで異なる文脈を共有し、register調整により非同一fragmentも統合する先行例を確認。単純なstack shuffleや共有blockへの置換を新規性にしない。全文・全評価数値は未読。
- Schloegelら、[LOKI](https://mschloegel.me/paper/schloegel2022loki.pdf)：意味の統合と深いhandlerは比較対象。本案はopcode/keyを受け取るselector型のhandlerではなく、同一支持集合を持つ入力表現とproducerを同時生成することを差分候補とする。LOKI全体より強いとは未主張。
- Andrej Spielmann, Viktor Kuncak, [Synthesis for Unbounded Bit-vector Arithmetic](https://lara.epfl.ch/~kuncak/papers/SpielmannKuncak12SynthesisUnboundedBitvectorArithmetic.pdf), IJCAR 2012, DOI 10.1007/978-3-642-31365-3_39。作者PDFの検索取得要旨を確認。算術とbit演算からtransducer/circuitを合成する基盤は既知。本案のbit逐次計算自体に新規性はない。
- Xin Xie, Fenlin Liu, Bin Lu, *A Data Obfuscation Based on State Transition Graph of Mealy Automata*, 2014, DOI 10.1007/978-3-319-09333-8_58。書誌と要旨の二次索引のみ確認。定数・文字列のMealy難読化が近接するため、本文取得前に本案との差を確定しない。

## 次の実験で判定すること

1. 意味保存：bit遷移からの帰納条件と、実.wasmの境界・ランダム入力比較。
2. アブレーション：通常の式、Fを一度計算する再基底化、融合transducer、最小化なし。単なる状態番号置換を別方式にしない。
3. 適応的攻撃：遷移表の読み出しは成功すると仮定。表から元のwordレベル演算DAGを復元する合成器を作り、入力・出力oracleだけの場合と比較。表が読めたことと元のword構造が戻ったことを区別する。
4. 通常の最適化後の表・式の残存、実行時間・サイズ・メモリ費用を測る。最適化器の未対応を耐性と呼ばない。

最大のReject理由は、既知のbit-serial演算virtualizationにすぎず、局所的な支持集合の一致が呼出し元を読む攻撃には無意味なこと。この反証を避けず、実際のinverse compilationで確かめる。現段階では構成規則を定義したところで、研究目標はactive。
