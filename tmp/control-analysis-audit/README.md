# 制御変換候補と解析器の対応範囲の照合

2026-10-12。新規アルゴリズムの採用報告ではない。既存候補を再度名前だけ変えて試作しないための、一次資料に基づく設計判断。

## 検討した具体的な書き換えと判断

元の領域を、入口ラベル p、生存状態 s、更新 F_p、次ラベル next_p で表す。

1. **例外転送**：領域終了時の `br q(s)` を `throw tag_q(s)` にし、対応ハンドラから q を実行する。payloadで生存状態を渡すだけなら、既存の例外ベース制御変換のWasm実装に留まる。2026-10-11のscreeningで既に見送っている。今回、再採用しない。
2. **継続転送**：`F_p(s); goto q` を、通常継続 k と例外継続 h を受ける領域関数 `K_p(s,h,k)` に変え、次の領域を継続呼出しとして表す。既存のCPS難読化と直接重なる。関数参照をWasmの継続参照へ変更するだけでは差分にならない。
3. **領域ごとの動的変種選択**：同じ意味を持つ変種 F_(p,j) を用意し、境界で j=oracle(s,r) を選び、生存状態を変種jへ渡す。関数入口だけでなく途中境界で変種を切り替える案も、ASE 2022のOSR方式と比較する必要がある。単なる途中切替を新規規則にしない。

この3案に独自性を付与できる具体的な追加規則は、今回確定できていない。一般にこれらを用いる全手法が新規性を持てない、と証明したわけではない。新しい規則を設計できた場合は、その規則の差を再審査する。

## 確認した一次資料

### 継続による難読化

Kenny Zhuo Ming Lu, *Control Flow Obfuscation for FJ using Continuation Passing*, arXiv:2012.06340v2, 2021-02-26。
https://arxiv.org/pdf/2012.06340

確認範囲：要旨、§1、§2の例とcombinator。通常・例外継続を使う制御変換を確認。著者実装や耐性評価の再現は未実施。PDF中の会議名・DOIのテンプレート表記を実在する掲載情報として転記しない。

### 動的変種切替の直接比較先

Giacomo Priamo, Daniele Cono D'Elia, Leonardo Querzoni, *Principled Composition of Function Variants for Dynamic Software Diversity and Program Protection*, ASE 2022, DOI 10.1145/3551349.3559553。
https://www.diag.uniroma1.it/~delia/papers/ase22.pdf

確認範囲：§1–3、Fig.1、§4の評価条件。領域境界のoracle、状態移送、call barrier、global storageとtail callの実装を確認。著者実装は未取得・未実行。実装候補の所在は https://github.com/gpriamo/osr-diversity 。

**今回の設計判断**：動的な切替先やtrace多様性そのものを新しい原理と呼ばない。異なる状態表現への移送も、既存の補償コードや本リポジトリで棄却済みの境界再符号化との差を必要とする。任意の変種間移送がこの論文で解決済みとは解釈しない。

### 動的VMスケジューリング：本文未確認

Kuang et al., *Enhance virtual-machine-based code obfuscation security through dynamic bytecode scheduling*, Computers & Security 74 (2018), DOI 10.1016/j.cose.2018.01.008。
https://eprints.lancs.ac.uk/id/eprint/89498/?template=browse
https://www.sciencedirect.com/science/article/pii/S0167404818300270

今回確認したのは掲載情報と要旨。公開PDF https://eprints.lancs.ac.uk/89498/1/DSVMP_C_S.pdf のweb取得は失敗。要旨の動的スケジューリング・複数VMという内容を検索手掛かりにし、具体的な全変換規則を確認済みとはしない。著者実装も未確認。

## GenWasymを比較器にする場合の条件

*Compiling WebAssembly Concolic Execution with Staging, Continuations, and Snapshots (Extended Version)*, arXiv:2608.18327v1 (2026)。
https://arxiv.org/html/2608.18327v1

確認範囲：導入、§7.1–7.2、§8の実験条件、§9のmeta-level継続の説明。§7.2にはSIMD・function references・module import/exportの未対応記述がある。解析器内部のCPSと、入力Wasmのnative continuation対応は別。例外やstack switchingへの対応可否は未確定。

固定artifact入口： https://zenodo.org/records/21769340 （v7）。付属Readme.mdを取得し、公開MD5と一致を確認した。915.6MBの本体tar.gzは未取得・未実行。Readme内の別recordへのリンクを、固定v7本体を実行した証拠としない。

- 保存名：GenWasym-artifact-Readme.md
- MD5：12a5a440fdc2d69df9b6e7ffe4e47b17
- SHA-256：d4b970ea0a14a1243f8c29f539f7f54ea7c424b3e571049b6426c76259c1d474

**こちらの比較方針**：通常版と候補版の双方について必要命令の対応を先に確かめる。unsupported、compile error、runtime error、時間切れ、再構成成功を分離する。未対応命令を導入して解析器を止めただけなら保護効果に数えない。論文間の速度比を、この候補の難読化解除コストへ読み替えない。

## 次の設計で埋めるべき点

次に実装へ進めるには、上の3規則にはない状態・制御の依存関係の変化を示す必要がある。候補の形式は、入口関係 R_p(s,z)、実際の変換後更新 G、出口関係 R_q(F_p(s),G(z)) として記述する。これは検証用の形式であり、この表記自体を新アルゴリズムと主張しない。

とくに、共通生存状態を境界で再構成しない方式を検討するなら、既存の符号化変換・OSR補償・仮想化でも同じ移送を実現できないのかを比較する。単に対応する解析器をまだ実装していないことは採用理由にならない。

検索語：WebAssembly obfuscation exception handling continuation control flow obfuscation / obfuscation effect handlers continuation resumption control flow / obfuscation coroutine / obfuscation continuation permutation / control flow obfuscation scheduling。

新しいWasm変換器・実行測定結果はこの記録には含まれない。新規性と有効性を支持できる採用候補は未確定。CSEC原稿と既存実験は変更していない。
