# webassembly_obfuscation

**2026-10-27 引き継ぎ:** 最新の研究状態・未完了事項・clone後の実験成果物復元は [HANDOFF.md](HANDOFF.md) を参照してください。以下の進捗は履歴を含みます。

2026-10-24追補19：[実配布ffmpeg-mtの制御変種](research/state-witness/post-start-live-results.md)で、起動時drop省略による7,320寿命差と同じ1 GiB memory hashをNode/Wasmtimeで確認した。元API実行は0で、動画変換の追試・自然な復元bugではない。起動後に差を読めないという判断は静的到達条件による。内部差とアプリ不具合を分ける対照を追加し、**強いアルゴリズム新規性と自然な有効例は引き続き未確立**とする。

2026-10-24追補18：[直接反例構成](research/state-witness/guard-import-direct-results.md)を実装し、280小caseと最大97 APIの12反例を2engineで再生した。生成部分は自作SMT比37.8倍だが、共通前処理込み概算は約1.3倍。[既知worklistとの比較](research/state-witness/guard-import-worklist-results.md)も400契約で同じ条件を出した。**新しい一般解析原理の確立とはせず、修士研究としての主題の独自性と自然な用途は未達**という判定を維持する。[package v3](artifacts/state-witness-import-v3.zip)は79 binary fileの同一bytesでの再生成を新directoryで検査済み。[現在の研究判断](research/state-witness/status.md)。

2026-10-24追補17：[現在の研究判断](research/state-witness/status.md)。hostの必須上書きと任意部分書込みを区別し、既存試験群では出なかった契約差を2-import対照で確認した。32反例を2engineで再生。[再現package v2](artifacts/state-witness-import-v2.zip)は57 binary fileの同一bytes生成を新directoryで検査済み。**Jの先行技術との差は弱く、Kも修士研究の主成果としての独自性・自然な用途は未確立**という判定を維持する。

2026-10-24追補16：[同じ初期条件を生成する一般SMT対照](research/state-witness/guard-import-generic-results.md)も全256契約・8chainを解いた。一般対照を改善すると、Kの人工例での速度差は約8–23倍へ縮んだ。[ffmpeg.wasmの固定2標本](research/state-witness/post-start-results.md)では、core-mtに7,320 dropがある一方、そのreaderは起動後APIから到達不能だった。**Kの実装と限定した効果はあるが、強い新規性と自然な実用例の確立は未達。** [import解析の再現zip](artifacts/state-witness-import-v1.zip)は39 binaryの同一bytesでの生成と2engine検査を別directoryで再現済み。

2026-10-24追補15：[同期void importを含む条件合成](research/state-witness/guard-import-results.md)を実装。256契約をNode/Wasmtime、1,164のarray義務、具体BFSで検査し、実復元fixtureの指定継続部分にも適用した。一方、[実アプリ由来242本の静的全走査](research/state-witness/coverage-results.md)では明示的segment dropがなく、自然な用途での有効性は未実証。強い新規性や一般的実用性が確立したとはしない。[小さな再現package](artifacts/state-witness-minimal-v1.zip)は公開host書込みの小対照を新directoryで再現済み（後のimport拡張は含まない）。

2026-10-24追補14：[公開storeへのhost書込みを含む条件合成](research/state-witness/guard-environment-results.md)を実装した。初期条件が無条件一致でも、guest呼出しとhost書込みを交互にすると差が出る元APIの反例を2engineで確認。混合96 module・576契約では339初期storeの判定が変わった。公開復元器でも、復元直後のmemoryは同じなのにhost書込み後だけ公開差が出るサイズ対照を再現した。一方、汎用Spacerも576具体状態queryを全て解けており、**一般的な新検証原理の発明とはしない**。[統合CLI](research/state-witness/quickstart.md)は`--host-writes`で契約を選べる。特許目的は終了し、修士研究の限定した新規性と適用境界を検証中。

2026-10-24追補13：[観測範囲とtrap後の利用契約を指定する診断CLI](research/state-witness/quickstart.md)を追加した。実復元後に最大33呼出しで現れる公開差を確認した一方、Weaveの公開driverではtrap後再入が未対応と分かり、[契約別に再評価](research/state-witness/guard-protocol-results.md)した。同じ78初期状態で差21件が13件へ変わった。限定terminal/returnsでは固定点なしの一回判定と全7,536寿命対で一致する簡約も得た。**修士研究向けの条件合成・反例・適用境界の実証として継続し、新しい一般検証原理を確立したとはしない。**

2026-10-24追補12：[条件合成をtableへ拡張](research/state-witness/guard-table-results.md)し、公式67状態対中55対を受理。[最短API反例の抽出](research/state-witness/guard-witness-results.md)では393列をNode/Wasmtimeで再現した。既存の具体BFSでも同じ最短長を得られ、一般探索原理の新規性とはしない。[日本語草稿](research/state-witness/paper-draft.md)を観測契約・条件合成・反例診断を中心に更新した。Iris-Wasmと2026年のCHC検証論文も[再照合](research/state-witness/prior-art.md)し、修士研究として残る対象差と未確立部分を明示している。

追補12の観測範囲を[訂正・監査](research/state-witness/guard-observation-audit.md)：393列は全store契約に対する反例で、元return/trap差96、元公開memory差234、追加observerだけのprivate store差63。最後の63は元関数APIでは区別できず、公開API不具合とは数えない。[費用比較](research/state-witness/guard-cost-results.md)と[状態数削減](research/state-witness/guard-projection-results.md)も保存した。

