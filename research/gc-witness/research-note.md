# Wasm GCの構築可能性を区別するテスト入力生成：限定実験

2026-10-27追補: 本ノート本文は初期実験の記録。[追加の強い対照](smith-results.md)では、既存生成器の最小修正でnonnull自己参照arrayの構築成功が0/64から24/64になった。2,022呼出しの追加入力探索で新たにアクセスへ届いたのは1生成物で、深さ1で足りた。Rの独立した主アルゴリズムとしての採用根拠は得られていない。

## Abstract

合法なGC型の全てが、外部から参照を供給せずに構築できるわけではない。本ノートではfinalなGC型を対象とし、空arrayとfunction参照を構築の起点にする限定生成器を検査した。86型構成から965の実Wasmを出力し、3エンジンで2,895実行が成功した。memo化DFSとの325出力はbyte一致しており、新しい一般アルゴリズムの優位性は得られていない。既存fuzzerの型filterと実行成功の間の差を、追加研究の仮説として残す。

## Introduction

Wasmエンジンの検証では、binaryが型検査を通ることに加え、狙った命令まで到達する入力が必要になる。非null参照をnull castで代用すると、検査は通っても対象処理より前にtrapする。型をnullableへ変更して生成を容易にする方法も、元の型を受け取る固定moduleの入力生成にはそのまま使えない。

## Related Work

[先行技術の確認範囲](prior-art.md)を参照。Horn伝播、型の空性、DAG共有は既知。Binaryenは既に構築不能cycleのfilterと型修復を持つ。2026年10月のPR #9282もこの領域の既存修正である。wasm-smithにもGC constructor生成がある。本ノートはこれらの先行性を否定しない。

## Motivation

`(array (ref $self))`は長さ0なら作れ、その空arrayを要素にして長さ1の同型arrayも作れる。非nullのelementを要求するからといって、非null structの必須fieldと同じ依存にする必要はない。さらに「型の値が存在する」と「指定したarray.getが成功する」も別の要求である。

## Threat Model

これはWasmのテスト生成を改善する防御研究であり、秘密や悪意あるコードを隠す方式ではない。対象はローカルの検証器・コンパイラ・runtime。テストmoduleは元の型を保持する。標準Wasmの型安全性を前提とし、hostが任意のGC heapを偽造する状況やエンジンの既知欠陥を利用する状況は扱わない。

## Proposed Method

具体型の構築可能性を、structの必須fieldだけを依存とする有限固定点で求める。arrayは空配列、functionはtrap stubへの参照を起点にする。対象pathをたどれるように必要なarrayだけ長さ1にし、各`(type,path)`の構築証拠をlocalで共有する。構成規則・範囲・限定した正当性の説明は[algorithm.md](algorithm.md)に記す。

## Implementation

Rust/wasmparserで実binaryを検証・解析し、Pythonで証拠を構築してWATを出力する。wasmtime.wat2wasmで組み立てる。比較用のmemo化DFSとtree展開、独立した小型状態探索も実装した。さらにwasm-encoderによるcounter挿入を作り、対象constructorとアクセスが成功した後だけ数える。

## Evaluation

[保存済み実測](results.md)。384 taskに対しtree315、memo325、worklist325が成功。全方式で59 taskは構築不能または要求不能、treeだけ10 taskが予算超過だった。77小型構成の状態探索は判定と一致した。実Binaryen生成器の128出力はすべて検証できたが、observe(null)を1回呼ぶ条件では、nonnull自己参照arrayの成功constructorは32 seed中0だった。対照の型にも到達しない例が多く、これを生成器全体の到達不能性とは主張しない。

Python生成費用のprocess中央値の中央値はtree0.196ms、memo0.0372ms、worklist0.0382ms。worklistの優位性はない。965出力の再生成、325対の同一性、manifestと集計値を監査した。

## Discussion

今回の実装には、型修復をせずに値を構築し、path要求を満たせるという機能がある。しかし、それを可能にする固定点と共有は既知であり、強いmemo対照が同じ結果を返す。研究として残るのは、既存生成器の対象型選択と入力構築を分けることで、現実のテストで未実行のGC操作をどれだけ増やせるかという問いである。

## Limitations

継承・nonnull abstract参照・descriptor等は未対応。生成するalias配置は偏っている。実GCアプリの型を使った評価、既存fuzzerへの統合、coverageの比較、既知bug回帰試験、機械証明は未実施。任意moduleの意味保存変換、エンジンの新規脆弱性発見、難読化の解析耐性を示したものではない。

## Conclusion

限定した値生成の実装と再現可能な実測は得た。既存型を変えない生成への応用仮説は残るが、新しい一般アルゴリズムや修士主テーマとしての十分性は未確立。空array候補を追加した簡単な既存方式との比較を、次の採否条件とする。
