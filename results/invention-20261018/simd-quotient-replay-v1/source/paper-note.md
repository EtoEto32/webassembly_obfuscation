# SIMD非正規マスクによる条件式変換の評価

## Abstract

比較結果を偽0・真正数で表すWasm変換を実装した。融合で正規化の費用を削減できるが、同じ二値射影で条件式が自動回復される。独立した新規性と実用的保護の優位性は未確立である。

## Introduction

Boolean値を固定maskから広い値域へ移すと解析に何が残るかを検査する。解除不能性ではなく、追加の解析費用と実行負荷を評価する。

## Related Work

RamanほかHSCC2015のquantitative STLにmin/maxと符号によるBoolean意味の既知例がある。unsigned飽和差は標準SIMD命令。型統一方向にはUS8645930B2とWASMixerの間接呼出しが近接した。書誌・読了範囲は[README](README.md)と[特許追補](../patent/signature-and-simd.md)に記録する。

## Motivation

既存の0/255 maskを途中で作らず、比較と論理結合を数値演算として連続評価する。異なる値を通すことがBoolean構造の回復へ影響するかを問う。

## Threat Model

方式とバイナリが公開された解析者が比較とBoolean結合を回復する。元ソース・生成reportは与えない。小さな純粋SIMD関数に限定する。

## Proposed Method

E(a>b)=sat_sub(a,b)、E(AND)=min、E(OR)=max、E(NOT)=sat_sub(1,E)。出力前にgt_u(E,0)を適用する。Q(x)=[x>0]との交換則により意味保存を説明できる。

## Implementation

Python/WABTで実.wasmを読み書きし、Binaryen O2/O3で最適化した。Qを使う回復器と、適用条件を外れた簡約を防ぐ検査も実装した。

## Evaluation

3kernel×3表現×3最適化の27本と回復27本、3,649,536呼出しで不一致0。WABT108呼出しとbyte代数590,080比較も一致した。27条件すべて元と同じ正規化条件式を回復。81 fresh processの測定で融合は各gate正規化より軽いが、解析も約0.1–0.2msで済んだ。[生データ](../../results/invention-20261018/simd-quotient-v2/)。

## Discussion

値域が広くても各値を二値へ独立に射影できれば、値の多様性を解析者へ強制できない。融合は実行費用を下げる一方、解析側の式も小さくした。

## Limitations

人工kernel、単一CPU、限定されたSIMD命令を対象とする。全256bit入力を列挙した実装証明ではない。人間の理解時間、製品規模、他研究の実装との総合比較、特許性の判断は未実施。

## Conclusion

動作する具体的変換と比較結果は得たが、主難読化方式には不採用。独立した各値の簡単な射影で元演算へ戻せるかを、後続案の設計時に検査する。