2026-10-24追補11：[記号的メモリ条件の合成](research/state-witness/guard-results.md)を実装。異なるtrap位置でもAPI観測が同じになる条件を、具体memory一例から等式条件へ一般化した。23条件・53のSMT検証義務を確認し、弱めた14対照を棄却。Node/Wasmtimeの実行照合も保存した。[新規性の判断](research/state-witness/novelty-analysis.md)では、既知の関係検証・条件合成との差を限定し、強い新原理の確立とはしていない。

2026-10-24追補10：現在の目的は修士研究。[固定した分類器の追加評価](research/state-witness/disjoint-results.md)では67状態対を41同一観測・14API反例・12未対応へ分類した。[実アプリreplayとWeaveの比較](research/state-witness/r3-weave-results.md)も追加し、通常20・復元16条件で一致、4条件は中断未到達。observer自身の参照照合の合成失敗と信頼前提も[反証実験](research/state-witness/composition-results.md)で明確にした。既知の検査原理を超える強い新アルゴリズムの成立は未確認であり、実験件数を新規性の根拠にしない。

2026-10-24追補9：[復元状態差の元APIでの分類](research/state-witness/context-results.md)。18回のsegmentだけの差について、14回は保守的な解析条件を確認、残る4回のうち2回は同じmemoryへ書いた後のtrapで差が消えることを確認した。元programの限定APIモデルでは16同一観測・2反例となり、Node/Wasmtimeで一致した。新規な復元原理の確立ではなく、契約によって評価の結論が変わる実証成果として保存した。現在の目的は修士研究である。

2026-10-24追補8：[Kの外部実装比較](research/state-witness/README.md)を進めた。公開wasm-migrateとWeaveを固定sourceからbuildし、Node/Wasmtimeで復元を比較した。[公式testからの中断点生成](research/state-witness/cut-results.md)では14 module・17位置・272変換条件を検査し、wasm-migrateの4つの元moduleで成功/trap差を再現、Weaveでは一致した。中断直後の状態差が再実行で消えるケースも確認した。既知の手書きtestとの重なりが残るため、**実装・反例・評価方法は得たが、強い新アルゴリズムの成立は未確認**という判定を維持する。現在の目的は修士研究であり、以下の特許記述は履歴である。

2026-10-24追補7：目的を**特許から修士研究の新規性へ変更**。[Jの厳格な再評価](research/logical-reset/strict-review.md)では、公開Weaveに論理memory容量・bounds・segment寿命の主要機構を確認し、主方式への採用を見送った。Wasmtime poolingとの105条件比較を追加し、4 MiB初期memory / 64 KiB処理ではJが約2.35倍遅かった。別原理の[K：非破壊状態観測](research/state-witness/README.md)を実装し、元API実行4,872回、非破壊性検査1,168箇所、公式test由来63module・650既存操作を検査した。核となるprobeは既存仕様testにもあり、新規性の確立とはしない。実装・反例・実測・再現CLI・日本語草稿を保存し、実対象での価値を継続検証する。現在の利用枠観測は38%使用・62%残り（正確なtoken残数ではない）。以下の特許目的の記述は過去の判断の履歴である。

2026-10-24追補6：[J: 論理容量とセグメント寿命による再初期化](research/logical-reset/README.md)を実Wasm変換として追加した。Node full 25,704比較、Wasmtime 8,148比較で不一致0。不完全resetの21反例を検出し、請求項案・先行技術対比・日本語ノートを保存。Node fresh生成より速い条件はあるが、既存poolingへの優位は未検証。NoWaSet非空219本は現行interface制約で全て対象外。構成差分の仮説はあるが、特許新規性・進歩性は未確立で主案昇格を保留する。今回の利用枠観測は32%使用・68%残り（正確なtoken残数ではない）。

2026-10-24追補5：[新規性の再評価](research/masters-security-20261024/novelty-evidence-audit.md)。狭い構成上の差分は残るが、特許につながる新規性・進歩性は未確認。「全案が既存と同一と判明した」とは結論しない。新規性、容易想到性、実用効果を分け、既存の測定値と否定的な結果を保持した。

2026-10-24追補4：[新規性の振り返り](research/masters-security-20261024/novelty-retrospective.md)。F-O/H/Iの設計差分と試作はあるが、特許につながる強い新規性は未確立。Iの80生成例、NoWaSet非空219binary、XNNPACK縮小転記を追加した。さらに[profile別テーブル補償](research/profile-repair/compensation.md)を実装し、Node約6150万byte・Wasmtime約2211万byteを照合したが、通常profileの表と速度は既存方式と同等だった。新しい速度改善とせず、主特許候補への昇格を保留。最新観測の利用枠は28%使用・72%残りであり、残り20%には到達していない。

2026-10-24追補3：[I: 共通profileを保つ部分決定化](research/profile-repair/README.md)を実装した。部分的なstrict化で安定した値が崩れる反例を実Wasmで確認。25例で99site中14を選択し、独立site近似は92を要した。主Node313,500照合、Wasmtime627,000照合、別式モデル200queryが一致。全strictに対する主性能比は約0.893–1.022で、手簡約には劣る。既知CEGISとの差から特許性は未確立。[H](research/waiter-identity/README.md)は2engine、並行書込み、順序を用いた一括復元まで検証し、排他前提の反例も保存した。研究は継続中、最新利用枠は23%使用・77%残り（正確なtoken数ではない）。

2026-10-24追補2：[H: 待機集合による共有メモリの実体分割](research/waiter-identity/README.md)を別原理として実装した。290分割・904内容hash・11境界条件を確認。64独立memoryの一括検査0.2119msに対し代表pairwise13.7237ms、正しいregistry0.0026msであり、適用場面を限定する。同期場所の静止が必須で、既存標準からの進歩性は未確立。[F-O](research/fuel-observer/README.md)では公開Irisデータ由来の4分類器を追加し、150件の合計論理予約額12.1～23.2%減と、限定bitvector検査を確認した。いずれも実装・実測・請求項たたき台を保存し、権利化可能とは断定していない。

