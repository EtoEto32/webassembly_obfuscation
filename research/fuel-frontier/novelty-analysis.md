# 新規性の反証と請求項要素の対応

2026-10-24。結論は「動作する限定候補、特許に足る差分は未確立」。特許の成立性・抵触判定ではなく、技術資料の比較である。

|要素|既知の近接技術|今回の具体化|残る反論|
|---|---|---|---|
|資源使用による秘密漏洩の抑制|Ngoら S&P 2017、SNIP-50|Wasmの元opcode費用を予約|gas privacy自体は既知|
|公開イベントに共通の予定を強制|Zhangら CCS 2011、PLDI 2012|実時間でなく予算受付の境界|観測軸の変更だけでは弱い|
|累積費用の上界と未使用分の持越し|amortized resource analysis、potential|event順位ごとの最大累積費用の差を挿入|既知のpotential解析で説明できる|
|Wasm binaryから生成|通常のCFG・最長経路解析、meter挿入|検証済み有限subset、同一event suffixの照合|標準的解析の実装上の組合せに見える|
|不足時の公開prefix進捗|段階的受付・イベント予定|全額を入口で要求せず次区間前に停止|手書き同一scheduleでも達成する|

請求項F1–F4は[algorithm.md](algorithm.md)にある。技術要素を具体化したたたき台であり、この表で既知とした要素を広く独占できるという意味ではない。

## 最も近い論文と読了範囲

- Danfeng Zhang, Aslan Askarov, Andrew C. Myers, **Predictive Mitigation of Timing Channels in Interactive Systems**, ACM CCS 2011、査読済み。[著者公開本文](https://www.cs.cornell.edu/andru/papers/ccs11.pdf)。Abstract、予定・予測失敗の定式化、実装・評価の関連箇所を確認。公開情報を使う予定で出力を遅延させ、予測失敗の情報量を抑える。今回との違いは有限コードの静的費用上界と予算受付だが、公開イベント整形の原理は先行する。全証明・実装の追試はしていない。
- 同著者、**Language-Based Control and Mitigation of Timing Channels**, ACM PLDI 2012、査読済み。[著者公開本文](https://askarov.net/pltiming-pldi12.pdf)。Abstract、§7の関連箇所を確認。言語の型付けとmitigationを組み合わせる。型から安全な予定を導くという広い主張を新規としない。全証明・評価は未検証。
- Ngoらの定資源型、SNIP-50、Sapphire、Cogaの書誌と読了範囲は[screening.md](screening.md)。**Cogaは公式採択要旨のみ**であり、今回検索でも本文・実装の所在を特定できなかった。未読ゆえ、差分を断定できない。

## 先行特許

[US20250335260A1](https://patents.google.com/patent/US20250335260A1/en)、**Schema-based resource allocation for request processing**。発明者Jimmy Bourassa、掲載出願人Shopify Inc、優先日2024-04-30、公開日2025-10-30。Google Patents掲載情報であり、権利状態・全familyの法的監査はしていない。請求項1–11とWasm fuelの関連説明を読んだ。schemaのfield数等に基づく処理jobへの資源割当を扱い、今回の「同じ外部事象列に対する累積予約」の全要素一致は読了範囲では確認しなかった。しかし、これだけで新規性や進歩性を支持しない。

## 採否

この案は、最初の自作例が通常最適化で消えるという反例を経て、明示公開値のあるcompiler出力へ適用できた。技術的な効果は確認したが、強い対照への速度優位と実アプリでの必要性は示せていない。特許主案へ昇格せず、限定的な修士研究・評価題材として保存する。次の探索では「予定を自動生成した」以外の機構上の差が必要である。
