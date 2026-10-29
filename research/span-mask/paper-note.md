# 入力依存の線形包表現によるWasm変換の実験記録

2026-10-23。否定結果を含む日本語草稿。発表・出願していない。

## Abstract

Boolean計算を入力依存行列の線形包判定へ置換するWasm生成器を試作した。元式を配布せず同値計算を行えるが、3人工例の全条件を公開入出力から復元できた。固定混合に対して実行時間は約3.8～11.4倍で、新規性と費用対効果から主発明への採用を見送った。

## Introduction

目標は合法的なソフトウェアの知的財産保護であり、解析不可能性ではない。既存の単純な表現変換が固定decoderや局所要約で回復される問題に対して、入力ごとに異なる線形包の表現を検討した。

## Related Work

Karchmer–Wigdersonのspan programとEP2831791B1の入力依存行列生成が近い。[先行技術表](prior-art.md)に実際の閲読範囲を記録した。WASMixer、NotDec、LOKI等の実行を今回の結果に含めない。

## Motivation

入力依存混合は定数の行消去だけでは全て消えない。この限定した分析課題への負担増分が、追加実行費用に見合うかを調べる。

## Threat Model

方式・バイナリ・実行環境を利用できる解析者が、同等の短いBooleanコードを回復する。秘密鍵や外部サービスを仮定しない。生成manifestは攻撃入力から除く。

## Proposed Method

式をspan programへ変換し、可逆な入力依存row/column shearを係数多項式へ展開する。32bit並列のmasked Gaussian eliminationで実行する。[アルゴリズム](algorithm.md)に手順と条件を記録した。

## Implementation

Python生成器、WABT、Binaryen、Nodeを使用する。入力は純粋なAND/OR/XOR式に限定し、private memoryを追加する。標準Wasm binaryを読み書きするCLIがある。

## Evaluation

主検証158,558呼出し、追加Node45,056、scratch6,144、WABT164、独立GF(2)モデル1,152入力で不一致0。直接・係数前処理BDDは36条件中26復元、10node上限だった。逆shear前処理ではO3の6条件中5復元、残りはnode上限。全数入出力学習はO3の12条件全て回復した。測定方法・生値・ばらつきは[自動集計](../../results/invention-20261023/span-mask-report-v1/report.md)とリンク先JSONに保存する。

## Discussion

一つのBDD解析を止めることと、適応解析への保護効果は違う。小さい入力空間と32lane ABIにより全数学習が可能だった。入力依存化は解析だけでなく実行も重くし、改善の費用対効果を示せなかった。

## Limitations

3人工式・単一seed・単一性能engineである。一般のアプリ、全入力の実装証明、同費用に調整した既存難読化器との比較、特許請求項の全調査は行えていない。資源不足時のinstantiation差もある。

## Conclusion

動作する構成と再現可能な否定結果は得たが、独立した新発明と呼べる根拠は得ていない。単に入力数や混合回数を増やす改変を次の発明として数えず、別の研究課題へ移る。
