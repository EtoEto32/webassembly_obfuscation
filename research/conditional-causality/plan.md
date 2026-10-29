# 入力依存の計算順序を循環する共有演算へ移す仮説

2026-10-22、実装・測定前。直前のgoal turnは状況報告のみで、新しい実験上の進展はなかった。energyの係数変更は終了し、異なる計算順序を共有する方向を検査する。これは新規性を確認した発明ではない。

## 研究判断

語の依存順を固定しない循環が、有限環やenergyの局所射影の失敗を避ける可能性を調べる。先に読んだNeiroukh/Edwards/Song (2008)は、入力ごとに異なるscheduleを持つ循環回路と、それらを共通scheduleへまとめて非循環化する方法を既に扱う。Riedel/Bruck (DAC2003)は回路へのfeedback導入を合成に使う。したがって「入力依存の順序」「循環導入」「共通supersequence」自体を新規と数えない。

残る仮説は、Wasmの型の等しい純粋な語演算を共有する場合、同じ演算表を持つ通常の順序選択VMと比較して、追加実行費用より大きい回復費用を要求できるか、である。否定されたら主発明に採用しない。Wasmの検査済みcall_indirect、private memory、i32の全域剰余演算を使うが、Wasm固有の数学的原理とはいわない。

## 変換

sourceはrun(x:i32,s:i32)->i32と2–16個の純粋な単引数i32関数。sの最下位bitで2つの関数合成順を選び、各順序は全関数を1回ずつ使う。関数本体はadd/sub/mul/bitwise/shift/rotateと定数からなる式に限定する。divide、memory、import、例外・副作用・再入は拒否する。

各順序からpredecessor表を作る。二つの表の和グラフは循環してよい。実行器は関数ごとに一つの状態セルを持ち、選んだpredecessorの現在値を引数にして、そのセルを上書きする。最初の関数のpredecessorは外部入力xを表すsentinel。

二つの順序の最短共通supersequenceを動的計画法で求め、この固定scheduleでセルを更新する。選択した順序がsubsequenceに含まれるので、各セルはそのprefixが実行された後に正値となり、以後の更新でも正値を維持する。したがって任意の初期セルから最後の値が正答となる。これは順序についての帰納法であり、暗号的安全性ではない。

## 対照・攻撃・成功条件

- 元の直接call/branch、同じ演算表から選んだ順を1回実行するVM、固定supersequenceの循環版をraw/O3で比較する。
- 攻撃者はbinary全体と方式を知り、source/seed/生成manifestを持たない。公開predecessor表を各selector値で辿り、acyclicな関数合成を再生成する。scheduleが双方の順序を含むことと、既知実行器のbyte再生成を検査する。
- 3つの語演算fixture、境界値とseed固定乱数、継続呼出しによる非zero状態、別途memoryを公開する診断版の任意初期状態を検査する。短すぎるscheduleとtrap演算を負の対照にする。
- 時間、binary size、linear memory、process RSS、変換/回復時間を保存。性能はwarmup、較正、複数fresh processの中央値と範囲を報告する。未対応・crash・timeoutを解析耐性へ算入しない。
- 新規性と保護効果を別々に判定する。小さい実行費用で明確な解析費用増がない、または既存のschedule合成の直接実装なら不採用。回復可能であることだけを不採用理由としない。

## 原資料と読んだ範囲

- Osama Neiroukh, Stephen A. Edwards, Xiaoyu Song, *Transforming Cyclic Circuits Into Acyclic Equivalents*, IEEE TCAD 27(10):1775–1787, 2008, DOI 10.1109/TCAD.2008.2003305。査読誌。[著者PDF](https://www.cs.columbia.edu/~sedwards/papers/neiroukh2008transforming.pdf)のAbstract・Introduction・Prior Work（pp.1775–1776）を確認。入力条件によるscheduleの違いとschedule合成が本screenに直接近い。全アルゴリズム・実測表は未読で、論文実装の再現とはいわない。
- Marc D. Riedel, Jehoshua Bruck, *The Synthesis of Cyclic Combinational Circuits*, DAC2003, pp.163–168。査読会議。[著者PDF](https://cctbio.ece.umn.edu/wiki/images/b/bc/Riedel_Bruck_The_Synthesis_of_Cyclic_Combinational_Circuits.pdf)の表紙、§1–1.3冒頭を確認。feedbackをsubstitution/minimizationへ導入する構成が既存。以前のbit-feedback調査では本文未取得だったが、今回は取得して読解範囲を増やした。area削減は著者のhardware結果であり、本Wasmの効果に流用しない。
- Sharad Malik, *Analysis of Cyclic Combinational Circuits*, IEEE TCAD 13(7):950–956, 1994, DOI 10.1109/43.293952。[著者機関の書誌・要旨](https://collaborate.princeton.edu/en/publications/analysis-of-cyclic-combinational-circuits/)のみ確認。本文は未読。
- US7249341B2の直接openは今回cache missだった。以前の抽出記録から全請求項を読んだことにはしない。特許性・権利範囲の法的判断は行わない。
