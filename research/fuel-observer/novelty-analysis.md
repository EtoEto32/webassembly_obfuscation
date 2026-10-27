# 差分仮説と先行技術

2026-10-24。Fの拡張であり、別原理の新案数に数えない。**限定的な技術的効果は確認、新規性・進歩性は未確立**。

|一次資料|区分・確認範囲|近接点と残る差分仮説|
|---|---|---|
|Zhang, Askarov, Myers, [Predictive Mitigation of Timing Channels in Interactive Systems](https://www.cs.cornell.edu/andru/papers/ccs11.pdf), CCS2011|査読会議。abstract、§2–3、schedule説明と関連箇所|公開情報でscheduleを変える一般原理は先行。ここでは支払済み論理費用を下回らない累積予約・途中停止・公開後返金を実Wasmへ接続する。単に公開履歴を使うことは新規でない|
|Ene, Mounier, Potet, [Output-sensitive Information flow analysis](https://arxiv.org/html/1909.09567v5), LMCS17(1:15),2021, DOI10.23638/LMCS-17(1:15)2021|査読journal版。abstractと§1–2冒頭。全証明・実験未読|最終公開値で許容する漏洩を扱う。本案は公開前の会計を未来の出力に依存させない。公開出力に応じて保護を緩める一般原理は既知|
|Kuize Zhang, [Detectability of labeled weighted automata over monoids](https://link.springer.com/article/10.1007/s10626-022-00362-8), DEDS32:435–494,2022|査読journal。abstract、§1、§3.4 observer定義。全64頁未読|重み付き状態推定とobserverは先行。本実装は有限の公開語へ累積費用maxを保持する限定計算であり、一般observerを初めて作ったと主張しない|
|Ngoほか、定資源型、SNIP-50、Sapphire gas padding、US20250335260A1|[Fの読了記録](../fuel-frontier/novelty-analysis.md)|費用上界、gas privacy、Wasm quota自体は既知。請求をこれら一般要素に広げない|

追加特許検索でEP3944174A1（resource deduction）を候補として得たが、本文取得が二度失敗した。検索snippetだけで請求項との差を判定しない。全family・各国審査・抵触・出願可能性の法的判断は行っていない。

## 請求項の技術たたき台

**FO1**: WebAssemblyプログラムの実行資源の会計を制御する方法であって、前記プログラムの公開イベントと非負の命令費用を保守的に解析し、各公開履歴について当該履歴と整合する経路の次の公開イベント又は終了までの累積費用上界を生成し、前記履歴を外部へ公開した後に、当該上界と予約済み累積額との差に応じて追加予約又は返金を行い、追加予約が公開残高を超える場合に前記公開履歴の後で実行を停止する方法。

**FO2**: FO1において、同じ構文継続位置で同じ公開イベント列を持つ経路を、累積費用及びイベント到達費用の成分ごとの最大値へ集約して前記上界を生成する方法。

**FO3**: FO1において、返金後の予約額が前記履歴に整合する各経路の既実行費用を下回らず、未公開の実測費用又は将来出力によって返金額を選ばない方法。

**FO4**: FO1において、標準validation済みの変換binaryを生成contractと対応付け、公開イベントの後にのみ公開予算入力を反映し、対応のないイベント又は再入を拒否する方法。

これらは発明要素を検討する草案であり、特許取得の見通しを示すものではない。最大のReject理由は、既知の公開情報依存schedule、保守的費用解析、max-plus observer、予約・返金の組合せが当業者に自然だという点である。明確な独立原理の新規性を確認できるまで主特許案とはしない。

正しい手書き履歴予約との一致は健全性の対照として有用であり、それ自体が不採用理由ではない。ただし自動生成できたという事実だけで、新しい安全原理を証明したことにもならない。

追加でJohn Shortt, *A System for Bounding the Execution Cost of WebAssembly Functions*, Carleton University修士論文、2023年1月、[大学公開PDF](https://people.scs.carleton.ca/~soma/pubs/students/john-shortt-mcs.pdf)のabstract、§1.4、§4.4の経路費用、§6.4を読んだ。査読会議論文とは区別する。WANALYZEはWasmの費用上界を静的に求め、最も高価な経路を選ぶため上界の過大評価が生じると説明する。Wasmから費用上界を自動生成する点も独自要素にできない。全145頁の精読や実装再現は未実施。refundという語の検索不一致は類似機構の不存在を示さない。

その後、**Shortt, Amy Felty, Anil Somayaji, Bounding the Execution Cost of WebAssembly Functions**, VSTTE2025、LNCS16499、83–100、出版2026-08-02、DOI[10.1007/978-3-032-27340-6_6](https://link.springer.com/chapter/10.1007/978-3-032-27340-6_6)を出版元で確認した。会議版の公開年と会議年を混同しない。[会議公開preprint](https://systemf.epfl.ch/etc/vstte2025/preprints/Bounding%20the%20Execution%20Cost%20of%20WebAssembly%20Functions.pdf)のabstract、Introduction、§4末尾、§5–6を読んだ。著者は107,000超の関数への評価を報告し、経路maxの過大評価と関数間・import費用・形式証明を課題に挙げる。これは著者報告で、当方の追試ではない。F-Oのtiny subsetを大規模費用解析に対する優位性と扱わない。公開履歴後の返金が残る差分仮説である。

Jeppe Fredsgaard Blaabjerg, Aslan Askarov, **OblivIO: Securing Reactive Programs by Oblivious Execution with Bounded Traffic Overheads**, CSF2023, pp.292–307、査読会議（[大学書誌](https://pure.au.dk/portal/en/publications/oblivio-securing-reactive-programs-by-oblivious-execution-with-bo-2/)）。[著者PDF](https://askarov.net/oblivio.pdf)abstract、Introduction、§II冒頭、関連研究のdeclassification部分を確認。dummy trafficとpotentialによる反応型プログラムの資源上界が先行する。F-Oはdummy trafficを生成せず会計を扱うが、反応型・資源・情報フローを結び付けるという広い構図は新規でない。40頁版全証明と実装は未追試。