2026-10-24追補：[公開履歴による予約・返金](research/fuel-observer/README.md)をFの拡張として実装。7例中3例でdepth予約より低予算で完了でき、V8/Wasmtime、適応予算、経路集約、誤った返金の反例を確認した。新しい公開後返金の技術的差分を検討中だが、公開schedule・重み付きobserverとの近接性から新規性は未確立。[import同一性の比較検査G](research/import-alias-quotient/README.md)も実装したが、既存wasm-mergeが198条件全てを代替したため主案に不採用。両者の実測・ソース・草稿を保存し、別原理の探索を続ける。

2026-10-24継続：[公開イベントに沿う累積fuel予約](research/fuel-frontier/README.md)を別原理の候補Fとして実装した。公開値付きWasm/Rust例で49,152値照合が一致、区間別予約163/167を97/99へ低減。32 CFG例と適応予算policyも検査した。ただし初期7例の6つは通常最適化で分岐が消え、修正版も同じ自作例の3 pipelineである。35 process比較で正しい手書き予約より約17～23%遅く、定資源型・公開イベント予定との差も弱い。[実測](research/fuel-frontier/results.md)と[草稿](research/fuel-frontier/paper-draft.md)を保存し、特許主案への昇格は保留。

2026-10-24追加：Aの[単一処理計画方式](research/masters-security-20261024/effect-plan-design.md)を実装し、288実Component条件と576生成器単体条件が一致。正しい手書き単一計画を加えた20 process比較では時間比約0.994～1.018で、明確な安全性・速度優位は未確認。[最新草稿](research/masters-security-20261024/paper-a-plan-draft.md)と[追加先行調査](research/masters-security-20261024/prior-art-followup.md)へ反映。lift前の費用検査も試したが、memo化は正しい非memo方式に6例中5例で遅く、発明要素に不採用。強い特許新規性の確立は引き続き未達。

2026-10-24：ユーザー指定によりWasmセキュリティ全般へ拡張し、[修士研究向けの3発明候補](research/masters-security-20261024/README.md)を作成。構成・請求項案・先行特許比較・実装・再現手順を保存。Aは実Component2,178受付、ローカルファイル288条件、終了処理60条件を確認。別schemaのbinding不備を修正し336呼出しを再検査した。改修後20 processの手書き比時間は約0.96～1.08。Bはhash-wasmで保存量削減0、別bytecode checkerで98部分要約を確認。[採否判断](research/masters-security-20261024/decision.md)、[A草稿](research/masters-security-20261024/paper-a-draft.md)、[B草稿](research/masters-security-20261024/paper-draft.md)を参照。特許につながる強い新規性は未確立。

2026-10-23追補：[重みを伴う解釈状態の同期](research/synchronizing-decoder/README.md)を実Wasmへ実装し、主54条件62,208呼出しと代表回復12条件13,824呼出しの一致を確認した。非可逆遷移で全入口を同じ計算へ収束できたが、代表状態一つで全12sync条件を全状態解析とbyte一致のコードへ回復。元の約3.71–30.80倍の実行費用に対して追加保護の根拠が弱く、weighted synchronizationにも先行性があるため主案に不採用。[実測と再現](results/invention-20261023/synchronizing-decoder-report-v1/report.md)。

2026-10-23追補：[非線形共有退避](research/nonlinear-save/README.md)を実Wasmへ実装した。探索600例中1例と独立holdout600例中1例で、最良線形保存2bitに対して1bitを達成。主42条件40,362呼出しと追試14条件12,614呼出しは一致した。ただし公開APIから全24変換条件を同等遷移表へ回復でき、既知のfunctional index coding・cographとの差も弱い。表生成の補助的最適化として保存し、主たる難読化発明には不採用。[実測と再現](results/invention-20261023/nonlinear-save-report-v1/report.md)。

2026-10-23追補：[有限精度の観測閉包](research/observer-closure/README.md)を自動生成し、実Wasmへ実装した。主30正条件780,090 API呼出しは一致したが、全12変換を10step観測で小さな更新へ回復。reset/peekを削った追試でも全12変換を22stepで回復し、491,520stepは一致した。実行費用は元の約5.18–10.05倍で、既知の観測実現・多項式持上げを超える新規性と保護優位は未確立。主特許候補には不採用。[実測と再現](results/invention-20261023/observer-closure-report-v1/report.md)。

2026-10-23追補：[遷移二乗と双模倣評価](research/transition-square/README.md)を実Wasmへ実装した。主54条件106,488呼出し、境界48条件24,960呼出しは一致したが、公開行列の平方根とBoolean抽出で主24条件・境界12条件をすべて回復。同じgraph評価器に対して約26–37%高速化した一方、元の式比約811–8,643倍の実行費用。回路還元・行列関数の先行性と公開逆算から主特許候補には不採用。[実測](results/invention-20261023/transition-square-report-v1/report.md)。

2026-10-23追補：[外部解析器Disrobeの実測](research/disrobe-baseline/README.md)。27入力のC/JSON/WAT生成81処理は正常終了。整数式18条件は75,906呼出しで一致したが、未変換リスト9条件は生成WATの初期data欠落で5,148呼出し中504不一致。別deobの18出力は入力とbyte一致した一方、自前の適応射影による既存回復は成立している。ツールの未対応を難読化効果へ数えず、新発明の件数には加えない。[実測・再現](results/invention-20261023/disrobe-report-v1/report.md)。

