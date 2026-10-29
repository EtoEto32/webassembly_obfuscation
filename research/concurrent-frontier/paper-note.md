# Wasm並行演算グラフの逐次回復：否定的実験の追補

## Abstract

共有memoryとatomic命令を用い、純粋i32関数を実行可能な演算から処理するDAG実行器へ変換した。通常Wasm、同じDAGを用いる逐次VM、1/2/4workerを比較した。主101,376呼出しで値の不一致はなかった。しかし24の主VM条件すべてを依存順の展開で通常Wasmへ回復でき、atomic版の回復時間は逐次VM比約0.94〜1.08であった。実行時間の増加に対応する追加保護効果を確認できず、主提案として不採用とした。

## Introduction

難読化の目標は有用な解析タスクの費用を増やすことであり、解除不能性ではない。複数threadの実行順の数だけでは、その費用を説明できない。本追補はこの点をWasmで検査する。

## Related Work

Omarら2013のthread分割、Dunaev・Lengyel 2013のPetri net管理、US11403372B2の制御データ化が近い。[書誌・本文確認範囲](prior-art.md)を参照。本実験はこれらの一般的な方式を破ったという主張ではなく、自作の限定DAG方式の検査である。

## Motivation

WasmのSC atomicと共有memoryは、演算の取得と結果公開を明示できる。これは実装の意味保存に役立つ一方、解析者が読む依存の仕様も明らかにする。

## Threat Model

解析者は変換方式を知り、binary、host、memoryを観測・改変できる。課題は同じ入出力を持つ簡潔なWasmの回復。変換seedやスケジュールが秘密という仮定は置かない。

## Proposed Method

SSA演算をレコードへ変換し、全依存のREADYを確認したworkerがCASで取得する。結果値を保存してからREADYを公開する。出力は全worker完了後に読む。[疑似コードと条件](algorithm.md)に示した。

## Implementation

Python、WABT、Binaryenで実Wasmを変換し、Node worker_threadsで実行した。範囲は全域純粋i32単一関数、1〜16引数、1024node以下。共有1pageとhost adapterを要する。mem副作用・trap・I/O・元loopは非対応。

## Evaluation

主36target、回復24、追加31targetを検査。主101,376、追加72,912、WABT240呼出しで不一致0。2workerで6,617/9,216入力、4workerで5,604/9,216入力に複数担当者を記録した。性能108 fresh process、各7標本の詳細を[分析](analysis.md)とraw JSONへ保存。方式既知の回復はO(V+E)の順序付けで足りた。

## Discussion

同じ依存グラフを共有する逐次対照と比べ、atomic版の解析時間はほぼ同程度だった。実行はlocal同士でも約1.25〜2.07倍遅く、host連絡を含む複数workerの時間はさらに増えた。一般の重い並列計算への性能評価ではない。新規性の弱さと増分効果の不足を併せて不採用と判断する。

## Limitations

小さな人工kernel、一つのCPU、二engineのうち並行実行はV8のみ。回復器は4種類の公開VM profileに限定される。全入力・全scheduleの生成Wasm同値証明、人間の解析時間、現実アプリの保護、先行ツールと同costの直接比較は未完了。先行特許の法的範囲を判断していない。

## Conclusion

この限定方式では、正しい依存管理が同時に安い逐次回復手順を与えた。単にworker数や配置を増やす方向は続けない。これは失敗の機構を示した追補であり、新しい有効な主発明や特許性を確立した成果ではない。
