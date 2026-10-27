# WebAssembly共有メモリの待機集合を用いた実体関係検査

## Abstract

共有Wasm memoryのcloneでは、JSオブジェクトが異なってもbyte実体を共有する。通常の同一性検査を非alias保証に用いると誤る。本稿は、共有queueへの非同期待機と通知で実体分割を生成する限定試作を評価する。290条件で正しく分割し内容不変を確認したが、同期offsetの排他が必須であり、既存標準からの進歩性は未確立である。

## Introduction

複数memoryを受け取る境界の安全性は、import indexだけでなく実体の共有関係に依存する。cloneは参照比較と共有関係を分離する。本研究は、来歴IDが得られないhost内で受取済みのmemoryを検査する。

## Related Work

共有Data Block、waiter queue、shared WebAssembly.Memoryは既存標準にある。一般alias解析とは異なり、静的に任意プログラムを解析せずruntimeの同一queueを観測する。[読了範囲と特許候補](novelty-analysis.md)を示す。

## Motivation

二つのmemory importが別JSオブジェクトでも、一方のstoreを他方のloadが観測する場合がある。===を使う自作guardの失敗を局所的に再現した。信頼できるregistryはこれを正しく解決でき、本案はその代替が必要な限定環境に向ける。

## Threat Model

hostと組込みJS操作を信頼する。対象offsetの待機・通知・書込みは検査中に外部から行われない。識別の対象は受取済みラッパーであり、敵対的workerの活動を検査器が止めるわけではない。queue干渉と時間は観測可能。

## Proposed Method

各対象から1waiterを登録し、未分類代表のnotify-allによる完了集合を集める。件数照合を終えてから次へ進む。n登録とk通知で全分割を得る。判定後は捕捉した同じmemory配列へ結合する。[条件付き論証](algorithm.md)。

## Implementation

JavaScript hostライブラリと実2memory Wasmを使う。builtin getterでbufferを取得し、通常propertyのshadowと入力listの変更を避ける。最大256対象。sharedでない場合や検査cellが存在しない場合は拒否する。

## Evaluation

290分割・904内容hash、境界11条件を確認。15processで、64独立memoryの中央値はbatch0.2119ms、代表pairwise13.7237ms、registry0.0026msだった。[原データと条件](results.md)。全入力・全runtimeについての証明ではない。

並行writerへの追補では、同期操作を持たない限定guestを実binaryから検査した。更新cellで登録再試行1/64と、書込み範囲外のcellを選ぶ方式を比較した。各900回で成功数は26/87/900、成功分割の誤り0、残りは判定不能だった。未書込み位置方式の895回で、判定中の別cellの更新を観測した。追加43binaryの範囲監査も一致した。

Node/V8とSpiderMonkey150.0.1で共通290条件、実Wasm4条件、grow・shadow・拒否対照の結果が一致した。各engineで904実体の全byteを比較した。SpiderMonkey shellではtimer adapterが必要で、成功経路のみの比較である。

## Discussion

同一agentのreaction順と通知件数を使う追加版では、一回の完了待合せで分割を復元した。両engineの共通試験を通過し、n=k=64で単一timer・群別await版0.161705msに対し0.054230msとなった。k=1では遅く、正しいregistryにも劣る。順序前提を人工的に破る4要素模型では代表所属検査を通る誤分割が存在した。既知順序保証の利用以上の進歩性は未確認である。

メモリ内容は変更しないがqueueは変更する。外国waiterも起こす例から、非侵襲な一般検査という主張を否定する。wrapper共有の誤認を防げることと、新しい同期原理を作ったことは別である。

排他を破った追加5試行では、別memoryの通知を混ぜて件数が整合したまま誤結合する反例を得た。これは非alias guardの余分な拒否に相当する。件数照合で外部干渉を必ず検出するという強い主張は否定される。

## Limitations

自作microbenchmark、同期queueの排他、有限対象、trusted intrinsicsに依存する。成功経路は2engineで比較したが、実アプリへの適用率、browser配置、全family調査は未実施。既存のqueue semanticsを利用したbatch化以上の新規性は確認できない。

並行版は対象byte全体の静止を要求しないが、外部の待機・通知の排除をhost管理へ依存する。局所checkerだけでは全actorの不存在を証明できない。一般のdynamic-address writerでは未書込み位置を得られない。通常の範囲解析を使った前提の具体化であり、特許の独立した新原理が確認されたわけではない。

## Conclusion

実体関係をbyte書込みなしに同定する限定候補を実装し、正の結果と境界の失敗を保存した。特許性の断定を避け、既存機構からの差をさらに反証する必要がある。
