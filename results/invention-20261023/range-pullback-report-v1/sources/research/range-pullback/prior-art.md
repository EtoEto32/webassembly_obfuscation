# 先行技術・実ツールの確認範囲

2026-10-23。検索で見つからないことを新規性の根拠にしない。

|資料|区分・確認した範囲|今回との関係|
|---|---|---|
|Aditya K Kamath, Simon Peter, *(MC)²: Lazy MemCopy at the Memory Controller*, ISCA2024,1112–1128, DOI[10.1109/ISCA59077.2024.00084](https://doi.org/10.1109/ISCA59077.2024.00084)。[著者PDF](https://akkamath.github.io/files/ISCA24_MCSquare.pdf)、[著者artifact](https://github.com/AKKamath/MCSquare-ISCA24)|査読会議論文。要旨・導入、artifact README。詳細実装・全性能表は未読、gem5未実行|prospective copyを追跡し、accessをsourceへ転送するlazy copyが先行する。要旨はProtobuf43%改善、huge page COW latency250倍低減を報告するが、本研究の再現値ではない。hardware memory controllerという実装の違いを、一般の遅延コピーの新規性にはしない|
|[LLVM MemCpyOptimizer.cpp](https://llvm.org/docs/doxygen/MemCpyOptimizer_8cpp_source.html)|公式実装資料。検索で示されたload/store forwardingとmemcpy forwardingの説明のみ確認|load forwarding・copyの合成は既存コンパイラ技法。今回の逆順条件式やWasmのtrap条件をこのpassがそのまま処理するとは確認していない。LLVMでの本例の実測はない|
|[WebAssembly Core3.0 execution: memory.copy](https://webassembly.github.io/spec/core/exec/instructions.html#exec-memory-copy)|公式仕様、2026-10-23表示。memory.copyの範囲検査、零長、方向別コピー規則を確認|両範囲の検査が零長判定に先行すること、重なりの意味保存の根拠。仕様対応それ自体を発明としない|

探索語は `"obfuscation" "write log" memory`、`"obfuscation" "deferred" "memory" stores`、`"lazy" "memcpy" paper`、`"memory.copy" "lazy" WebAssembly`、`"load" "memcpy" "forwarding" LLVM`。この検索は特許調査の完了を意味しない。今回の限定変換には近い既知機構と安い回復があり、主特許候補としての追究を終了する。

## 新たに見つけた評価資料

Ryutaro Nishizaka, Yudai Fujiwara, Takuya Shimizu, Kazushi Kato, Yuichi Sugiyama, *Towards LLM-Resistant Software Protection: Agent Failure Patterns in CTF Reverse Engineering*, BAR2026, DOI[10.14722/bar.2026.23058](https://doi.org/10.14722/bar.2026.23058)、[主催者PDF](https://www.ndss-symposium.org/wp-content/uploads/bar2026-58.pdf)。ワークショップ論文。表紙・要旨・導入・実験設計冒頭のみ確認。3種のagentと24 CTF課題を扱う。全結果・失敗分類の個別事例は未読。本研究でLLM抵抗性を測ったという意味ではない。誤解やtool未対応を、算法の解析困難性と混同しないための追加資料とする。

WAMOのACM本文取得は今回も403で未達。第三者要約から新規性判断を補完しない。NotDecの既存sourceは保存されている。今回のread-only環境確認ではdockerDesktopLinuxEngineのpipe不在。WSL一覧はsandbox内でE_ACCESSDENIEDだったが、承認されたsandbox外の同じ一覧取得は成功し、docker-desktopのみを返した。利用可能な通常のLinux開発環境はこの確認からは得られなかった。いずれもNotDecの解析失敗ではなく、当環境で実ツール評価を実施したとはしない。設定変更やfactory resetは行っていない。
