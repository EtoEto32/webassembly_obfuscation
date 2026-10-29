# 文献と探索記録（2026-10-19）

## 最も近い一般原理

Eduardo D. Sontag, **Discrete-time polynomial systems with inputs and outputs: structure, reachability, observability, and minimal realizations**, [arXiv:2609.36423v1](https://arxiv.org/abs/2609.36423), 2026-09-29公開。プレプリントとして扱う。Abstract、§2の系の定義、§3.1の体の仮定、§5/§8の入出力差分式への言及を読んだ。全証明は読了していない。著者は**1976年の博士論文の更新版**と明記しており、原理自体が2026年に初出とは扱わない。

入力履歴と出力の関係、可観測な状態による実現を研究する一般理論がある。本実験の状態消去もこの問題設定に近い。ただし本文の基礎は無限体で、今回の有限環Z/(2^32)へ定理を無条件に移していない。今回の限定恒等式は分配法則から直接導出した。特定のword環への適用だけで新規性が成立するとは判断しない。

Sontag, **Polynomial Response Maps**, Springer, Lecture Notes in Control and Information Sciences 13, 1979, DOI [10.1007/BFb0042025](https://link.springer.com/book/10.1007/BFb0042025)。出版社の書誌・目次を確認。書籍本文を読了したとはしない。2026版と区別して記録する。数値的な難読化評価を行う資料ではない。

**On split realizations of response maps over rings**, Eduardo D. Sontag, Information and Control, 1978, DOI [10.1016/S0019-9958(78)90401-1](https://www.sciencedirect.com/science/article/pii/S0019995878904011)。検索抽出に「可換環上の線形response mapの実現」とある。本文openは403で失敗したため、今回の非線形式と同一手法とは判断しない。「環上なら新しい」という主張への追加照合先とする。

既存の[多項式表現の調査](../polynomial-carrier/prior-art.md)・[中間更新合成の反証](../checkpoint-composition/README.md)とも照合した。今回は2回分の単一更新を展開する構成ではなく、非公開状態を出力履歴へ置換する。しかし変換の形式が違うことと、独立した難読化技術としての新規性・効用は別である。

## 今回の別方向のスクリーニング

型・例外・共有参照を最初に検討したが、[既存の型/例外ゲート](../../tmp/candidate-screening/README.md)と[GC回路の記録](../alias-circuit/README.md)を確認すると、単なるtype/tagの置換や局所alias gateでは既存の反証を避けない。計算全体で共有状態を更新する案も、先行alias難読化から区別できる具体規則を確定できず実装へ進めなかった。

**Practical Data Location Obfuscation**, Bertrand Anckaert, Mariusz Jakubowski, Ramarathnam Venkatesan, Nick Saw, MSR-TR-2009-3, January 2009。[Microsoftの原資料ページ](https://www.microsoft.com/en-us/research/publication/practical-data-location-obfuscation/)の要旨を確認。heap再配置、localのheap移行、pointer scramblingを組み合わせるため、位置変更だけを新規案としない。SPEC CPU2006評価への言及はあるが、本文の数値は今回確認していない。技術報告として扱う。

weighted tree automataの[低rank近似論文](https://proceedings.mlr.press/v51/rabusseau16.html)（Rabusseau/Balle/Cohen, AISTATS 2016）は検索抽出のみ確認。多項式・tensor・基底変更を再度試す前の照合先であり、今回実装した状態消去の同一先行研究とは数えない。参照先を実際に確認した範囲を越えて、読了・追試・性能比較を主張しない。

検索語には`obfuscation input-output recurrence`、`nonlinear discrete time state elimination difference equations`、`obfuscation state elimination polynomial`等を使用。特定語に検索結果がないことは新規性・進歩性の根拠にしない。この回で新たな公開特許の請求項を精読したという記録はない。特許性は未確立。
