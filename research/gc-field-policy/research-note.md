# Wasm GCのフィールド権限検査：構成・実用条件・強い対照による反証

2026-10-26、日本語研究ノート。主テーマとして新規性を確立した論文ではない。既存のpaper/main.texは変更しない。

## Abstract

WebAssembly GCの構造的型に基づき、第三者moduleのaggregate生成・読出し・書込みを受理時に制限する試作を作成した。module間の型同値性と明示的subtypingを閉じることで、単なる型番号比較や完全一致では防げない直接操作を拒否した。一方、ownerの異なる同型objectを区別できず、安全なconsumerも拒否した。部分公開データの人工処理を2engine・360processで比較したところ、通常のデータ分離・増分public viewと同程度の実行時間だった。PCC、JVMアクセス制御、RichWasm等との原理的重なりが強く、新規な主アルゴリズムとの主張は現時点で見送る。

## Introduction / Motivation

GC参照を共有すると、受け取ったmoduleは同じ構造型やsupertypeを宣言してフィールドにアクセスできる。公開fieldを直接読む性能を維持しつつ、非公開fieldや生成権限を制限したい。private types提案は既にこの問題を指摘しており、課題の初出は主張しない。本試作はengineの型体系を拡張せず、受理するmoduleを制限する構成である。

## Related Work

[prior-art.md](prior-art.md)に書誌・読んだ範囲・重なりを記す。PCCの受理前検査とdata access policy、JVMのfieldアクセス制御、RichWasmの静的capabilityは強い先行である。Canonical ABI GC提案は型表現とcopy費用を既に議論している。これらの精密な保証をOが包含するとはしない。

## Threat Model

信頼するloaderが全untrusted Core Wasmを検査し、同じbyte列だけをinstantiateする。hostと公開APIの意味は信頼する。direct GC read/write/createが対象であり、type/identity/length/timing/resourcesは秘密にしない。未検査moduleへの参照流出、trusted serializerからの情報公開、host権限の誤設定はGC policyだけでは防がない。実験ではimport allowlistを別に設けた。

## Proposed Method

libraryの正確なpost-optimization binaryと型/field policyを入力とする。wasmparserの同じcanonical type contextでconsumerを検証する。対象Tのread/write禁止はoperand型UについてU <: TまたはT <: Uのとき適用し、create禁止はU <: Tのときに適用する。array.copyはsource read/destination writeの2義務とする。const expressionも走査する。詳細は[plan](plan.md)と[soundness-obligations](soundness-obligations.md)。機械検証済みの健全性証明ではない。

## Implementation

Rust、wasmparser/wasm-encoder 0.227.1、serde_json。Node loaderへbyte snapshotとpolicyをstdinで渡し、受理した同じbytesを実行する。feature setを固定し未対応proposalは拒否する。Node24.15/V813.6、Wasmtime Python50.0.1、Binaryen133で試験した。変換器ではなく検査器であり、binary書換え時間を測ったとはしない。

## Evaluation

主probeは18consumer×2library値で36組/engine。closureは今回の禁止操作24条件を全拒否し、安全な12条件のうち2条件も拒否した。追加9組でrecursive group・packed field・array操作と同型owner衝突を検査した。

部分公開処理は3行数、2順序、2pass数、5表現、2engine、3process、12warmup/11測定。全返値が独立Python計算と一致した。65536行1passでsharedはNode0.0565ms、Wasmtime0.4828ms。既知の増分viewは0.0567/0.4903ms、最初からpublic/privateを分ける方式は0.0529/0.4788msだった。小差は統計的優位と扱わない。全件copyに対する大きな速度差だけを強調すると、対照が弱いという結論になる。

別の45組/engineでprivate値を3種類に変え、公開返値と全private値を照合した。private-atをimportする変種はGC検査単体を通るが、import allowlistで拒否された。さらに既存linker/O3によるアクセサの高速化も24processで測った。実験入力は人工であり、自然なアプリ導入の証拠ではない。生値・実行コマンド・source snapshot・hashはresultsへ保存した。

## Discussion / Limitations

最も強い利点候補は、既存layoutを維持してpublic viewを追加保持しなくてよいこと。ただし、増分viewも既存layoutを保てるため、追加memoryと更新追跡の条件に限られる。型だけのpolicyでは所有元を識別できない。自然なcompilerでの適用精度、policy生成、全命令の形式的カバレッジ、複数module合成証明は未達である。

custom descriptorでownerを識別する別方向も調べた。正規値から得たdescriptorを用いたpayload再生成をBinaryen interpreterが受理し、descriptor identityだけでは真正性を保証できないと分かった。Nodeはencoding未対応で別扱い。非公開exception tagによる封印は直接の先行技術があるため、新原理に数えない。

## Conclusion

限定した受理検査は動作したが、新しい主アルゴリズムとしての新規性と代替方式に対する明確な優位は確立していない。主題化を保留する理由を再現可能な形で示した。今後は自然な必要例と新しい合成保証が得られる場合にのみ、この枝を再評価する。
