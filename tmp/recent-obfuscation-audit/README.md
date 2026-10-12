# 次候補選定の追加監査（2026-10-12）

encoding-cosynthesis-gateの棄却後、同じ多項式の次数増加を続けず、最近の研究と別の表現方式を再確認した。新しい実行実験は行っていない。新規アルゴリズムの採用は未確定、研究全体の目標は継続する。

## 実装前に除外した単純案

### T関数で非線形なディスパッチャを作る

US11227033、Efficient obfuscation of program control flow、2022-01-18登録。Justia掲載の特許本文DescriptionのT-Functions節とClaims9/10/20を確認。T関数による状態の符号化・復号・更新をディスパッチャへ使う具体例が存在する。したがって「多項式からBoolean混合のT関数へ変える」だけは新方式として採用しない。

特許の強度主張や秘密鍵前提を検証したものではなく、第三者の実験的証明ともみなさない。登録日・優先日・公開日は区別し、本記録は法的な権利範囲の判断ではない。
https://patents.justia.com/patent/11227033

### 浮動小数点を別表現へ持ち上げてMBAを使う

Protecting Floating-Point Computation for Deep Neural Network Binaries with Mixed Boolean-Arithmetic Obfuscation（FLOB）、arXiv:2607.17603v1、2026 preprint。HTML本文§3.1–3.2.1、§5.2–5.3を再確認。浮動小数点の演算を分解し、拡張した表現でMBAを適用する内容がある。この発想自体を新規性にしない。

符号付きゼロについて概要と詳細の記述に注意が必要だが、著者コードや全適用条件を調べていないため、著者実装のバグとは断定しない。また評価の失敗分類にはクラッシュ等も含まれるため、未対応解析器の停止を我々の難読化の強度として数えない。
https://arxiv.org/html/2607.17603v1

## 新しい候補を判断する上で本文が不足している資料

| 文献 | 現在の根拠 | 次に必要な照合 |
|---|---|---|
| asmMBA: Robust Virtualization Obfuscation with Assembly-Based Mixed Boolean-Arithmetic、SAC2025、DOI10.1145/3672608.3707862 | 著者大学の書誌・要旨。著者labの業績リストで存在確認。ACM PDFは403 | 命令段階でのMBA適用と既存LOKIとの差。要旨だけで具体変換規則を推測しない |
| WAMO: Toward Secure Browser Inference via Web Model Obfuscation in WebAssembly、WWW2026、DOI10.1145/3774904.3792297 | 書誌のみ。ACM PDF取得不可 | モデル状態・メモリ表現の具体的な難読化方式。未読のまま重複/非重複を断定しない |
| Resilient Web Code Execution: E-Graph Driven Obfuscation for Microarchitectural Attack Mitigation、DOI10.1109/ICSADL67539.2026.11451945 | 二次書誌サイトの検索情報のみ | 出版者・著者の本文で確認するまで研究の技術的根拠として採用しない |

asmMBAの一次書誌：https://pure.korea.ac.kr/en/publications/asmmba-robust-virtualization-obfuscation-with-assembly-based-mixe/

著者lab業績：https://protocol.korea.ac.kr/publication （検索結果取得、本文openは失敗）

WAMO書誌：https://ir.webis.de/anthology/publications/rec%2Bconf%2Bwww%2BWangYHGXH26 （二次書誌）

これらの取得失敗は研究全体の作業を妨げる障害ではない。特定資料に依存しない設計・実験は可能。アクセス制限を回避した取得や、著者への無断連絡は行わない。

## 次候補に必要な具体条件

1. 既存の符号化を選び直すだけでなく、復元された原因を変える更新規則を示す。難しい数学関数を入れたというだけでは採用しない。
2. 秘密鍵を外部から得る前提や、解析者が内部を観測できない前提を新しく導入して過去の失敗を隠さない。
3. 別表現で計算する場合は途中の元の状態露出を検証する。弱い復元文法だけを基準にしない。
4. 全数検証可能な小幅モデルは初期ゲートに利用できるが、lookup表の状態数を増やしただけをi32向け新アルゴリズムとはしない。
5. 浮動小数点へ進むなら、丸め・signed zero・subnormal・NaNを含む意味保存の規則と、FLOBとの差を先に具体化する。単に追加測定する研究へ目的を変更しない。

ここまでで新しい方式ができたわけではない。本文取得済みの根拠と未取得資料を分け、既知の単純案の重複試作を避けるための監査結果である。

## 検索記録

WebAssembly obfuscation 2025 2026 new technique paper / WebAssembly obfuscation limitations future work 2025 / WebAssembly obfuscation algorithm structured control flow polymorphism 2026 / WAMO Web Model github / asmMBA pdf / asmMBA github / WAMO 3792297 pdf / WebAssembly obfuscation floating point SIMD encoding / obfuscation T-functions data encoding / obfuscation carry SIMD encoding / obfuscation minimum cut data encoding / obfuscation intermediate values encoding synthesis / obfuscation rounding error-free transformations。

最後の丸め関連検索ではEFT・数値解析の文献が見つかったが、本文未確認。補償項や誤差項を運ぶこと自体を新発見とはしない。検索結果のクロール時刻は刊行年に使用していない。