2026-10-23追補：[共有退避の生成器](research/side-save/README.md)を実装。同じBを保ち、入口保存次元を4→1、32→4、10→1へ削減した。正37,184呼出し・期待trap19,152で一致し、rotate32の実行中央値は同じBのbasis対照より約13.8%短縮。一方temporaryとcode sizeは増え、既存回復器がbasis/side各12条件を元Wasmへ戻した。coded side-informationとの近さから独立した新難読化・特許性は未確立。総メモリ削減とは主張せず、費用改善の補助部品として保持する。 [実測](results/invention-20261023/side-save-report-v1/report.md)。

2026-10-23追補：[実装・測定](research/residue-wrap/README.md)。既知RNCの明示した移植規則を検査し、odd版全6条件で誤答、二修正版を含む正24条件101,208呼出しで一致した。aligned版はraw/O3全6条件を元とbyte一致するWasmへ回復。修正版は元の約2.76–15.25倍の実行時間となり、主特許候補には不採用。著者実装のバグ、RNS一般の不可能性、新しい環の定理は主張しない。 [集計](results/invention-20261023/residue-wrap-report-v2/report.md)。

2026-10-23追補：[解除器の適用範囲を実測](research/profile-boundary/README.md)。動作が同じ84条件のうち旧解除器は60条件を形式未対応としたが、範囲証明を含む拡張で全84条件を回復した。追加式24条件も回復し、正しい12条件はなお未対応として区別。延べ530,460呼出しは一致した。新発明の件数には加えず、未対応を保護効果へ誤算入しない評価改善として保存した。[集計](results/invention-20261023/profile-boundary-report-v1/report.md)。

2026-10-23追補：[更新のたびに中間対応を変える二表表現](research/mutable-factor/README.md)を実装・反証。主60本と診断36本の計202,080呼出しは一致したが、全24変換条件を変更履歴なしに元とbyte一致するWasmへ回復。元の約1.40–1.99倍の実行費用に対する追加保護と独立した新規性は未確立で、主特許候補には不採用。[実測](results/invention-20261023/mutable-factor-report-v1/report.md)。

2026-10-23追補：[copy履歴を観測位置へ引き戻す案](research/range-pullback/README.md)を初期検査。36本92,544呼出しの値/trapは一致したが、全12変換条件を元とbyte一致するWasmへ回復。疎なreadでの高速化は既知のlazy copy/read forwardingに近く、主特許候補には不採用。[実測](results/invention-20261023/range-pullback-report-v1/report.md)。

2026-10-23追補：[部分文字列をまたぐ非線形な文法変換](research/substring-shear/README.md)を実Wasmで検証。主120本49,640呼出し、四次追加28本9,968呼出しは一致したが、公開係数から主54+追加12条件すべてを回復。任意の重みにも通用する解除条件を論証し、実行時間約1.43〜1.65倍の本案は主特許候補に不採用。[実測・再現](results/invention-20261023/substring-shear-report-v1/report.md)。

2026-10-23追補：[更新を含む情報消去の成立条件と反証](research/mutation-quotient/README.md)を実Wasmへ実装。主90本448,230呼出し一致。公開I/Oから対照・変換54条件すべてを各n回の問い合わせで等価実装へ回復し、主特許候補には不採用。[実測・再現](results/invention-20261023/mutation-quotient-report-v1/report.md)。独立した有力な新規性の確立は引き続き未達。

2026-10-23追補：[状態付き切替グラフの全体合成](research/rotor-synthesis/README.md)を別原理の候補として実装した。共通評価器、直接命令化、上限削減の3段階を検査し、元との正当性比較は各主24binary・115,992呼出しで不一致0。最良版は元の約5.4〜9.4倍で、公開命令だけから全例を回復できた。既知rotor計算・有限仕様合成以上の新規性も未確立のため主候補には不採用。[実測と再現資料](results/invention-20261023/rotor-synthesis-report-v1/report.md)。

2026-10-23追補：[非共役なBoolean残差補正](research/boolean-feedback/README.md)を3段階まで実装・実験した。普遍補正器25,968個の分類と整数持上げの論証を得たが、bitwise・word・切替版はいずれも適応解析で回復。切替版の解析負担増は約3倍、実行増約3.5–3.7倍で主特許候補には不採用。[実測と再現](results/invention-20261023/boolean-feedback-report-v1/report.md)を保存し、別原理の研究を継続する。

2026-10-23再開：[有限回更新と隠れた依存順序](research/hidden-filtration/README.md)を実装・実験した。元の座標対応を配布しなくても、公開Wasmだけから全18条件を回復。非線形版の解析時間0.12–4.75秒、主307,656呼出し一致、回復18モデルのSMT等価性確認。限定的な解析負担増はあるが、既知の非線形座標変換との差と実行費用から主特許候補に不採用。別原理の研究は継続中。

2026-10-23：[現在の研究判断](research/novelty-status-20261023.md)。[入力依存の線形包表現](research/span-mask/README.md)を実Wasmで実装し、正当性・適応解析・性能・独立監査まで実施した。全数入出力学習でO3の12条件を全て回復し、固定混合より約3.8～11.4倍遅いため主特許候補に不採用。[借用メモリの早期検証](research/catalytic-memory/README.md)も6/6回復し、trap後の状態破損を検出した。新しい有力な発明を確立したとは主張しない。従来の有限環方式の限定した構成候補は保持する。

2026-10-22追補：[入力条件で順序が変わる循環する共有演算](research/conditional-causality/README.md)を実Wasmへ実装・反証した。主126,000呼出しと任意初期状態12,288呼出しは一致したが、全12条件を回復し、回復O3は元版とbyte一致。循環版は通常VMより約33–59%遅く、既存schedule合成との差も弱いため主発明に不採用。新規性確立・特許目標の達成とは扱わない。

