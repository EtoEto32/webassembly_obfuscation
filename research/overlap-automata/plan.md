# 元DFAで検証しながら状態を重ねるNFA化：候補の固定

2026-10-18。採用済み発明ではなく検証可能な仮説。共有relayは引数対応の要約で消えたため、今回は実行中の状態と元の状態の一対一対応をなくす方向を調べる。

## 規則

入力は二文字DFAを実行するWasm scanner。全ての語を受理する既知の補助NFA Uとの積を作る。次にNFAの状態を2個ずつ結合する。ただし、元DFA D の補言語との積が空である結合だけを許す。結合は受理語を減らさず、積の空性検査は誤受理の追加を防ぐので、元言語を保つ。

単なるNFA最小化との仮説上の差は、状態数最小だけを目標にせず、NFAの各状態rが同時に対応し得る元状態集合 R(r) の重なりを増やす選択である。配布物にRや元DFAは入れない。複数の元状態で同じNFA状態を共有し、状態ごとの単純な色分けによる復元を妨げられるかを測る。

```
N <- product(D, universal_guard(k))
repeat within a fixed search budget:
    enumerate/sample candidate pairs of NFA states
    N' <- identify one pair, union their transitions/initial/final flags
    if an accepting pair is reachable in N' × complement(D): reject
    compute R(r) from reachable pairs (q,r) in D × N'
    choose a safe merge maximizing sum_r (|R(r)|-1)
emit a packed-bitset Wasm transition engine for N
```

Uは奇数長kのwindow内で隣接bit（末尾と先頭も隣接）が一箇所以上等しいことを、複数のpatternの和として受理する。奇数cycleに二色を交互配置できないため、長さk以上の全語を受理する。長さk未満は別の有限鎖で受理する。補助状態は秘密鍵ではない。実行中の非決定性は乱数ではなく、到達可能状態集合を決定的に更新する意味である。

## 反証と成功条件

保護課題は同じ言語を受理する簡潔なDFAの回復。元の番号や生成seedの回復は要求しない。解析者は方式・全バイナリを知る。素朴なsubset構成、forward bisimulation後のsubset構成、逆向きの決定化も試す。一般問題のPSPACE困難性は、この生成族の保護強度を保証しない。

比較は元、積だけ、同じ回数の安全なランダム結合、重なりを優先する結合。集合数・元状態との重なりは診断値であり、回復時間・メモリ・実行費用を主指標とする。状態集合が大きくても逆向き決定化やsimulationで安く回復できれば、その費用を報告する。

Wasm固有性は現時点では強くない。固定幅整数・SIMDを用いる集合更新、非公開追加memoryの境界保持を実装上の焦点にする。新たなWasm命令を使うこと自体は新規性としない。最大のReject理由は、古典的NFA構成・意味保存最小化から独立した効果がなく、混合後も安い商へ戻せることである。

## 先行技術の初期照合

[Brzozowski/Tamm, Minimal Nondeterministic Finite Automata and Atoms of Regular Languages](https://arxiv.org/pdf/1301.5585)（arXiv v1 2013、今回読んだ版はプレプリント）のAbstract、§1–2を確認した。quotientの和でNFA状態を表すこと、非一意のNFA、Kameda–Weinerの最小化は既知。新しい数学原理とは主張しない。Kameda/Weiner1970の元論文は今回は検索抽出のみで、原本文全体は未読。

[Clemente/MayrのNFA reduction資料](https://homepages.inf.ed.ac.uk/rmayr/1711.09946.pdf)と[Ćirićほかのbisimulation資料](https://arxiv.org/abs/1102.5449)は追加の解除・先行性比較先。詳細の確認範囲は実際に読んだ後に更新する。特許性の確定や、全関連文献の網羅を意味しない。

## 初回モデル検査後の修正1

`overlap-screen-v1` は未到達・受理状態へ到達しないstateもRの得点へ含めていた。これでは捨てられる状態を混ぜるだけで得点が増える。v2以降は初期構成・候補結合ごとに到達可能かつ受理可能な状態だけへtrimし、その後で得点を計算する。元言語を保つtrimであり、前の数値を肯定的な保護証拠にしない。ランダム版と選択版の実状態数も保存し、結合回数が同じことだけで費用が同じとは扱わない。
