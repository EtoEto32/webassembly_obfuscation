# 先行技術の照合

2026-10-22。以下は一次資料で確認した範囲。全文未読の資料の方式や数値を補完しない。全特許公報の調査完了や法的な特許性の判断は行っていない。

## LLVM StackColoring

LLVM project contributors、`llvm/lib/CodeGen/StackColoring.cpp`、継続開発される一次実装（査読論文ではない）。[公式source](https://github.com/llvm/llvm-project/blob/main/llvm/lib/CodeGen/StackColoring.cpp)。導入、implementation notes、生存区間と分岐の例を読んだ。互いに使われない格納領域を共有し、領域を縮小する。先頭TODOは異なるoffsetへの小領域の統合にも言及する。全passを独立実行・性能測定したものではない。

今回の核である生存区間による共有は既知。Wasm byte addressで異なる型の重なりをtie-breakとして増やす選択は具体的な追加だが、これだけで独立した新原理と評価できない。部分重複そのものも新規性の根拠にできない。自作first-fitをLLVMと同一の実装だと扱わない。

## LLVM MemorySSA

LLVM project contributors、*MemorySSA*、現行技術文書（査読論文ではない）。[公式文書](https://llvm.org/docs/MemorySSA.html)。MemoryDef/Use/Phiの説明、例、clobberとwalker、設計の節を読んだ。書込みの到達関係と分岐の合流を扱う既知の枠組みであり、型矛盾だけでこの解析を排除できない。

今回の回復器は静的byteアドレス向けの限定した実装で、LLVM MemorySSAを実行した結果ではない。比較上重要なのは、追加した表現の回復が既存の到達定義・phiという原理で説明できること。非対応の動的aliasやループにも自動的に成功するとは主張しない。

## Wasm仕様

WebAssembly specification contributors、*WebAssembly 3.0 — Instructions*、2026-10-20表示の現行draft。[memory命令の実行規則](https://webassembly.github.io/spec/core/exec/instructions.html#memory-instructions)。load/storeのbyte列、範囲検査とalignmentの注記を確認した。非atomicなload/storeのalignmentは意味を変えない。privateという属性が読み出しに対する秘密を与えるわけではない。

## 制御フロー解析の候補選別

Soyeon Baek, Sungho Lee、*Deobfuscation of Control Flow Flattening Based on Abstract Interpretation*、2026、IEEE TSE 52(3),1110–1124、査読論文。[出版社の要旨・書誌](https://doi.org/10.1109/TSE.2026.3659437)、[著者研究室の一覧](https://cnu-ants.github.io/publications)。要旨と書誌だけを確認。k-switch文脈感度を用いる静的な平坦化解除を提案するという範囲まで確認し、本文アルゴリズム・成功率は未確認、本体未実行。

この資料と既に確認した[Chisel](../nonlocal-literature-audit.md)から、分岐数や履歴数だけを新規性・解析費用の証拠にしない方針を採った。本案はそのどちらに耐性を示した実験でもない。

## 判定

候補の違いは「同じ場所に同時には存在しない、幅の異なる値を意図的に重ねる配置目的」に限定される。既知の生存区間再利用との距離が小さく、型付き値へ戻す解析も既知原理で実装できた。新しい独立難読化アルゴリズム、既存研究を上回る保護、特許に適した差分のいずれも確立していない。方式名やWasmへの移植を新規性に数えない。