2026-10-22追補：[違反同士を結び付ける最終改良](research/energy-descent/interactions-analysis.md)。局所最小を2引数だけで選べない構成を得たが、逐次消去では全12条件が回復した。修正版30条件61,860呼出し一致、元版比約210–245倍。公開binaryだけでenergyの前提を検査する回復器も追加。このenergy方向は3設計段階で不採用とし、別原理の主方式を目指す研究は継続する。

2026-10-22追補：[局所更新を一致させないenergy改良](research/energy-descent/relaxed-analysis.md)。全体の収束条件を合成し、元ゲートと逆向きの更新でも正答する例を実装した。通常180,420呼出し・全初期値probe2,922,496呼出しが一致。ただし最小化による変数消去で全28条件を回復し、改良例は元版比約172倍の実行費用。旧解析器の未対応を保護成功に数えず、同じ方式の改良として不採用理由を保存した。

2026-10-22追補：[違反量の下降による計算](research/energy-descent/README.md)。実Wasmの正42条件136,444呼出し一致。正答を保証する重み条件から局所更新が回復し、全18保護条件を通常DAGへ変換できた。現評価器は小カーネルの元版比約993–1,810倍の実行費用。既知penalty/energy構成との距離も弱く、主発明には採用しない。構成・論証・実験・反例を保存し、研究全体は継続する。

2026-10-22追補：[非単射な持続状態表現](research/torsion-state/README.md)。全状態へ一意に戻せない表現で、呼出しをまたぐ整数更新を実Wasmに実装した。正48条件807,024 step・6,816 resetが一致し、非単射版の実行は元版の約1.03–1.09倍。一方、低次元線形系という前提のもとで全24対照・変換条件を各16公開応答から回復した。前提を破る反例も保存し、独立した主発明には採用しない。

2026-10-22追補：[生存区間を使う型の重複配置](research/lifetime-overlay/README.md)。値の符号化とは別に、同時には使わないi32/i64の格納場所を重ねる実Wasm変換を検査した。正36条件943,104呼出しが一致し、実行費用は元版の約1.01–1.06倍。ただしraw/O3全18条件を到達定義解析で回復でき、既知のstack coloringとの差も弱い。主発明には採用せず、型衝突数と経路数を解析困難性の代替にしないという反証を保存した。

2026-10-22追補：[2進刻みの差分評価と修正版](research/dyadic-difference/README.md)。元式を呼ばず差分だけを累積する実Wasm変換を実装。初版247,830・修正版297,396呼出しが一致したが、修正版を含む全18条件を各34公開問い合わせで回復できた。既知の有限環多項式の補間が核に対応し、元版比約63–101倍の実行費用に見合う保護優位は未確認。主発明には不採用。次数を増すだけでは避けられない理由と、条件外の反例を保存した。

2026-10-22追補：[逆向き受理情報の非線形混合](research/reverse-observer/README.md)。実Wasmの正42条件182,532呼出し、別WABT336呼出し、48本のbyte再現が一致。逆変換手順を生成物から除いても全18保護条件を小さなDFAへ回復した。既知のオートマトン反転と観測関数の閉包が近接し、混合の実行費用は元版の約1.17–11.29倍。独立した新規性と保護優位は未確立で主発明には採用しない。

2026-10-22追補：[コピーの情報損失に適合する現状態修復](research/loss-flag/README.md)。入口保存を不要にする表現と修復器を実Wasmへ実装。正54条件83,196呼出し、別WABT360呼出し、66本のbyte再現が一致。同じBの共有入口保存対照より正常2構造で約26～28%高速化し、1構造は約2.8%悪化した。既存回復器が未変更で全12条件を元binaryへ戻せたため、工学的部品として保持し、独立した主発明には採用しない。

2026-10-22追補：[型検査の妥当性へ条件式を移す試作](research/validation-value/README.md)。Wasmのunreachable typingを使う実binary変換を実装し、24実行条件53,456呼出し、別WABTと6回復式のSMT同値確認を実施した。全6保護条件を実行oracleなしで通常のBoolean式へ回復でき、実行は元の約88～136倍。計算を検証器へ移す具体的構成は保存するが、独立した新規性と保護優位は未確立で主発明には不採用。

2026-10-22追補：[native waitを保つ共有field混合](research/wait-partition/README.md)。待機の観測範囲から許す混合を選び、実Wasmへ変換した。24条件50,088呼出し・393,216並行更新・待機通知48条件を検査し、素朴なsnapshot翻訳が通知を取り逃がす反例も再現。一方、全24条件の表現を4回の選択書込みで同定でき、独立した新規性と追加保護効果は未確立。正当性条件の知見として保存し、主発明には採用しない。

2026-10-22追補：[値から配置を決めるメモリ表現](research/invariant-layout/README.md)。配置表を持たず、語の変更差分で配置を更新する実Wasm変換を実装。正42条件19,656呼出しで値・trap・復号後メモリが一致し、全体復号対照より約12～19%高速化した。ただし18条件すべてに通常配置の回復候補が得られ、元計算より約12～18倍遅い。既存の動的符号化に対する独立性と保護優位は未確立で、主発明には採用しない。

2026-10-22追補：[状態依存係数でも正解へ到達する十分条件](research/root-descent/README.md)。係数内の回転を許す論証・実Wasm・適応的回復器を作成し、正42条件128,016呼出しが一致した。18/18条件を係数から回復でき、回転版の実行は元の小さな式の約425～429倍。一般収束理論に対する新規性と追加の保護効果は未確立で、独立した主発明には採用しない。

