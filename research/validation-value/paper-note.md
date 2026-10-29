# 論文草稿追補：妥当性検査による条件式計算の限界

## Abstract

Wasmのstack-polymorphic validationを利用して、CNF条件式の真偽を補助モジュールの妥当性に移す構成を試作した。24実行条件53,456呼出しで結果が一致した。一方、全6保護条件を実行oracleなしで通常のBoolean式へ回復し、その等価性をbit-vector solverで確認した。原型の実行時間は元版の約88～136倍となり、保護上の優位は確認できなかった。

## Introduction

公開逆変換を持つデータ表現では、decoderの抽出で保護対象へ戻れる場合があった。本実験では値表現を変える代わりに、公開された型検査器へ計算を担わせる可能性を検討する。

## Related Work

BABELの計算モデル変更が最も近い一般的発想である。Wasmのunreachable typingとJS validate APIは既存仕様であり、それら自体を新規とはしない。[先行資料](prior-art.md)に読了範囲を保存した。型システムと難読化の意味論的比較も、検証器を計算に使う同一の構成と混同しない。

## Motivation

一部の変換は通常のoptimizerが扱わないhost機能へ処理を移せば残存する。しかし、残存と方式既知の解析への耐性は別である。本実験ではvalidatorを未知の外部関数とみなさず、その使用範囲の意味を要約する。

## Threat Model

合法的な条件処理の保護を対象に、方式・変換後binary・host adapterを公開する。解析者は元のCNFや生成時metadataを受け取らず、外部validator不要の等価Wasmを得る課題を解く。検出回避や暗号学的秘密保持は評価しない。

## Proposed Method

各clauseをvoid blockとし、真literalをunreachable、偽literalをnopにして、最後にoperandなしのi32.add/dropを置く。block内のいずれかが真のときだけ型検査が通る。全blockの妥当性がCNFの真となる。生成した補助moduleは実行せず、validate結果のみを元の出力とする。

## Implementation

WABTを用いるPython CLIで実Wasmを変換する。対象は二つのi32からbit literalを取る純粋CNF。生成器は固定1page memoryと同期host importを要する。元ABIを保つ汎用変換とは異なり、外部挙動の契約に専用adapterを含める。

## Evaluation

同じCNF族の3設定、元／validator／専用recognizer／回復版、raw/O3で24条件を実行した。53,456呼出しが一致し、93補助moduleはNodeとWABTのvalidationで一致した。元・回復のWABT逐次実行72件、18binaryの再生成、4拒否対照も確認した。

回復器はblockの型検査をORへ要約し、patch式を代入してCNFを得た。全6条件はZ3で元の式との不一致がunsatとなった。36process/252batchの性能評価ではvalidator版が元の約88～136倍、回復版は約1.018～1.058倍。詳細な生値と再現手順は[README](README.md)に示す。

## Discussion

逆写像のない表現でも、利用する公開サービスの状態が少数の意味状態へ閉じれば簡潔に回復できる。今回の型検査ではclause内にunreachableが現れたかという状態で足りた。外部関数境界を保護根拠にせず、その部分評価に対する増分を調べる必要がある。

## Limitations

有限の生成族の結果であり、実アプリ・汎用Wasm・任意のvalidator入力へ一般化しない。CNFへの一般変換、特許公報の網羅調査、変換器全体の形式検証は未実施。追加資源不足と実時間は同値性の対象外。SMTの結果は抽出した6つのscalar式についてのものである。

## Conclusion

Wasmの妥当性へBoolean出力を移す具体的構成と、その解除を実装した。独立した新規性と有用な追加保護効果は未確立であり、主発明には採用しない。
