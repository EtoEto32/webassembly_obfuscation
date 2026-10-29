# 修士研究としての差分と未確立部分

**2026-10-25更新**：[厳格な採否判断](masters-verdict-20261025.md)では、現状のKを新しい解析アルゴリズムの主テーマとして推奨しない。ESOP2005の等式WPに直接近い規則を確認し、[別backend](guard-herbrand-results.md)が404契約の全状態条件を一致させ、人工chainでK worklistより約1.5–3.7倍速かった。K固有の解析能力・速度優位という根拠は残らなかった。[ffmpegの実処理](ffmpeg-workload-results.md)と[Wizerの公式CLI](wizer-comparison-results.md)も追加したが、契約依存診断が自然な用途の判断を改善する証拠は未達である。以下の履歴を「新規性を確認済み」と読まない。

**最新の厳しい判定**：[ffmpeg.wasmの目的抽出](post-start-results.md)で自然なdropを7,320個発見したが、全てstart専用readerに対応し、起動後には寿命差が観測できない十分条件を満たした。Kが必要な自然な用途の不足は解消していない。[一般SMTの実装改善](guard-import-generic-results.md)でも全条件が一致し、人工read-chainの速度差は約8–23倍へ縮んだ。Kは実装・診断・限定した性能結果のある候補として保持するが、主題の新規性と実用性を確立済みとは判定しない。

[同じ出力課題での比較](guard-import-generic-results.md)でも、自作の一般SMT WP/QEが全256契約と遅延chain8条件で同じ初期条件を生成した。Kだけが条件を出せるという主張は棄却する。人工的なreadありchainではKが約25–34倍速かったが、既知等式処理への特化の効果で、先行最良実装や自然なアプリに対する一般的優位ではない。

[自然な用途の追加調査](coverage-results.md)では、取得済み実アプリ由来243 file中242本を完全に静的解析したが、明示的なsegment dropは0本だった。R3の10本にはmemory.initがあった。これはKの一般的実用性を支持する結果ではなく、主張を限定する反証である。既存手法との差分候補があることと、修士研究の主成果として十分であることは、引き続き別問題とする。

[同期import境界の条件合成](guard-import-results.md)を追加し、host trace・read・writeの位置を含む限定profileを実装した。256契約の別array検査と具体BFSは一致し、後者も全1,024初期storeを解けた。差分候補は具体的な診断出力と適用境界であり、一般的なhost合成、data independence、WPを新原理とはしない。