2026-10-22追補：[全計算を行列式へ移す候補](research/unit-minor/README.md)。公開された逆行列を使わない生成時混合を実Wasmへ実装し、正42条件214,032呼出し、別WABT336呼出しが一致。全18条件を係数表の直接的な記号計算で回復した。定数混合比で解析本体8.06–15.24倍、実行2.85–3.09倍の増加はあるが、ADPと既存特許の多項式行列生成に近く、独立した主発明としては不採用。実測・再現手順・限界を保存した。

2026-10-22追補：[再帰frameごとの動的混合](research/recursive-frame/README.md)。実Wasm変換・関数要約による回復・反例・性能比較を実施。正36条件265,680呼出し、別WABT288呼出しが一致。動的6条件はraw/O3とも履歴を展開せず回復でき、同じroot条件のv2で実行は元の4.51–6.30倍。固定混合より解析本体は1.59–1.76倍、読取込みの中央値和は約0.4–3.3%増加したが、履歴依存の困難化と独立した新規性は支持されず主発明に採用しない。

2026-10-22追補：[商と余りの小数部融合](research/fractional-pair/README.md)。可変除数に応じて内部値の許容範囲を生成する実Wasm変換を実装。36正条件951,540呼出し（trap3,528件）一致、範囲の論証・全列挙・反例を保存した。一方、raw/O3の12/12条件を通常div/remへ回復でき、実行は通常のqsub対照の約1.58–1.81倍。小数部から余りを得る既存研究との技術差と限界を記録し、主発明には採用しない。

2026-10-22追補：[飽和演算を広いレーンの商として実行する方式](research/saturation-buckets/README.md)。下位bitの正規化を省く実Wasm変換を作成し、60正条件・3,962,880呼出しが一致。正規化ありの対照より約14–26%速い一方、通常の8bit SIMD版より約12–33%遅い。方式既知の入出力学習は30/30条件で等価候補を得て、通常版と問い合わせ数も同じだった。独立した新規性と追加の解析耐性は未確立で、主発明には採用しない。有限環方式の構成的提案は保持する。

2026-10-22：[現在の新規性評価](research/novelty-status-20261022.md)。有限環方式の構成的提案は保持する一方、特許性・保護上の優位は未確立。追加の[同符号係数混合](research/sign-coherent/README.md)は約238万回の比較が一致したが、既存activation cone研究との近接性と18/18の等価形回復から主発明に採用しない。

2026-10-22追補：[コピー列の共有修復](research/prefix-repair/README.md)。途中trap後の状態も保つ実Wasm変換を実装し、42,496呼出しが一致。同codecの逐次修復より約28～48%時間短縮したが、未変換比約10.9～16.4倍。正48条件は全て元形式へ回復でき、低rank差分・状態補償から独立した新規性は未確立。主発明には採用せず、構成と費用削減を保存した。

2026-10-21追補：[Hasse係数回路への変換](research/hasse-gate/README.md)。実Wasm32本・40,960呼出しを照合し、変換版は最適化前後8/8で係数表へ回復できた。解析費用増加は存在するが、既知の係数算術から独立した新規性が弱く主発明には不採用。回復したHorner実装は元の因数分解と異なり、今回の実行では高速化しない点も記録した。

2026-10-21追補：[回転で観測位置を変える履歴型変換](research/rotation-history/README.md)。固定回転の状態を履歴へ置換し、24本26,496呼出しで一致。一方、source/historyとも64問い合わせで規則が戻り、追加の保護利得は未確認。入力依存回転では任意の有限長の実際の入出力履歴だけでは足りない条件と必要な追加情報量を整理し、実行反例も保存した。主発明には採用しない。

2026-10-21追補：[倍率に合わせた浮動小数点の丸め格子](research/shifted-rounding/README.md)。32条件204,800呼出しを独立oracleと照合したが、方式既知の解析ではgrid0/shiftedの16条件すべてを元の演算順序へ回復した。非正規化数を含む限定入力で速度改善はあるものの、倍率0の対照でも得られる。CPFloat・既存の倍率符号化との近接性も記録し、主発明には採用しない。有限環方式の構成的提案は保持する。

2026-10-21追補：[可変多項式表現の更新差分](research/polynomial-update-gate/README.md)。56本170,298呼出しを照合し、通常キーの更新1,102件は前後の係数snapshotだけから全件回復した。既知の補間を可変辞書へ拡張しても更新差分が直接キーを露呈するため、新しい主発明には数えない。実装・再現・性能・適用限界を保存した。

2026-10-21追補：[型回復のアクセス経路と既知変換の対照](research/type-language-gate/README.md)。公開Retypdを実行できる環境を構築し、実Wasmから制約を抽出した。40本70,440呼出し（trap期待3,600件を含む）が一致。末尾loop peelingで精密な制約列挙の費用は増えたが、既存の形状統合により全40本のfield配置を回復できた。既知変換を新発明に数えず、NotDec本体の実測とも区別する。研究は継続中。

2026-10-21追補：[静的リストの多項式表現](research/polynomial-lookup/README.md)。局所decoderを残さずlookup全体を置換する案を実Wasmで検査。70条件92,230呼出し、別engine210probe、算術4,312比較が一致。28変換条件は公開係数の因子分割で全辞書を回復した。128件で読取込みの回復は配列対照約22ms→約670ms、hit実行は約16.6ns→約623ns。費用増加を認めつつ、既知の集合多項式・補間から独立した新規性は未確立で主発明には採用しない。有限環方式の構成的提案は保持する。

2026-10-21追補：[アトミック命令に両立する表現の生成](research/atomic-codec/README.md)。18正条件16,470呼出し、追加4,000呼出し、実worker328,448正更新を照合。単一native命令へ閉じる表現の制限を導出し、同codecのCAS対照から約6–14%の時間短縮を確認したが、14符号化条件は2回の選択storeで回復した。Tigressの演算適合codec選択との近接性も確認し、主発明としては不採用。有限環の構成的提案は保持する。

