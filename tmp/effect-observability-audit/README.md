# 外部から観測できる書き込みと保護対象の監査

2026-10-12。新規アルゴリズムの完成報告ではない。次候補の保護対象を誤らないための反証実験。

## 実測結果

既存trap-prefix-fusionのprefix-divとgenerated-0..7、通常版/変換版、raw/O2の36バイナリを使用。各64入力、計2,304実行で、最初のstore値を内部計測なしで読み取れた。不一致0。

観測者は別Nodeプロセスでバイナリ、公開入力、初期memoryだけを受け取る。runにa=b=0,d=0を渡し、divide-by-zero trapを捕捉後、exportされたmemoryのword0を読む。原IRや乗算係数は観測者に渡さず、検証器だけがBigIntで計算する。14境界値とseed 0x70ba3921の50入力を使用。生データ・バイナリ複製・SHA-256はartifactsに保存。

意味保存の対象にtrap後memoryを含める限り、同じ入力でこの値を返す必要がある。従って、内部ログを式へ置き換えても、この観測点の値の秘匿は達成できない。一方、全store列、元の式、順序、秘密情報を復元したとは主張しない。この9プログラム以外に自動適用できる観測者でもない。新たなlog-free変換自体を実装・測定したものではない。

## 次候補の比較判断

| 案 | 具体的な規則 | 近い既存内容 | 現時点の判断 |
|---|---|---|---|
| 書き込みログを式へ置換 | byteごとの読み出しを後続storeとのアドレス一致条件でselectし、first-fault以前の最後の書き込みだけcommit | SMT配列のread-over-write、MemorySSA、例外を考慮するDSE | これだけでは新規則なし。観測可能なprefix値の保護にもならず、単なるhelper除去としては採用しない |
| CPSをtyped continuationへ移植 | 元blockを継続として渡し、resume/suspendで遷移 | CPS難読化、WasmFX | 単なる移植は採用しない。新しい解析上の効果は未提示 |
| 継続の利用履歴に依存する変換 | 継続の動的な消費状態を制御と関連付ける案 | WasmFXのone-shot制約、CPS解析 | 未設計。二重resumeはtrapするため、単に複数経路で同じ継続を使うと意味を壊す。型だけで使用回数が証明されるとの仮定も誤り。実装前に具体的な規則と比較対象が必要 |

ここで棄却したのは列挙した単純規則。メモリや継続を用いる新方式すべてを否定していない。過去の汎用枠組みへの包含だけで全候補を棄却しない。

## 根拠資料

SMT-LIB ArraysEx、作成2010-04-28、release2.7/2024-07-21。定義の2つのread-over-write公理を確認。同じアドレスを読む場合は書込値、異なるアドレスなら旧配列の値、という場合分けは既存。Wasmの有限メモリ・trap規則はこの理論には含まれない。
https://smt-lib.org/theories-ArraysEx.shtml

LLVM公式MemorySSAとDeadStoreElimination.cpp、2026-10-12閲覧、live文書でcommit未固定。DSEソース1115–1127および1153–1157付近のmayThrowBetween/isDSEBarrier/unwind可視性の注記を確認。例外時の可視性は既存最適化でも扱われる。ただしLLVM例外とWasm trapは同一ではなく、今回案と完全同一の実装だとは言わない。コードの実行・性能比較なし。
https://www.llvm.org/docs/MemorySSA.html
https://www.llvm.org/doxygen/DeadStoreElimination_8cpp_source.html

Kenny Zhuo Ming Lu, Control Flow Obfuscation for FJ using Continuation Passing、arXiv:2012.06340、2020 preprint。§5.1–5.2、§6–7を確認。CPSによる解析の精度低下やcontext-sensitive解析との関係を既に論じる。結論では実装進行中とする。本文のConference'17表示を採録実績と取り違えず、preprintとして扱う。著者実装は未確認。
https://arxiv.org/pdf/2012.06340

Continuing WebAssembly with Effect Handlers、OOPSLA2 2023、arXiv:2308.08347v3。§6のone-shot、型、関連研究の説明を確認。二重利用を動的に検査してtrapする設計で、静的affine型検査を採用したという説明ではない。2023論文の設計を2026の全エンジンの対応状況とは扱わない。著者サイトPDF取得失敗後arXiv本文を利用した。
https://arxiv.org/pdf/2308.08347

検索: compiler dead store elimination precise exceptions predicated stores memory SSA / obfuscation memory store load fusion symbolic array expressions exceptions / WebAssembly obfuscation stack switching continuation WasmFX / obfuscation delimited continuations one shot continuation control flow。

## 再現・次の作業

Node v24.15.0。verify.cjsは既存候補のartifacts-v2を読み、必要バイナリを複製する。TRAP_FUSION_ARTIFACTSで参照元を変更可能。新ディレクトリにスクリプトをコピーして実行する。既存artifactsがあると停止する。追加依存なし。observe.cjsは原IRなしで独立実行できる。

今後の採用判断は、外部に返す必要がある値の秘匿ではなく、元の内部処理・制御関係の理解に必要な解析量を増やす具体的変換を対象にする。これは目的の変更ではなく、意味保存と両立しない保護主張を避けるための条件。新アルゴリズムを開発する全体目標は継続し、CSEC原稿や実験を変更しない。
