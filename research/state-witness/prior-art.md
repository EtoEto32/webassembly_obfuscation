# Kの先行研究と反証

## 2026-10-25：直接近い等式解析とWizerの追加照合

* Markus Müller-Olm / Helmut Seidl / Bernhard Steffen, **Interprocedural Herbrand Equalities**, ESOP 2005, LNCS3444, pp31–45, [DOI10.1007/978-3-540-31987-0_4](https://doi.org/10.1007/978-3-540-31987-0_4)。査読会議論文。[著者PDF](https://www.uni-muenster.de/imperia/md/content/informatik/agmueller-olm/publications/esop05-herbrand.pdf)のabstract/Introduction、§2–3の一部、§4の未知値代入・固定点Theorem1を読んだ。[著者所属大学の書誌](https://portal.fis.tum.de/en/publications/interprocedural-herbrand-equalities)でも会議・著者・DOIを確認した。等式連言への逆代入、未知値の普遍量化、異なる二値による簡約を既に扱う。Kの既知原理との重なりを、一般的なWPという名前以上に具体的に裏付ける。一般Herbrand項や再帰関数の全理論をKが再実装したわけではない。著者実装は未実行。[追加の自作backend比較計画](guard-herbrand-plan.md)を保存した。
* Markus Müller-Olm / Oliver Rüthing / Helmut Seidl, **Checking Herbrand Equalities and Beyond**, VMCAI2005, LNCS3385, pp79–96, [DOI10.1007/978-3-540-30579-8_6](https://doi.org/10.1007/978-3-540-30579-8_6)。著者所属大学の[公開書誌](https://www.uni-muenster.de/AlleInformatiken/professoren/mueller-olm.shtml)と検索に返った著者PDFのabstract/WP節抜粋を確認。PDF直接取得はTUM版timeout、Münster版404であり、全文読了としない。等式連言・正のBoolean組合せを扱う先行研究として候補に入れるが、今回の技術比較の主要根拠は本文を読めた前項に置く。
* **Wizer / Wasmtime 50.0.0**、Bytecode Alliance、公開実装、2026-10-20 release。学術論文とは区別する。[lib.rs](https://github.com/bytecodealliance/wasmtime/blob/v50.0.0/crates/wizer/src/lib.rs)のdrop/table更新拒否、[rewrite.rs](https://github.com/bytecodealliance/wasmtime/blob/v50.0.0/crates/wizer/src/rewrite.rs)のactive/passive/data index維持を確認した。今回は公式CLIも実行し、4受理例の同じ観測と4例の明示的未対応を[記録](wizer-comparison-results.md)した。寿命を扱えない場合に適用範囲を狭めることも先行し、未対応をbugとしてKの優位へ換算しない。

追加検索は `Karr affine weakest preconditions equality analysis`、`weakest preconditions Herbrand equalities algorithm`、`Interprocedural Herbrand Equalities`、`WebAssembly snapshot passive data segments Wizer`。同じ題名が見付からないことを新規性の証拠にしない。

## 2026-10-24追加の反証調査

追加の有限domain対照では、[Oxford Concurrency GroupのData Independence解説](https://www.cs.ox.ac.uk/activities/concurrency/research/dataindependence/)本文を読んだ。copy/input/output/equalityに制限した系を有限の型instanceへ縮約する先行研究の概要であり、本研究の新原理とはしない。

Andrzej S. Murawski / Steven J. Ramsay / Nikos Tzevelekos, **DEQ: Equivalence Checker for Deterministic Register Automata**, ATVA2019, pp350–356, DOI10.1007/978-3-030-31784-3_20。[著者PDF](https://www.cs.ox.ac.uk/andrzej.murawski/papers/atva19.pdf)のabstract、Introduction、Implementation（PDF1–3頁の該当箇所）と[大学metadata](https://research-information.bris.ac.uk/en/publications/deq-equivalence-checker-for-deterministic-register-automata/)を読んだ。査読会議論文。群論による簡潔な関係表現でdeterministic register automataの同値を検査し、RALib/LOIS/NLambdaと比較する。全文の評価追試・著者実装の実行はしていない。有限alphabetへの展開や記号的な同値検査自体をK独自とする根拠はない。

|資料|読んだ範囲と種別|今回との関係|
|---|---|---|
|Jiakai Xu / Tianle Zhou / Georgios Liargkovas / Danielle Gillai / Ruizhe Fu / Patrick Shen / Eugene Wu / Kostis Kaffes, [StateFork: Branchable Infrastructure for Agent Exploration](https://arxiv.org/html/2609.38648v1), arXiv2609.38648v1, 2026-09-29, DOI10.48550/arXiv.2609.38648|プレプリント。abstract、Introduction、§2.2を読んだ。査読済みとしない|将来の許された操作列で観測が一致する復元契約を明示する。全bit一致より弱い契約、外部入力と隔離境界の議論も先行する。Kはこの一般論を新規性に数えられない。本文の評価を再現した比較ではない|
|Raiki Tamura / Daisuke Kotani / Kazuyuki Shudo / Yasuo Okabe, [Bringing Together Cross-ISA Checkpoint/Restoration and AOT Compilation of WebAssembly Programs](https://conf.researchr.org/details/icfp-splash-2025/mplr-2025-papers/1/Bringing-Together-Cross-ISA-Checkpoint-Restoration-and-AOT-Compilation-of-WebAssembly), MPLR2025, DOI10.1145/3759426.3760985|査読会議。会議abstract冒頭と[著者文献一覧](https://shudo.net/publications/)の書誌情報。本文・評価未読|AOT時の機械語instrumentationとstackmapにより機械依存stateとWasm stateを対応付ける。実行形式の違いをまたぐ状態復元は先行する。segmentやhost契約の詳細対応は未確認|
|Yeqi Fu / Kaihang Ji / Yuanpeng Wang / Zong Cao / Jiahao Liu / Ding Li / Yao Guo / Zhenkai Liang, [WASCII: Bridging WebAssembly Specifications and Implementations through LLM-Enhanced Validation](https://conf.researchr.org/details/issta-2026/issta-2026-research-papers/61/WASCII-Bridging-WebAssembly-Specifications-and-Implementations-through-LLM-Enhanced-), ISSTA2026|査読会議research track、公開abstractと著者欄のみ。本文未読|仕様からCheck Treeを作り実装と対応付け、実行検査後にruntime差分試験を行う。abstractの著者報告は7 runtimes、209差、33新規確認、18修正。今回の再現値ではない。LLMによる仕様検査や差分試験自体をKの新規性に数えない|

StateForkの対象はterminal agentのsessionで、Kの限定Wasm条件合成とは異なる。しかし「復元を観測同値で評価する」という動機が異分野でも明示されているため、対象差だけで独立原理を主張しない。

調査日2026-10-24。読んだ範囲だけを記載する。新規性を確認したという結論ではない。

|資料|種別・読んだ範囲|提案・確認した事実|Kへの反証/限界|
|---|---|---|---|
|[WebAssembly core specification](https://www.w3.org/TR/wasm-core/)、WebAssembly Working Group、2026版|標準。storeとbulk instructionの該当節|memory/table/global/segmentを別々に意味状態として定義|state構成要素を列挙することは新規でない|
|[公式memory_init test](https://github.com/WebAssembly/spec/blob/aa4dcf44b8de3f3f3270ca067422172518ecc341/test/core/bulk-memory/memory_init.wast)、WebAssembly contributors|公開実装。drop周辺と0長case、実際に取得し実行対象にしたmodule|source offset 1 / length 0がdrop後trapになるcaseが既存|Kの識別命令そのものは既知。現testはgeneratorから作られており「自動生成だから新規」も成り立たない|
|[Weave](https://github.com/dphilla/weave/tree/55e36b5f5d5b31d14f1521c3a4327c248ddeba19)、dphillaほか、commit日時2026-10-08|公開実装。DESIGN、memory.rs、emit.rs、該当test。追加実験で実行済み|checkpoint前後の意味比較、drop-gating、0長境界testがある。今回32復元も一致|checkpointのdrop状態を調べることも既存。最近接の具体的反証資料|
|[WEST: Specification-Based Test Generation for WebAssembly](https://pure.kaist.ac.kr/en/publications/west-specification-based-test-generation-for-webassembly/)、Dongjun Youn / Wonho Shin / Sukyoung Ryu、ASE 2025、pp.1403–1414、DOI 10.1109/ASE63991.2025.00119|査読会議。大学公開abstract/metadataのみ。本文未読|SpecTecからtestを生成し、abstractでは4engineの16bugs、11確認・修正を報告|仕様由来のtest生成をK独自としない。内部oracleとの差は本文未読で未確定|
|[WASMaker: Differential Testing of WebAssembly Runtimes via Semantic-Aware Binary Generation](https://2024.issta.org/details/issta-2024-papers/101/WASMaker-Differential-Testing-of-WebAssembly-Runtimes-via-Semantic-Aware-Binary-Gene)、Shangtong Cao / Ningyu He / Xinyu She / Yixuan Zhang / Mu Zhang / Haoyu Wang、ISSTA 2024、DOI 10.1145/3650212.3680358|査読会議。会議abstractと公開README。別途preprint WRTester (2023, arXiv:2312.10456v1) §3.4を読んだ。版の同一性は未照合|binaryの分解・組立と差分試験、instrumentationによる原因箇所特定。会議abstractは33 bugs、25確認と報告|binary-based differential testingや原因特定自体は新規でない。実装は今回未実行|
|[WADIFF: A Differential Testing Framework for WebAssembly Runtimes](https://www4.comp.polyu.edu.hk/~csxluo/WADIFF.pdf)、Shiyao Zhou / Muhui Jiang / Weimin Chen / Hao Zhou / Haoyu Wang / Xiapu Luo、ASE 2023、pp.939–950、DOI 10.1109/ASE56229.2023.00188|査読会議。abstractと§V-A/B、§VIの該当箇所|runtime stateをlocals/stack/memory/globals/tableで比較。tableはsizeのみ、参照値は比較せず、arithmetic NaNをcanonicalize。7 runtimesの21 bugs、8確認という著者報告|包括的state oracleは既存。Kのtable identity/segment観測はこの読んだmodelにないが、WADIFF実装全体の能力不足と同一視しない。今回未実行|
|[StackArmor](https://www.ndss-symposium.org/wp-content/uploads/2017/09/05_2_2.pdf)、Xi Chen / Asia Slowinska / Dennis Andriesse / Herbert Bos / Cristiano Giuffrida、NDSS 2015|査読会議。abstract、§III-B definite assignment、related work該当箇所|binaryのbyte単位のwrite-before-read解析で初期化を省く|Lの単純なmust-overwrite reset省略は既知原理に近い。このまま新案として実装する価値は弱い|
|[Automatic Verification of Intermittent Systems](https://www.cse.iitd.ac.in/~dahiya/vmcai18.pdf)、Manjeet Dahiya / Sorav Bansal、VMCAI 2018|査読会議。abstractとIntroduction pp.1–3のみ|連続実行と断続実行のequivalenceを検査し、checkpoint stateの縮小にも利用する。一般に完全なsnapshotを要件としない|再実行を含む意味保存や必要stateの検討自体は既存。Wasm固有機能を扱う部分との違いを追加説明する必要がある|
|[Towards a Formal Foundation of Intermittent Computing](https://msurbatovich.github.io/assets/docs/surbatovich_oopsla20.pdf)、Milijana Surbatovich / Brandon Lucia / Limin Jia、PACMPL 4 OOPSLA, Article 163, 2020、DOI 10.1145/3428231|査読論文。abstractとIntroduction pp.1–2のみ|断続実行のmemory consistencyと入力に関する正当性を定式化|「再実行があるためstate一致と観測同値が違う」という一般論をK独自にしない。全形式化は今回未読|
|[Checkpoint-Restart-Verify — a methodology and tool to facilitate experimentation with program sections](https://udspace.udel.edu/bitstreams/666ab38e-d176-4290-a8db-3acf643ebee5/download)、Ahmed Jalal Al Tamimi、University of Delaware、2022|修士学位論文。査読会議論文と区別。abstractと§2.3 live-variable analysis、Introduction該当箇所|Cの部分処理を保存状態から再開し、変更前後のstate比較に使う。必要stateの説明にlive-in/live-out解析を用いる|state比較やdef-use解析をcheckpoint検査へ適用すること自体は新規でない。Wasmのsegment差・API列の評価との詳細対応は未完。今回未実行|
|[Wasm3 snapshot testing](https://github.com/wasm3/wasm3/tree/28ecb9af6d2040e474a70f7cb7f43666740141fb)、Wasm3 contributors、commit 2026-09-29|公開実装。docs/Testing.md、extra/pause-points.py、snapshot runnerの主要箇所、format runnerのsegment/多段再開箇所。実行していない|命令列から入口・call・back-edgeの中断点を列挙する。異なるslot幅等のbuildで交互に復元し、stdoutを継続実行と比較。format検査ではsegment flagの不正値も検査|自動中断点列挙、複数実装での再開試験、state形式検査も既存。元API観測の限定classifierとは対象が違うが、広いテスト自動化の新規性には反証となる|

検索語には `WebAssembly snapshot state equivalence`, `WebAssembly zero-length probe`, `Wasm restore oracle differential testing`, `WebAssembly snapshot passive segments`, `secure memory reuse initialization static analysis` 等を使った。検索で同名方式が出ないことを未発表の証明にはしない。特許検索の継続は現在の目的から外した。

条件合成の追加比較：

|資料|読了範囲・既存の提案|今回との関係|
|---|---|---|
|[A Self-Certifying Compilation Framework for WebAssembly](https://antonxue.github.io/files/papers/namjoshi2021self.pdf)、Kedar S. Namjoshi / Anton Xue、VMCAI 2021、DOI 10.1007/978-3-030-67067-2_7|査読論文。abstract、§1、§3–4。変換ごとの関係witnessを生成し、独立validatorで正当性を確認する。trapと観測を含む|Wasmの状態関係を検証する原理は先行。Kの有限bulk API・segment寿命・trap後の再呼出しという契約との差に限定する。今回実装を実行していない|
|[Weakest Precondition Synthesis for Compiler Optimizations](https://web.ist.utl.pt/nuno.lopes/pubs/psyco-vmcai14.pdf)、Nuno P. Lopes / José Monteiro、VMCAI 2014|査読論文。abstract、Introduction、§2の前提言語とtrapの扱い。有限の前提言語で条件を反例駆動合成するPSyCO|自動前提合成は既知。copy/constant条件を生成したこと自体では新規性を主張できない。全文・実装評価は未読/未実行|
|[Symbolic Register Automata](https://matteosammartino.com/assets/pdf/cav19.pdf)、Loris D'Antoni / Tiago Ferreira / Matteo Sammartino / Alexandra Silva、CAV 2019|査読論文。abstract、Introduction、モデル定義、検索で得たsymbolic bisimulation節。register対応の記号的関係で同値性等を扱う|記号的な等式と有限control stateの組合せは既知。今回の有限byte-domain、bulk update、API観測契約とは詳細対応が必要|

[LWDIFF](https://discovery.ucl.ac.uk/id/eprint/10222953/)（Shiyao Zhouほか、ICSE 2025、DOI 10.1109/ICSE55347.2025.00233）は大学公開abstract/metadataのみ確認。LLMが仕様から取り出した知識をmutationへ使い、decode/validate/executeを試験する。大学abstractは8 runtimesで31 bugs、25新規と報告する。PDFは開けたが本文の評価節はまだ読んでおらず、Kの詳細oracleとの比較済み資料に数えない。

残り得る研究上の差は、既存moduleへ非破壊の観測を生成し、reset境界のstate分類と元APIの反例を区別する一体の評価手順である。しかしこれは**現段階では検証手法の仮説**であり、一般的なconformance testingや既存checkpoint testに対する十分な優位は未実証。公開wasm-migrateでの反例、Weaveでの正常復元を実測できたことと、検査原理の新規性を分ける。新しい難読化・復元アルゴリズムの成功として数えない。

追加の[元API分類](context-results.md)は通常のdef-useと有限状態対の遷移閉包を使う。16同一観測/2反例という実測上の区別は得たが、bisimulationや状態の観測同値を新原理と主張しない。WESTの全文は大学metadata・会議・DOI・公開検索から取得できず、内部oracleを未読のまま比較しない。Wasm3取得sourceのhashは `.tools/wasm3-snapshot-review/provenance.json` に保存した。

追加資料：[Wasm-R3: Record-Reduce-Replay for Realistic and Standalone WebAssembly Benchmarks](https://dlehmann.eu/publications/Wasm-R3-oopsla2024.pdf)、Doehyun Baek / Jakob Getz / Yusung Sim / Daniel Lehmann / Ben L. Titzer / Sukyoung Ryu / Michael Pradel、PACMPL 8 OOPSLA2 Article 347 (2024)、DOI 10.1145/3689787。査読論文。abstract、Introduction、§5.2、§6、READMEのbenchmark/test説明を読んだ。hostとの相互作用を記録して単独replay moduleへ変換し、著者は43 web app中27でreplayを生成したと報告する。Kの新方式ではなく、[追加実験](r3-results.md)のデータ供給元である。記録/replayの正しさ・shadow state比較・参照の対応付けも既存技術に含まれるため、その一般原理を本研究の新規性とはしない。

追加資料：[Execution-Aware Program Reduction for WebAssembly via Record and Replay](https://software-lab.org/publications/ase2025_RR-Reduce.pdf)、Doehyun Baek / Daniel Lehmann / Ben L. Titzer / Sukyoung Ryu / Michael Pradel、ASE 2025。[著者repository](https://github.com/sola-st/rr-reduce)で会議版と実装を確認。検索サービスが返したabstract/IntroductionとREADMEのみを読んだ。PDF直接openはtimeoutのため全文未読。実行を記録してbug-triggering functionを切り出すRR-Reduceと、既存縮約を合わせるHybrid-Reduceを提案する。28 programで評価したとの著者報告で、今回再実行していない。Kは縮約器ではなく、実行差から判定する一般的手法の新規性を主張しない。

2026-10-24の追加検索：`WEST Specification-Based Test Generation WebAssembly Youn Shin Ryu pdf 2025`、`RR-Reduce record replay wasm test reduction Lehmann 2025 pdf`、`WebAssembly checkpoint restore observational equivalence testing state oracle`。WESTの全文は引き続き未取得。大学のabstract以上の詳細差分は保留する。

## 条件合成と反例抽出の追加照合

2026-10-24。`WebAssembly weakest precondition`、`WebAssembly observational equivalence verification`、`WebAssembly checkpoint verification paper`を再検索した。一般的なWP、trapを値として扱う論理、固定位置のtableの変数化も既知である。以下は実行比較ではなく文献比較である。

|資料|種別・読んだ範囲|確認事項とKへの反証|
|---|---|---|
|[Iris-Wasm: Robust and Modular Verification of WebAssembly Programs](https://iris-project.org/pdfs/2023-pldi-iris-wasm.pdf)、Xiaojia Rao / Aïna Linn Georges / Maxime Legoupil / Conrad Watt / Jean Pichon-Pharabod / Philippa Gardner / Lars Birkedal、PACMPL 7 PLDI Article151、2023、DOI10.1145/3591265|査読論文。abstract、§1、§2.1–2.2の該当箇所、[公開実装README](https://github.com/logsem/iriswasm)。実装未実行|Wasm1.0の高階分離論理とhost側を含む合成、trapを含むlogical valueを機械化する。再入・table更新の例も既存。Kは証明能力の一般的拡張を主張できない。限定bulk profileの自動条件・反例抽出が対象差候補|
|[CHC-based Automated Verification of WebAssembly Programs](https://arxiv.org/html/2607.17220v1)、Akihisa Yagi / Ken Sakayori / Naoki Kobayashi、2026、arXiv2607.17220v1、DOI10.48550/arXiv.2607.17220|プレプリント。著者metadataはHCVS26発表と記載、査読状況を別途確認していない。abstract、§1–2、§3.1/3.3、§4–5を読んだ。実装未実行|WasmをCHCへ変換し、型による間接call候補削減とpanic handler簡約を行う。固定indexのtableを有限変数化する最適化もある。§2はmemory境界trapを省略し、§4の簡約はtrap到達性の契約。Kのtrap前store保持・trap後API契約へそのまま適用できるとは言えない。著者評価は90例中Spacer56判定、22timeout、12false alarm。今回の再現値ではない|
|[A Checkpoint/Restore Mechanism with Interoperability Among Distinctive WebAssembly Interpreters](https://apsys2024.github.io/posters/apsys24posters-final73.pdf)、Daigo Fujii / Katsuya Matsubara / Yuki Nakata、APSys2024 poster|1ページposter全文。通常の長編査読論文と区別、選考方式未確認|WasmEdge/WAMR/Wasm3間の命令位置対応と型情報を用いたvalue stack変換を示す。状態表現の対応付けをK独自とはしない。定量評価表はこのposterにない。今回実装未実行|

[Formal Reasoning about WebAssembly and Extensions](https://cs.au.dk/~birke/phd-students/LegoupilM-thesis.pdf)（Maxime Robert Sébastien Legoupil、Aarhus大学博士論文、2025-09-30）もabstractと§1.3/Chapter2の関連箇所を確認した。Iris-Wasmとその拡張をまとめた学位論文であり、一般的なWPやhost相互作用の形式化を本研究の新規性としない。全196ページを読了したとはしない。

最短反例抽出については、固定点の不成立理由を逆にたどる通常のモデル検査の構成を使っている。[実測](guard-witness-results.md)でも重複状態を除く具体BFSと比較し、BFSでも同じ最短長が得られた。反例生成を新しい一般探索原理とする余地はなく、条件合成と実Wasmの復元診断を接続する限定的な貢献として残す。

## API利用契約の先行性

2026-10-24。Weaveの公開driverがtrap後の再入を拒否することを受け、protocol制約を追加照合した。

|資料|読んだ範囲|今回との関係|
|---|---|---|
|Luca de Alfaro / Thomas A. Henzinger, [Interface Automata](https://web.cs.wpi.edu/~heineman/html/teaching_/CS562/p109-de_alfaro.pdf), ESEC/FSE2001, pp109–120, DOI10.1145/503209.503226|査読論文、abstractとIntroduction（PDF1–2頁）、[著者所属機関metadata](https://research-explorer.ista.ac.at/record/4622)。全評価・証明の読了ではない|呼出し順序の環境仮定、返値・例外、許されない入力を既に扱う。trap後の呼出し可否をFSMで制限する一般原理は新規でない|
|Shawn Meier / Sergio Mover / Bor-Yuh Evan Chang, [Lifestate: Event-Driven Protocols and Callback Control Flow (Extended Version)](https://arxiv.org/abs/1906.04924), 2019, arXiv1906.04924v2|プレプリントabstractのみ。関連ECOOP2019 DOI10.4230/LIPIcs.ECOOP.2019.4はmetadataで確認、査読版本文未読|lifecycleとtypestateを組み合わせ、許されるAPI traceと反例の実現可能性を扱う。一般的protocol-aware診断をK独自とする根拠はない|

現行[Core仕様](https://webassembly.github.io/spec/core/bikeshed/)の実行規約は、trapで当該計算を中止しても別の計算を後から開始できると明記する。WeaveのJS driverの終端方針はcore意味論とは別のhost契約であり、片方を他方の不具合と扱わない。固定版`js/weave.mjs`のdrive/init/failed遷移を読み、[実行でも確認](guard-external-results.md)した。

WESTの全文も研究室の[公開文献一覧](https://plrg.kaist.ac.kr/research/publications)から再探索したが、今回読めたリンクはDOIへの参照で、本文取得には至らなかった。既存のabstractのみという読了区分を維持する。

[Whiskの固定ソース比較](whisk-review.md)を追加した。README、利用説明、proof/state型、full evaluatorの関連箇所を確認した。著者実装は未実行。一方で、比較課題を具体stateの到達可能性に合わせた[標準CHC/Spacerの実行](guard-chc-results.md)は行った。これは自作encoderであり、先行論文の再現結果と混同しない。

## Snapshot再利用の追加照合

2026-10-24。`WebAssembly checkpoint restore passive segments snapshot equivalence testing state observability`、`program reset synthesis observational equivalence selective state restoration checkpoint`等で再検索した。

|資料・書誌|読了範囲と提案|評価・今回への影響|
|---|---|---|
|Dinghong Zhong / Alexander Y. Bai / Mikail Khan / Guannan Wei, **Compiling WebAssembly Concolic Execution with Staging, Continuations, and Snapshots**, OOPSLA2026、[DOI10.1145/3839498](https://doi.org/10.1145/3839498)|[公式会議掲載](https://2026.splashcon.org/details/oopsla-2026/124/Compiling-WebAssembly-Concolic-Execution-with-Staging-Continuations-and-Snapshots)で査読会議とDOIを確認。読んだ本文は[arXiv2608.18327v2](https://arxiv.org/html/2608.18327v2)のabstract/Introduction、§5–7のsnapshot・外部call・対応機能、§8のsetupと結果の一部。全証明の読了ではない|GenWasymはCPSとstagingによるconcolic compiler。184 benchmarkでWASP比29.4倍、heuristic reuseで44.9倍という著者報告。外部callがあるprefixのsnapshot再利用を保守的に禁止し、symbolic modelの統合を今後の課題とする。§7.2はimports/exports・funcref等を未対応と記す。Kは一般concolic engineではなく、この研究との能力/速度直接比較は未実施。host summaryを使うだけで独自原理とはしない|
|Marco Guarnieri / Petar Tsankov / Tristan Buchs / Mohammad Torabi Dashti / David Basin, **Test Execution Checkpointing for Web Applications**, ISSTA2017、[DOI10.1145/3092703.3092710](https://doi.org/10.1145/3092703.3092710)|査読論文。[著者PDF](https://mguarnieri.github.io/publication/issta2017/issta2017.pdf)のabstract/Introduction/§2を読んだ。test間をcheckpointで隔離し、共通prefixの再実行を省く|PHP5アプリで平均44%のtest時間短縮という著者報告、今回未再現。snapshotをtest隔離と組み合わせる一般的発想は先行。任意のclient/Wasm/host状態を扱う結果ではない|

GenWasymのartifact metadataは約915.6 MBのarchiveを示すが、本体を取得・実行していない。未対応機能をKの誤検出率や性能の優位へ換算しない。本文と会議書誌を区別し、arXivの古いv1に残る会議名placeholderを正式発表先として引用しない。

## 関係論理・effect/frameによる追加反証

2026-10-24。`relational verification havoc frame agreement equality abstract interpretation counterexample generation`、`relational Hoare logic partial updates agreement variables havoc`等で、直接反例構成の既知原理との重なりを調べた。

|資料・書誌|種別・読んだ範囲|Kとの重なりと限界|
|---|---|---|
|Anindya Banerjee / David A. Naumann / Mohammad Nikouei, **Relational Logic with Framing and Hypotheses**, FSTTCS2016、[DOI10.4230/LIPIcs.FSTTCS.2016.11](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.FSTTCS.2016.11)|査読会議論文。公式metadata、PDF abstract、§1–2、§3冒頭を読んだ。全証明未読|実行対のalignment、関係specification付き手続き、read/write frame conditionを扱う。理論と例が中心で、今回読んだ部分にはKと比較可能な速度表はない。host効果を関係条件で扱う大枠はK独自でない。一方、Kの限定mask閉包/N+1代入基底そのものを同論文が提示するとまでは確認していない|
|Anindya Banerjee / Ramana Nagasamudram / David A. Naumann / Mohammad Nikouei, **A Relational Program Logic with Data Abstraction and Dynamic Framing**, ACM TOPLAS44(4) Article25、[DOI10.1145/3551497](https://doi.org/10.1145/3551497)|査読journal。[著者所属機関](https://researchwith.stevens.edu/en/publications/a-relational-program-logic-with-data-abstraction-and-dynamic-fram/)は公開日2023-01-10/©2022と記載。読んだ本文は[arXiv v6、2022-07-19](https://arxiv.org/pdf/1910.14560v6)のabstract、§8.5–8.6、§9の該当箇所。HTMLは取得サイズ超過、PDFで部分確認。全138頁読了ではない|WhyRelはWhy3経由のSMT検証で、利用者がspec・biprogram等を与えるauto-active方式。union-findや優先queueを使う例を報告。Kは制限した自動条件/反例出力が対象だが、関係検証能力が一般に優れるという意味ではない。著者実装未実行、性能直接比較なし|

**Constraint-based Relational Verification**（Hiroshi Unno / Tachio Terauchi / Eric Koskinen、[arXiv2106.02628v1](https://arxiv.org/abs/2106.02628)、2021）は今回abstractのみを確認した。CHCを一般化した制約とalignment推論を扱うとの記述で、詳細比較済み資料には数えない。会議書誌や性能をabstractから補完しない。

今回の二値候補は本repositoryのAPI間host-write版にも既に存在する。したがって直接構成を新発明として数え直さない。部分書込みの閉包と組み合わせた限定構成の明文化・実装・再生は成果物だが、検索で同一式を見付けなかったことを新規性の証明にはしない。

Thomas Reps / Susan Horwitz / Mooly Sagiv, **Precise Interprocedural Dataflow Analysis via Graph Reachability**, POPL1995、[DOI10.1145/199448.199462](https://doi.org/10.1145/199448.199462)も追加確認した。査読会議論文。[著者所属大学のPDF](https://pages.cs.wisc.edu/~fischer/cs701.f14/popl95.pdf)のabstract、§1、§2冒頭を読んだ。有限factと分配的flow関数を満たす問題をgraph reachabilityとして解き、Cでpossibly-uninitialized variable解析の予備実験を報告する。全評価節・全証明は未読、著者実装未実行。Kの[atom worklist比較](guard-import-worklist-results.md)は既知の分配的計算を用い、同論文の手続き間valid-path算法の再現とはしない。計算順の変更を新しい解析原理と扱わない。