2026-10-21追補：[ページ内block表現とtrapを保存するlowering](research/page-block-codec/README.md)。実Wasmの30正条件79,820呼出し比較が一致。byte更新対照より約4.45–5.47倍速いが、既知の高アドレス優先storeでも同じ意味を保ち、復号helperを用いて12条件すべての全memoryを回復できた。主発明に採用せず、正当性規則・費用・先行性の具体的な対応を保存した。有限環方式の構成的提案は保持する。

2026-10-21の早期ゲート：[計算全体を奇数長の閉路・traceへ移す案](experiments/odd-trace-gate/README.md)。先行論文に近い構成を確認し、Wasmの整数wrapで偶数長が情報を失う反例を実行した。補正した6正条件は804比較で一致するが、全条件を52byteの式へ回復。新規の主案には採用せず、汎用変換器・大規模性能評価へは進めていない。

2026-10-21追補：[コピー互換の非線形残差表現を全SHA-256圧縮へ適用](research/copy-fiber/README.md)。公開状態APIのない10条件で圧縮2,620・全SHA410比較が一致したが、全条件をbinary-only解析で同じ1,881演算DAGへ回復できた。1層nativeは素朴repairより約3.12%短い一方、plainの約23.47倍。非線形化とAPI削除だけでは相殺を防げず、主案には不採用。既存の有限環方式の構成的提案は保持する。

2026-10-21追補：[コピー操作からメモリ混合codecを生成する試作](research/copy-centralizer/README.md)。32主条件＋8回復条件で値・trap・全論理memoryを照合。非自明な3profileの入力選択workloadは同じcodecの全復号版より約30–58%短いが、全8条件を32 readだけでcloneできた。自動生成と費用削減の成果を保持し、独立した主発明には採用しない。

過去の成果を含む現在の評価：[有限環残差フィードバック方式には、限定採用した構成的提案と実Wasmの検証がある](research/repository-assessment-20261021.md)。その後の解析実験で現実装の保護上の弱点を確認したことと、構成上の提案の存在は区別する。

2026-10-21の別原理の試作：[内部変数を消した制約伝播](research/propagation-projection/README.md)。48本19,176呼出しで値・全memory一致、24条件を公開I/Oから等価式へ回復した。80processの同条件比較ではCNF対照比で1例約25%改善、3例は悪化。論理同値でも伝播だけでは停止できない反例も保存した。主発明への採用は見送り、bit間の関係を持つ計算での別の生成規則を次の検討課題とする。

2026-10-21の別案の成立性検査：[復号器の商・剰余更新と意味計算の共用](research/selector-quotient/README.md)。固定剰余による表現では入力値によらない次の処理を選べない条件を導出し、9,734設定と実Wasmで反証した。正しく修復した対照・回復式等24本24,960呼出しは一致するが、対象のアフィン関数族は公開I/Oで容易に回復できる。32本のbyte再生成も一致。本案は不採用であり、成功した発明を追加したという報告ではない。

2026-10-21の別原理の試作：[浮動小数点の零符号を遅延修復する変換](research/zero-sign-transport/README.md)。主56正対象の372,736呼出し、追加84正対象の106,176呼出しで不一致0。自作の各演算修復対照より通常値3例で約36–66%時間減。ただし数値graphを抽出し、零時だけ元処理を残す部分簡約は通常値で未変換の約0.99–1.12倍の時間となった。費用改善部品として保持し、主発明としての採用は保留。独立した新規性・有用な保護効果を目指す研究は継続中。

2026-10-21の有限環方式の追加評価：[回復実験・費用・再現手順](research/finite-ring-evaluation/README.md)。採用済みの構成的提案を保持したまま、その実装の弱点を検査した。元DAGを与えずraw/O3両方から381座標の回路を回復し、全scratchを再現した全SHA版も531入力で一致した。原型helper約832µsに対し状態回復版約0.257µs。構成上の提案が存在することと、強い保護効果が実証されたことを区別する。

2026-10-21の追加比較：[位置依存表現のコピー後補正](research/bulk-rebase/README.md)。44本の正当性検査・適応復号・別実行器・270 fresh processの性能比較を完了。直接SIMD対照よりO3サイズは354bytes小さいが、9条件中8条件で約31–75%遅く、1条件は同程度。主方式には不採用とし、サイズと時間のトレードオフを保存した。以下の過去の限定採用は保持し、研究全体は継続中。

2026-10-21の過去成果の再確認：[リポジトリ全体の評価の訂正](research/repository-assessment-20261021.md)。10月12日の[有限環残差フィードバック方式](experiments/sha256-fixedpoint/research-checkpoint-ja.md)は、元の依存順序からの生成規則を**限定した構成的提案として採用済み**。実Wasmと531入力の全ハッシュ検証があり、今回保存証拠を再照合した。以下の継続研究の「主発明の確立は未達」は、この過去の提案が存在しないという意味ではない。保護性能の優位・実用性・特許性は別途未確立。

2026-10-21の継続結果：[privateな飽和カウンタの符号化費用](research/saturation-anchor/README.md)。48本の正当性・メモリ副作用を照合し、主要240 fresh processでは同じ符号化のmin版比、中央値で約2–14%の時間減と42bytes減を観測した。適応解析は16問い合わせで全48本の符号化を回復。Hamburg(CHES2009)に近い表現設計があり、[特許の主核は保留](research/patent/saturation-anchor.md)。限定カーネルへの適用範囲を調べた改良試作であり、特許を目指す主目標は継続中。

