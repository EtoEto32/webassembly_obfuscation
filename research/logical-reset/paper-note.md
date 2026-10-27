# 論理容量とセグメント寿命の連動による閉じたWebAssemblyの再初期化

追補：[最近接Weaveとpooling対照](strict-review.md)により、主要機構の新規性が弱いと判断し主方式への採用を見送った。本稿は試作時点の研究ノートとして保持する。

2026-10-24。研究ノート。論文としての新規性・採択可能性は未確定。

## Abstract

同じWasm instanceをリクエスト間で再利用する際、memory内容のみの復元では、容量成長とsegment破棄に由来する差を除けない。本試作は論理容量とsegment有効長を導入し、対象命令の仲介と初期像の再適用をbinary変換で構成する。限定した4構造例のNode 25,704比較とWasmtime 8,148比較は一致した。不完全方式の反例も保存した。Node fresh生成より速い条件がある一方、第三者コーパスの非空219本は現状のinterface制約で対象外だった。新規性と実用性は未確立である。

## Introduction

対象は、同一の閉じたguestを停止境界で初期状態へ戻す処理である。問題設定自体には先行提案がある。目的は標準engine上で正しい再利用ができる狭い変換を作り、必要な状態とコストを検証することに置く。

## Related Work

reset提案、pooling、Wizer、enclave再利用、bytecode checkpoint/restore、公開特許を[先行資料](prior-art.md)にまとめた。snapshot・命令挿入・仮想化という一般原理の新規性は主張しない。請求項レベルの差分は[新規性分析](novelty-analysis.md)で未解決事項として扱う。

## Motivation

成長したmemory/tableはguest命令で縮小できず、dropしたsegmentは単純なmemory copyでは復元されない。次のリクエストのsize・境界trap・initの結果がfreshと変わる。この観測差を解消するには内容以外の状態の扱いが必要になる。

## Threat Model

trusted hostが変換済みの閉じたmoduleを実行し、guest停止後にresetする。guestの数値APIからの前epoch状態の観測を対象とする。shared state、外部resource、非停止の強制中断、host攻撃、時間非干渉、物理消去は含めない。

## Proposed Method

物理容量より小さい論理容量をprivate globalで管理し、全対象accessを範囲検査する。dropは有効長0への変更にし、active初期像は専用passive shadowへ保持する。再成長時には露出領域を必ず初期化する。詳細な疑似コードと状態関係は[algorithm.md](algorithm.md)に示す。

## Implementation

Python、WABTのfolded AST、標準Wasm命令で構成する。最大256ページ・4096table要素、数値signature、constant global initializer等の制約がある。受理範囲と全入力意味保存の機械証明は同じではない。

## Evaluation

raw/O3と2engineの差分、3アブレーション、9拒否例、5processの性能、静的な第三者コーパス検査を実施した。[全実測](results.md)を参照。0長操作、重複copy、副作用後trapを含む。declarative segmentのO3 parse拒否は成功に含めなかった。65,536byteの仕事ではfull/freshの時間比中央値0.551–0.646。これはfresh生成に対する局所的な効果である。

## Discussion

論理容量・範囲検査・segment寿命の連動の必要性は反例で説明できる。しかし、この連動が既知virtualizationの通常適用を超えるかは未解決である。単純なmemory復元対照の失敗を、正しいruntime resetに対する優位へ読み替えない。

## Limitations

同一fixture系列、1CPU、数値APIのみ、real application未検証、pooling未比較、物理memoryを保持する費用、追加helperの資源消費がある。コーパス全件が範囲外となった事実は適用性の弱点である。全入力証明、特許familyの網羅比較、最近接実装の該当code比較は未完了。

## Conclusion

閉じたWasmの論理状態復元を行う実装と、必要要素の反例・費用を保存した。新発明の成立とは判定しない。次の判断には、第三者用途と強い既存対照、および具体的な先行構成との比較が必要である。
