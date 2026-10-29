# 論文追補：単一アトミック更新に閉じる符号化の制約

## Abstract / Introduction

共有メモリの表現変換では、逐次計算に使える復号・更新・再符号化をそのまま分割するとatomicityを失う。Wasmの一命令更新を保つcodec選択を試作し、正当性・性能・回復可能性を比較した。独立した新難読化の確立には至らなかったが、選択可能な表現と追加状態・再試行の必要性を区別する制限を得た。

## Related Work / Motivation

データ表現の共役、演算集合によるcodec選択、CAS loopによる一般更新には先行構成がある。[読んだ一次資料と具体的差分](prior-art.md)。本案の検証課題は、その構成をWasm atomicへ適用して正当性・低費用・保護効果を同時に得られるかである。

## Threat Model / Proposed Method

方式既知、配布binaryと物理memoryを観測可能な解析者を対象とする。秘密鍵を仮定しない。32bit共有セルの操作集合からaffineまたはNOTを選び、各操作を一つの対応atomicへ写す。全加算と全ANDをそれぞれ固定したnative opcodeへ写せる全単射は恒等とNOTだけになることを導出した。[量化・証明・非適用範囲](algorithm.md)。

## Implementation / Evaluation

実.wasmを入力するPythonパスを作り、raw/O3の18正条件で16,470呼出し、追加10条件で4,000呼出しを検査した。実workerの328,448正更新、WABT162probeも契約に整合した。分割RMWの負例には失われる更新があった。単一counterの競合なし測定では、同じcodecのCAS対照からNOTで約5.76%、affineで約14.16%短縮した。14の符号化条件は2回の選択storeでmemory表現を回復できた。

## Discussion / Limitations / Conclusion

単一native命令へ閉じる制約は、ここでの表現の自由度を強く減らす。CASの削減を保護向上と取り違えられない。混合幅、成長、公開生memory、wait/notify、他codec、競合時性能、一般アプリ、逆コンパイラの型回復は未評価である。正当性は設計上の局所対応と有限試験に基づき、コンパイラ全体の機械証明ではない。原子的表現変換の部品・失敗知見として保持し、新規で有効な主方式には採用しない。
