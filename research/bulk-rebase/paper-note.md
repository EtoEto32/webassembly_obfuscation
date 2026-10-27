# 論文草稿への追補：位置表現とbulk copyの費用

## Abstract
位置依存のbyte表現を保つWasm変換に対し、memory.copy後の移動先補正を実装した。44条件の差分検証は一致したが、直接SIMDによる補正copyと比べ速度の優位は得られなかった。コードサイズの削減と、意味保存に必要なtrap・重複契約を確認した。

## Introduction / Related Work / Motivation
位置依存maskは既知であり、移動先の位置が変わるコピーには表現の修復が必要になる。Data Randomizationのwrapper、位置依存配列難読化、位置依存暗号メモリの再複製を近接構成として比較した。書誌と読解範囲はprior-art.mdに記録する。Wasmのcopy契約で方向判定と事前検査を代替できるかを調べる。

## Threat Model / Proposed Method
解析者は配布binaryを知り計測できる。private・非共有memoryの逐次プログラムを対象に、E_a(v)=P(v) XOR K(a)を使う。copy直後の移動先へK(s+i) XOR K(d+i)を適用する。元の位置の値を読み直さないため重複を扱え、成功済みのcopy範囲内で補正するため新たなbounds trapを起こさない。

## Implementation / Evaluation
PythonとWABTによるbyteアクセス変換CLI、scalar/SIMD版、直接copy等の対照を実装した。44本・34,144呼出し・全memory照合で不一致0。WABT別実行器120呼出し、小モデル112,130件、4負例も保存した。31選択書込みで全44条件の同等decoderが回復した。270 fresh processの9比較で速度改善はなく、後補正/直接SIMD比は1.000–1.752だった。一方O3サイズは1,509から1,155 bytesへ減った。

## Discussion / Limitations / Conclusion
境界契約を標準命令へ委ねる構成は小さいコードを生成したが、2走査の負担を相殺する速度効果は得られなかった。Pの相殺は直接版にも可能で、提案だけの利益にはならない。限定fixture・単一hostであり、一般の逆コンパイル抵抗や特許性を確立した結果ではない。主発明への採用は見送り、意味保存と費用の比較を研究資産として保持する。
