# 次の探索に向けた先行性の追加確認

2026-10-27。Sの弱い差分を別名で新案としないため、入力生成・GC testing・cross-language testingの既存範囲を追加検索した。このノートは候補の採用や効果の実証ではない。

- **Weaver: Fuzzing JavaScript Engines at the JavaScript-WebAssembly Boundary**、Zhangほか、arXiv:2603.18789v1、2026-03-19。プレプリントとして扱う。[本文](https://arxiv.org/html/2603.18789v1)の§II/IIIを確認。JSとWasmの型を追跡し、生成時に値を相互利用する。型canonicalizationによるmodule間matchingも説明されている。「複数言語の型を追跡して合う値を渡す」という一般枠組みを新規性の核にできない。論文報告のcoverage・2件のbugは著者の結果であり、今回の再現結果ではない。
- **RGFuzz: Rule-Guided Fuzzer for WebAssembly Runtimes**、Junyoung Park, Yunho Kim, Insu Yun、IEEE S&P 2025。[著者研究室のabstract](https://hacking.kaist.ac.kr/publication/park-rgfuzz/)を確認した。コンパイラ規則を使った生成とreverse stack generationが既存である。本文・実装の全精読は未実施。「対象の規則から難しい命令組を作る」だけでは差分が弱い。
- **Heap Fuzzing: Automatic Garbage Collection Testing with Expert-Guided Random Events**、ICST 2023候補。[著者所属機関PDF](https://rmod-files.lille.inria.fr/Team/Texts/Papers/Poli23a-ICST-HeapFuzzing.pdf)は今回timeoutで本文取得できず、検索抜粋まで。GC eventを使うfuzzingの近接研究として追跡する。未読の詳細を補完しない。
- **Exploring JVM Garbage Collector Testing with Event-Coverage**、ACM TOSEM、DOI [10.1145/3733598](https://doi.org/10.1145/3733598)。出版社検索結果のabstract・書誌を確認したが本文openは403。JVM GCのevent coverageを使う研究が存在するため、GC eventをfeedbackにする一般着想も独創性の根拠にはしない。Wasmへの適用差は未確認。

次の実験を設計する際は、実際に到達していない状態・操作を先に特定し、それを対象にする必要性を確認する。既存fuzzerの実行ログが保存済みなので、まずRの502生成物のtrap/fuel/未到達を分類することが可能。ただし、分類するだけで新しい生成器を発明したとは呼ばない。

なお、今回のCLI最小例も `results/gc-realization/cli-v1` に保存した。実型binaryから132-byte Wasmを生成し、Wasmtimeで `run() = 1` を確認した。