[StateFork (2026-09プレプリント)](https://arxiv.org/html/2609.38648v1)の§2.2も、将来の許された操作に対する観測同値を復元契約として明記する。したがって「全bit一致ではなく観測を基準にする」自体を新規性として使わない。WASCII/ISSTA2026とcross-ISA AOT復元/MPLR2025も[文献表](prior-art.md)へ追加した。前者二つの会議論文はabstract/metadata以上の比較を済ませたとしない。

最新追補：[host書込みを許す条件合成](guard-environment-results.md)を実装した。全ての共通初期storeで閉じたAPIが一致する場合でも、途中の公開書込みで差が出る例を示し、初期条件だけの環境閉包では不十分と分かった。固定点の各寿命状態対で閉包を計算する必要がある。ただし環境遷移・普遍量化・二項不変条件は既知であり、独立した新しい一般原理ではない。新しい576具体状態queryもSpacerが全て解けた。研究上の差分候補は、Wasmの復元差と利用契約に特化した条件・最短交互反例・実対象での切分けである。

[例外tagによる権限封印などの別案](alternative-screening.md)も検査したが、Wasm仕様自身にfresh tagとpayload非公開が記述されている。直接の仕様利用を新発明に数えず、主案へ昇格しなかった。

2026-10-24。特許性を判定する資料ではない。**実装・反例・条件合成という研究成果候補はあるが、既存研究にない強いアルゴリズム原理を確立したとは言えない。**

|構成|最近接の既知技術|今回残る差分候補|証拠と弱点|
|---|---|---|---|
|Jの論理stateによる再初期化|Weaveの容量/境界/segment寿命のvirtualization|同一instance resetの特定運用|主要原理が重なり主案から降格。poolingより遅い条件もある|
|Kのfull state observer|Wasm公式test、WADIFFのstate差分、Weaveの復元test|復元契約ごとにstate差を分類する生成器と評価|実装・外部再現はある。0長probeやstate比較は既知|
|API継続による分類|def-use、bisimulation、有限モデル検査|segmentだけの残存差を元APIの同一観測/反例/保留へ分類|18実測差で16同一観測/2反例。元programのguest stateに限る|
|記号的memory/table条件合成|predicate transformer、等式抽象、PSyCO、register automata、Wasm関係検証|trap後の再呼出しを含む限定bulk APIについて具体stateを超えた条件を出す|table拡張で公式67対中55対を受理。array式での帰納義務124件を検査。実アプリの自然なdrop利用は未評価|
|条件不成立からの最短store反例|固定点モデル検査、幅優先探索|同じ限定bulk modelで肯定条件と否定反例をつなぐ診断|393列を2engineで再現、具体BFSと最短長一致。元API/公開memory差330、追加観測だけ63。新しい探索原理ではない|
|復元変換とのobserver合成|参照registry、representation mapping|wrapperによる検査器の誤診を切り分ける具体対照|10 replayで検査可能。directory自体の相関破損を見逃す限界も実証|

## 主張できる候補

追加した[may-writeの契約](guard-import-may-results.md)では、必須全上書きと任意subsetを区別する限定等式閉包と実行対照を得た。旧128対応契約だけでは両者の取り違えを検出できず、2-importの別対照で初めて判定差が出た。これは契約境界の検証材料だが、may/must effectや一般的環境WPを発明したという主張にはしない。一般SMTも新128契約と2対照を同じ条件で解いた。

「Wasmの復元評価において、内部状態一致、元APIの具体反例、限定API列の同一観測、state依存の同一観測条件を分ける方法と実証」は、修士研究として検討できる。新しい一般的な同値判定原理や最強の復元器を主張する必要はない。一方、既知部品を実装して並べただけとの反論に答えるには、契約の違いが判断を変える実例と、その分類に各段階が必要な理由を論文の中心に置く必要がある。

最近接の[A Self-Certifying Compilation Framework for WebAssembly](https://antonxue.github.io/files/papers/namjoshi2021self.pdf)は変換器が生成する関係witnessを独立validatorで検査する。Wasm状態関係とtrapの検査そのものは先行する。今回の対象はsegment寿命が異なる二つのstoreと、trap後も再呼出しできる元APIの契約である。異なる対象に同じ検証原理を適用しただけとの反論は残る。

[PSyCO](https://web.ist.utl.pt/nuno.lopes/pubs/psyco-vmcai14.pdf)は前提条件合成を、[Symbolic Register Automata](https://matteosammartino.com/assets/pdf/cav19.pdf)は記号的な同値関係を既に扱う。copy写像と等式の固定点を使ったこと自体を新規と扱わない。

## 採否

[ffmpeg-mt実binaryの制御変種](post-start-live-results.md)で、7,320寿命差と同じ1 GiB memoryを2engineで実測した。これは内部差を元API不具合数へ換算できないという評価上の対照で、自然な復元bugでも、独自の解析原理でもない。元API実行0という動的範囲も明記する。

[既知worklistへの置換](guard-import-worklist-results.md)も400契約で同じ全状態条件を出した。反例rankを保存しない同士の条件生成比較で、96 cellの三条件は全反復比約8.4–8.7倍、小caseでは遅かった。分配的WPと増分伝播の応用であり、Kの独立した一般解析能力を示す結果ではない。

[直接反例構成](guard-import-direct-results.md)を追加した。280小caseではSMT反例生成比37.8倍だが、共通前処理を加えた概算は約1.3倍である。最大97 APIの12反例も両engineで再生した。二値代入基底は既存のAPI間書込み版と共通で、関係論理のeffect/frameも先行する。これは限定モデルに対する実装の改善であり、別原理の発明や自然なアプリでの有効性の証拠にはしない。

追加の[GenWasym/OOPSLA2026との照合](prior-art.md)でも、snapshot再利用・symbolic状態・外部callの健全性という問題設定は先行する。Kは有限bulk APIの二状態条件を出す別の課題だが、hostをsummaryで扱ったことだけを新しい原理とは主張できない。著者実装との直接比較は未実施である。

Kは**実証を伴う修士研究候補として保持**する。独創的な難読化/復元アルゴリズムが発明できたという結論にはしない。異なる契約を採る既存研究を誤りと断定せず、その契約内では正しい判定と、適用範囲外を分ける。新規性の不足を、実行回数、方式の名前、資料の量で埋めない。

次の優先事項は、記号的条件合成の制限を明示した直接比較と、既知の意味論に対する独立性の確認である。全文未取得のWESTを詳細比較済みとしない。外部実装の反例は作者確認なしで、実製品の脆弱性件数へ読み替えない。

## 追加の厳しい比較

[Iris-Wasm](https://iris-project.org/pdfs/2023-pldi-iris-wasm.pdf)はWasm1.0のtrapをlogical valueとして含む高階WPとhost合成を既に機械化している。[WasmVerifierの2026年プレプリント](https://arxiv.org/html/2607.17220v1)は固定index tableの有限変数化も記述する。したがって「Wasmのtrapやtableを記号的に扱った」は新規性の主張に使えない。

Kで残る対象差は、復元後にsegmentだけが異なる二つのstoreについて、同じ任意API列を実行し、各return/trap時のstore一致条件を自動で出す限定問題である。Iris-Wasmはより広い論理を人が利用して証明する研究、WasmVerifierはtrap到達性の安全検証であり、対象・自動化・観測契約が異なる。ただし、対象差が論文として十分かは未確定で、両実装との同一課題での直接実行比較はしていない。

[反例生成](guard-witness-results.md)は深さ4を超える例を解けたが、既存の具体BFSも解けた。高速性を主貢献とせず、任意初期storeの条件と診断結果の説明可能性を優先する。次に測るべきは、準備費用を含む性能と、状態数上限で保留になる境界である。

その後の[性能比較](guard-cost-results.md)では、深い反例の異なる32storeをまとめる分布では準備込みで速くなる一方、単一store・繰返し・一様乱数ではBFSが優位だった。無関係なsegment状態で上限に達する弱点は[既知の依存関係削減](guard-projection-results.md)で改善した。いずれも新しい一般原理の根拠にはしない。

[観測範囲の自己監査](guard-observation-audit.md)で、393列のうち63列は追加observerだけのprivate store差で、元関数APIは同一と分かった。これらを公開API不具合とする解釈を撤回した。修士研究としての貢献候補は、むしろこのように契約によって診断結果を分離し、数値と根拠を追跡可能にする点である。

この区別を手作業の分類に留めず、[契約別の二つのstoreの条件合成](guard-contract-results.md)へ実装した。中間のprivate state差を残したまま追跡し、segment寿命が揃ってから公開resourceへ差が伝わる反例も扱う。一般的な二項関係解析は既知だが、従来実装の単一共通store・早期打切りが不十分になる理由を、反例と別array式で示した。8本の元binaryだけの実行でも公開差と修復対照が整合した。現段階の技術的貢献候補は、この限定bulk問題の条件合成・契約別診断と実証である。

[実復元器への追加適用](guard-external-results.md)でも、復元entryの結果が一致する一方、後続公開操作で差が出る4条件をwasm-migrateの実験host上で得た。ただし作者の再入保証は未確認である。Weaveの公開JS driverはtrap後にfailedとなるため、同じ反例列は利用契約外になる。この差を無視した製品比較は不適切である。

そこで[trap終端/再入の選択](guard-protocol-results.md)を実装したが、Interface AutomataやLifestateがAPI環境仮定を既に扱う。さらにterminal/returnsの限定profileでは、固定点計算を使わない[一回判定](guard-terminal-lemma.md)で十分になる。147module/7,536寿命対が汎用版と一致し、単純手法で足りる範囲を明確にした。これも狭い命題と実装上の簡約であり、強い新原理を発明したとは結論しない。

修士研究として残す中心課題は「復元差に対し、観測範囲とhost利用契約を指定した条件・反例を作り、診断が変わる境界を実証する」である。先行検証器との直接比較、自然な実アプリでの寿命差、Wasm意味論からの証明が未完であり、研究テーマとしての独立した新規性を確立済みとはしない。

[Whiskの公開ソース](whisk-review.md)で関係certificate・trap・SMT検査の先行性を確認した。本体は必要なOCaml環境がなく未実行である。一方、[自作の標準CHC符号化とSpacer](guard-chc-results.md)では同じ具体状態の全156queryを判定でき、Kと一致した。「汎用手法では解けない」という優位は反証された。残る条件合成・最短反例という出力差も既知技術の特化であり、単に比較対象を狭めて新規性を主張しない。