追加比較：[固定文字列の群上rolling照合](research/rolling-point/README.md)。点関数の先行性を確認したうえで実Wasm変換・方式既知の回復・raw/O2/O3・性能を検査。主27条件の1,998呼出し等で不一致0。未知部分が1–3byteで残り既知なら全54条件で回復した。rollingは群上再計算より8–15倍高速だが、この実装の総コストは大きい。独立した新原理ではないため主提案には採用しない。発明研究は未完了。

最新の探索：[メモリの利用結果だけを残す射影](research/memory-quotient/README.md)。実Wasm変換・公開I/Oによる復元・raw/O2/O3・性能比較まで実施。54条件・3,553,335実行で不一致0だったが、全18保護条件を元と同じ2load+XORへ戻せた。元データが一意でなくなる場合にも容易な等価実装が作れるため、アルゴリズム保護としては不採用。独立した新規性と有効性の確立は未達。

追加の棄却実験：[2回の更新を合成して中間状態を消す案](research/checkpoint-composition/README.md)。奇数係数の二次更新は最大4候補で再分解でき、最適化後を含む18条件で回復した。54バイナリ・14,256実行で不一致0。既知の次数上限の下では公開I/Oの5問い合わせでも同等のWasmを生成できた。これは新発明の成功ではなく、採用しない理由を具体化した結果である。[追加文献照合](research/nonlocal-literature-audit.md)。

最新の追加試作：[Wasm GCの参照共有でBoolean回路を実行する方式](research/alias-circuit/README.md)。実バイナリ変換・最適化・解除・性能測定を実行し、27条件・115,776実行で不一致0。ただし最適化後を含む全9条件から通常の回路を回復でき、先行するalias難読化からの新規性も未確立のため不採用。公開I/Oだけでも短い式を学習できる小例であり、保護強度の主評価には使わない。

メモリ方向の評価を訂正：[公開APIだけの接続回復](research/memory-trace-audit/io-audit.md)で、27条件すべての全payload・接続を回復した。生成したWasm cloneとの627,444入力条件で不一致0。[アクセス列の対照](research/memory-trace-audit/README.md)は計測器の検査には使えるが、公開API自体が対象を開示するため難読化強度の主評価には使わない。新しい難読化方式は未確立。

最新の継続実験：[飽和SIMDの代数を使う分解消去](research/saturating-frontier/README.md)。実Wasm変換と解除側を実装し、24本・199,512入力条件で一致。4例とも元と同じ演算数へ再構成できたため、有効な新方式としては未採用。[残差方式の対照実験](research/operand-rebasing/novelty-ledger.md)も追加した。発明研究は継続中。

追加実験：[対称式だけで内部状態を更新する方式](research/symmetric-state/README.md) を実装。36本・47,232入力条件で正当性検査を通過したが、12条件すべてで元の更新則を復元できた。実測・再現スクリプトを保存し、新規性・保護効果は未確立として扱う。

継続研究：Wasmの可変関数テーブルを使う別方式も実装・検証したが、最適化後を含む9条件すべてで解除できた。[設計・実測・再現手順](research/table-transport/README.md)。新方式の確立に向けた研究は継続中。

2026-10-18の発明研究では3案を比較し、観測文脈を保持するWasm式再合成を実装・評価した。75条件の正当性検査は通過したが、保護対象60条件を全て0–2演算で復元でき、有効な新規保護方式の確立には至らなかった。以下のCSEC研究とは別の成果である。

- [日本語論文草稿・負の結果](paper-draft.md)
- [環境構築・CLI・一括再現](research/observation-synthesis/README.md)
- [文献調査](research/literature-review.md)・[3案の設計比較](research/candidates.md)・[実験計画と結果](research/experiments.md)
- [全条件の実測比較](results/invention-20261018/observation-suite-v2/comparison.md)・[完了条件と未達事項](research/completion-audit.md)

現環境での再現例（rootから、新しい出力先を指定）：

```powershell
./research/observation-synthesis/reproduce.ps1 -OutputDirectory results/research-new-run -NodeCommand 'C:/Program Files/nodejs/node.exe'
```

12月のCSEC研究会に向けた研究用リポジトリ

2026年10月5日時点のテーマ候補、先行研究、データセット、実験設計は
[研究計画](docs/research-plan.md)を参照。
発表申込用の和英タイトル・概要案は[申込下書き](docs/submission-draft.md)に記載。

CSEC研究報告用のLaTeXひな形とビルド手順は[論文ひな形](paper/README.md)を参照。
本文は`paper/main.tex`である。公開されているクリプトジャッキング関連データセットを対象に、難読化の指標が測定方法によってどの程度変わるかを扱う。

2026-10-06時点で版を固定したデータを使い、予備実験を完了した。候補25件を確認し、公開バイナリを取得・統合できた18データセットを静的解析した。配布フォルダ内のファイル数は109,846件で、SHA-256が異なるバイナリは70,564種類である。解析に成功した67,729件だけでなく、検証・読み取りに失敗した2,835件も、結果が得られなかったものとして一覧に記録した。論文の対象はクリプトジャッキング関連データセットに限り、実環境全体の難読化率や、年ごとの変化は結論に含めない。

- [先行研究・対象候補・新規性の検討](docs/literature-review.md)
- [取得・解析の進捗履歴](docs/corpus-progress.md)
- [予備実験の最終報告と図表](docs/pilot-report.md)
- [予備実験の完了条件の確認](docs/completion-audit.md)
- [再現手順と測定上の注意](docs/reproduction.md)
- [現在取得済みの範囲の集計](results/corpus/summary.json)

旧研究計画と申込下書きには、目的を変更する前の記述が含まれる。現在の研究結果として、そのまま提出しないこと。
