# 近い先行技術と新規性の判断

2026-10-22。実際に確認した範囲を区別する。本文の未読部分、検索に現れなかった文献、特許family全体の先行性を確認済みとはしない。

|資料|書誌と実読範囲|今回との関係・限界|
|---|---|---|
|[An Obfuscation Scheme Using Affine Transformation and Its Implementation](https://www.jstage.jst.go.jp/article/ipsjdc/2/0/2_0_498/_article/-char/en)|Kazuhide Fukushima, Shinsaku Kiyomoto, Toshiaki Tanaka、2006、査読誌IPSJ Digital Courier 2:498–512、DOI 10.2197/ipsjdc.2.498。今回発行元PDFへアクセスでき、§4.1、§5.1のdynamic attack、§6のfunctionality/efficiencyの該当部分を読んだ。|複数変数のaffine混合は既知。実験は一部入力でoverflowに伴う結果差を記録し、費用は主に生成命令数を比較する。今回のdet=1の剰余演算は全word値で恒等式を保つが、それだけで新発明とはならない。著者の全方式を再実装・解除した実験ではない。|
|[Obfuscation of Abstract Data-Types](https://www.cs.ox.ac.uk/files/2892/thesis.pdf)|Stephen Drape、Oxford博士論文、2004。学位論文で、査読誌論文ではない。今回Abstract、§3.2 pp.49–51、§8.1.4 pp.136–137を実読。|データrefinement、可逆変換の共役による演算導出、異なる表現の使用を既に扱う。今回の変換は拡張状態(v,M)へ同じ共役の見方を適用できる。実行ごとに表現が違うだけでは独立した差にならない。本文全体の精読ではない。|
|[Control Flow Obfuscation for FJ using Continuation Passing](https://arxiv.org/abs/2012.06340)|Kenny Zhuo Ming Lu、2020/2021、arXiv:2012.06340v2。今回は書誌とAbstractを確認、過去の本文調査は[continuation-routing](../continuation-routing/README.md)を参照。拡張プレプリントとPEPM短報を区別する。|CPSと固定長call-string解析への影響は既知。今回は関数要約を攻撃に用い、呼出し文脈の数だけを難しさとしなかった。今回CPS実装自体を再現したわけではない。|
|[Learning Deterministic Visibly Pushdown Automata Under Accessible Stack](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.MFCS.2022.74)|Jakub Michaliszyn, Jan Otop、MFCS 2022、LIPIcs 241:74:1–16、DOI 10.4230/LIPIcs.MFCS.2022.74。査読会議論文。書誌・Abstractのみ。|stackへ読み書きできるモデルで効率的な学習を扱う。black-box側の困難性を、配布binaryを読める本方式の耐性へ転用できない。証明全体や学習器は今回未実装。|
|[US8286251B2, Obfuscating computer program code](https://patents.google.com/patent/US8286251B2/en)|Johan Eker, Björn Johansson, Carl Von Platen、B2公開2012-10-09、A1公開2010-09-30。書誌、説明のencodingとruntime変更部分、請求項1–5を確認。|関数entry pointの複数語表現、実行中の表現変更を扱う。今回は計算の値を混合し直接callを残す点が異なるが、「呼出しをまたぐ表現変更」一般を初出とは言えない。残りの請求項・審査経過・権利範囲の法的評価は未確認。|

Giacobazziらの *Obfuscation by partial evaluation of distorted interpreters* の著者PDFは今回timeout。検索抽出だけから本文の詳細を補完していない。VPAの最小化困難性や一般の文脈自由文法の性質も、本実験の難読化効果の証明に使用しなかった。

## 判定

具体的な成果は、再帰frameへ行列を渡す実Wasm変換、その意味保存、frame非依存の関数要約による回復、性能比較である。今回のshear選択とWasm loweringが全先行例にないことは示していない。既知の複数変数混合・共役・実行時表現変更から独立した構成上の貢献は弱く、Wasm固有性も弱い。主発明には採用しない。

解析本体の費用増加は実測したため「何の効果もない」とはしない。同じroot行列でそろえたv2では、固定混合比で要約本体は1.59–1.76倍、読取込みの中央値和は約0.4–3.3%増えた。一方、履歴を追う必要が生まれるという中心仮説は支持されない。方式を変えずに再帰深さや係数だけを増やす実験は続けない。特許取得・非侵害・世界初を判断した記録ではない。
