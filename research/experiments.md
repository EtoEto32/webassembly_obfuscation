# 観測文脈再合成の事前実験計画

2026-10-23追補：[解除器の形式依存を調べる追試](profile-boundary/README.md)。同値変更84条件で旧24成功・60未対応、範囲証明を加えた拡張84成功。追加24成功・正しいself-partner12未対応・範囲不正12拒否を別集計した。Node延べ530,460呼出し、WABT1,008呼出しで不一致0。元の6fixtureと同一回復binaryの反復を独立標本数として扱わない。新しい難読化原理の実験とは数えない。

2026-10-23追補：[span事前計画](span-mask/plan.md)に対する[実測集計](../results/invention-20261023/span-mask-report-v1/report.md)を追加した。main158,558、追加45,056、scratch6,144呼出し、WABT164、GF(2)1,152入力。解析36試行中26復元・10node上限、全数学習12/12。性能45process315batch。[借用メモリの早期検証](catalytic-memory/README.md)は18条件76,374呼出し・6/6回復。初期readerエラーを除外して再実行し、未対応やクラッシュを保護効果に数えない。

2026-10-22追補：[条件別の循環共有の事前計画](conditional-causality/plan.md)に対する[実測](conditional-causality/analysis.md)を追加した。主30条件126,000呼出し、初期state probe12,288呼出し、回復12条件、helper SMT96、記号合成順24、WABT120呼出しを検査。性能v2は45process/315batchで短batch0。v1の較正上限による61短batchも保存し、未対応・測定不足を保護効果に数えていない。

2026-10-22追加：[energyの符号付き相互作用の実験記録](energy-descent/interactions-analysis.md)。全状態制約の初期版と、同値energyの自由な選択も考慮した修正版を分離。各30条件（byte異なる24本）61,860通常呼出し・全初期値probe384呼出し一致、各12回復・30 byte再現・WABT120呼出し。性能は各45 fresh process/315batch。入力は各2bitだけなので実用的耐性の証拠とはしない。全エネルギーに対する公開前提検査と、同値値を使う最小selectorの全列挙を追加した。

2026-10-22追加：[energy改良の事前計画](energy-descent/relaxed-plan.md)と[結果](energy-descent/relaxed-analysis.md)。初期6例では重みが変わらず、事後追加1例で局所逆向きと全体収束を両立。70条件はbyte異なる37本で、通常180,420・全初期値probe2,922,496呼出し一致。28回復、248最小化段と28出力同値のSMT、70 byte再現、WABT280呼出しを確認。15 fresh process/105batchの性能比較は追加1例だけであり、アプリ一般へ広げない。

2026-10-22追補：[違反量による評価の計画・結果](energy-descent/README.md)。正42条件136,444呼出し一致、全18回復、等重み6反例。byte再現48、WABT168、局所規則336、性能45process/315batchを保存。局所収束条件が解析にも与える情報を評価し、一般NP困難性や元制約分解の非一意性を保護根拠にしない。

2026-10-22追補：[非単射状態の事前計画](torsion-state/plan.md)と[結果](../results/invention-20261022/torsion-state-report-v1/comparison.md)。3状態数設定 × plain/basis/quotient/perturb × raw/O3と回復版で正48条件、807,024 stepと6,816 reset。不一致0。全24条件を各16公開応答から回復し、前提を別途binaryから検査した。WABT384 step、48本byte再現、solver5,184系、性能45 fresh process/315batch、前提外反例2種を保存。独立アプリ3個と数えず、16問による任意プログラムの同値性証明とは扱わない。

2026-10-22追補：[型の重複配置の事前計画](lifetime-overlay/plan.md)と[結果](../results/invention-20261022/lifetime-overlay-report-v1/comparison.md)。3合成kernelの元/first-fit/型衝突優先 × raw/O3と回復版で正36条件（異なるbyte列23本）、943,104呼出し。WABT144呼出し、36本byte再現、6対象外拒否、評価順と符号拡張288呼出しを追加。性能36 fresh process/252batch、回復90反復。初版のO3 local.tee未対応9件は修正後に全回復し、耐性に数えない。型矛盾はproxyであり外部逆コンパイラの失敗率ではない。

2026-10-22追補：[差分評価の事前計画と修正](dyadic-difference/plan.md)、[実測](dyadic-difference/README.md)。初版30正条件247,830呼出し、修正版36正条件297,396呼出し、各36process/252batchを保存。静的回復への修正を行った後、元版と同じ34問い合わせで全18条件を回復し、問い合わせの前提を外す負の対照も検査した。各区間には同じbinaryや入力が含まれるため独立件数として合算しない。

2026-10-22追補：[現状態修復の事前計画](loss-flag/plan.md)と[実測](loss-flag/README.md)。3固定copy構造、2seeds、raw/O3、正54条件83,196呼出し（trap42,588）、負12条件、66本byte再現、別WABT360呼出し・1,404memory probe。既存回復器は全12 current条件を回復。性能は初回と呼出し境界を分けた追加harnessを各36process/252batch実施し、v2を主比較にした。正常2構造でbasis比26～28%短縮、1構造2.8%増加。3実アプリの評価や全経路性能とはしない。

2026-10-22追補：[再帰frame混合](recursive-frame/plan.md)の事前計画を実施。[結果](recursive-frame/README.md)：42binary、正36条件265,680呼出し、別WABT288呼出し、42byte再生成、6有効Wasm拒否対照。保護12条件（動的6）は元sourceなしで回復。同じrootにそろえたv2が主比較。72fresh process・648batch、126batchは10ms未満。3つの係数設定であり3実アプリとは数えない。モデル25,368+10,000組はWasm呼出し数と分離した。

2026-10-22追補：[小数部融合の実験](fractional-pair/README.md)。pair・16段連鎖・Euclid型ループを含む3合成consumerを比較。36正条件951,540呼出し（trap3,528件）一致、6負条件に反例、方式既知解析12/12回復。42本の再生成とWABT288呼出し、6拒否対照も実施。性能は2除数分布×5方式×3 consumer×3 fresh process、計90 process/810 batch。初回の負例が発火しなかったv1を成功へ加算せず、修正v2を主結果とする。[比較表](../results/invention-20261022/fractional-pair-report-v1/comparison.md)。

2026-10-22追補：[飽和商表現の実験](saturation-buckets/README.md)。3合成関数、plain/native8/canonical/zero/bucketと誤変換、raw/O3、方式既知の公開I/O学習を比較した。主main-v2は60正条件3,962,880呼出し一致、6負条件に反例。各条件の65,536 broadcast入力と512独立packed入力を全2^128入力の検査とは数えない。54 fresh process・486 batchの性能測定、66本のbyte再生成、別WABT実行480呼出し、4対象外profile拒否を保存した。全30学習条件で通常版と同じ問い合わせ数となり、追加の保護効果は支持されない。[比較表](../results/invention-20261022/saturation-buckets-report-v1/comparison.md)。

2026-10-22追補：[同符号群の係数混合](sign-coherent/README.md)。3合成関数・1混合seed、正36条件2,377,728呼出し、負6条件、方式既知回復18条件、36 fresh processの性能測定、42本のbyte再生成と別WABT288呼出しを保存。全正条件一致、全回復条件で短い等価形となり、追加保護効果は未確認。

2026-10-22追補：[共有prefix修復の実験](prefix-repair/README.md)。正48条件42,496呼出しと負12条件、別WABT336呼出し、60binaryと60probe再生成を検証。72 fresh processで同codecのeager/full/basisを比較。方式既知で正48条件すべて回復。回復checkerの代表値検査に不足を発見し、元引数の使用検査と反例を追加したanalysis-v4を最終結果とする。

2026-10-21追補：[Hasse係数の早期実験](hasse-gate/README.md)。4合成式、32本40,960呼出し、別実行器128 probe、32本byte再生成が一致。未変換/変換に同じ係数回復器を適用し、16/16で回復。36 fresh processで費用を測定。回復対象は係数表とHorner実装であり、元DAGの完全復元や高速な複製は達成していない。

2026-10-21追補：[回転履歴の実験](rotation-history/README.md)。主24本26,496呼出し（期待trap7,776）、別interpreter192 probe、24 byte再生成が一致。小幅256,904入力列と32bit512列のモデルを照合。source/history各8条件を各64問い合わせで回復した。24 fresh processの性能と、入力依存回転の12組の履歴長反例・104組のbit反例を保存。任意の観測履歴型難読化一般への否定ではない。

2026-10-21追補：[丸め格子の変換実験](shifted-rounding/README.md)。主32条件204,800呼出し、復元16条件102,400呼出し、量子化器16,380 probe、WABT384 probeが一致。48 binary再生成・5拒否対照も保存。108 fresh processで通常値・零・underflowを比較し、underflow時の改善がgrid0にもあることを確認した。4合成kernelの限定評価であり、全入力同値証明・一般アプリ・CPFloatそのものの比較は未実施。

2026-10-21追補：[型回復の対照実験](type-language-gate/README.md)。2入力族×5展開数×2形×raw/O3の40本、70,440呼出しと全memory不変を確認。Retypd76正常終了、1件15秒timeout、3未実行を分離。適応shape回復40/40、40binary再生成一致、36 fresh Node processの実行費用を保存。短いbatchの診断測定であり小差の性能優位を確定しない。独立した新発明を採用した実験ではない。

2026-10-21追補：[多項式lookup実験](polynomial-lookup/README.md)。主70条件92,230呼出し、WABT210probe、BigInt4,312比較、3誤変換反例、4拒否対照、56binary再生成一致。96 fresh Node processのhit/miss性能と36 fresh Python processの辞書回復を測定。多項式28条件を回復。元配置消去についてarray対照も同じになることを追加検査した。NotDec、NTL実装、人間の解析時間は未測定。

2026-10-21追補：[atomic codec実験](atomic-codec/README.md)。18正条件16,470呼出し、追加10条件4,000呼出し、実worker328,448正更新、WABT162probe、22byte再現、5拒否対照を保存。誤ANDと分割RMWの負例を分離し、後者のraceはscheduler依存と明記。15 fresh processの競合なし性能、14符号化条件の二点回復を保存した。全アプリ・全interleavingの証明ではない。

2026-10-21追補：[block表現の計画・実測](page-block-codec/README.md)。30正条件79,820呼出し比較・期待trap30,170で不一致0。12負条件中8に反例、0ページ4条件には反例なし。30fresh process、12回復条件、70別engine照合、6byte再現、4拒否対照を保存。監査v1のthreads flag不足はv2で修正し保護成果に数えない。APIとページ数を変えた同一合成プログラムであり、独立した30benchmarkではない。

2026-10-21追補：[odd-trace早期ゲート](../experiments/odd-trace-gate/README.md)。6正条件804比較・回復804比較・rawのtrace804比較、6負条件と3衝突例、小語長882条件、別engine6probe、O3正3本のbyte再現を記録。同じ134入力を各条件で使っている。先行性と回復のゲートで棄却したため、汎用compiler・性能統計は未実施であり、Phase5の全面評価完了とは扱わない。

2026-10-21追補：[copy-fiberの事前計画](copy-fiber/plan.md)と[実測](copy-fiber/analysis.md)。主10条件で圧縮2,620・全SHA410比較、回復20条件で圧縮5,240・全SHA820比較が一致。共通262入力/41messageの再利用である。18fresh process、4負例、3非対応拒否、10主byte再現、6別engine probeを保存。最終監査はaudit-v3。

2026-10-21追補：[copy互換codecの実測と再現](copy-centralizer/README.md)。32主条件22,016呼出し、8回復条件5,504呼出し、40 WABT/Node probe、28小モデル、4誤変換反例を保存。2workload計96 fresh processで全復号対照と比較。全8 native条件の直接回復は各32 read、0 writeで、検証済みcloneとbyte一致。

2026-10-21追補：[制約伝播の実測・再現](propagation-projection/README.md)。主48本19,176vector呼出しで値・全memory不一致0、WABT192probeとbyte再現48本を確認。回復24条件は全て等価式を生成し、各例6条件でbyte一致。主性能は同じO3を適用した80processで、1例だけCNF対照より約25%速く、3例は約16–54%遅い。性能用16本6,392呼出しも再照合した。入力分布、単回変換時間、初期のharness不備と測定条件修正を区別して保存した。

2026-10-21追補：[selector-quotientの実験と再現](selector-quotient/README.md)。事前計画に従い9,734条件103,592値を全列挙し、固定後続が成立する条件0。4例32本33,280呼出しのうち、正対象24本24,960呼出しで不一致0、反証対象8本では値不一致4,526・診断用上限trap 3,794。別実行器96呼出しと32本のbyte再現を確認した。正しさの必要条件を満たさない案なので実行性能の測定へ進めず、単回変換時間を性能比較として使わない。

2026-10-21追補：[零符号の遅延修復の検査](zero-sign-transport/README.md)。主88本585,728呼出しのうち正対象56本372,736呼出しは一致。candidate16本中4本に零符号不一致、零fallback16本は一致。追加6共有DAG108本では正対象84本106,176呼出し一致、candidate24本中8本に零符号不一致。120processの性能、WABT336probe、88本byte再現、丸め順序の4負例を保存。[分析](zero-sign-transport/analysis.md)。

2026-10-21追補：[有限環残差方式の追加評価](finite-ring-evaluation/README.md)。局所2,560呼出し、全SHA3,186呼出し、24trapに不一致なし。方式既知回復はraw/O3両方で成功し、6生成物のbyte再現とWABT10probeを確認した。5方式×5 fresh processの測定ではO3原型helper約832µs、129反復約50.3µs、全scratch回復版約0.257µs。保護費用の限界を示し、構成的提案としての採用と区別する。[実測表](../results/invention-20261021/finite-ring-report-v1/comparison.md)。

2026-10-21追補：[飽和値への零割当](saturation-anchor/README.md)。主48本で60,228,864 Wasm呼出し、6,864状態検査、全memory照合に不一致0。生成seedを与えない16問い合わせで全48本の共通置換を回復。初回240 processのwarmup懸念を記録して全条件を再測定し、主要240 processでは同じ符号化のmin版比約2–14%時間減、binary42bytes減を観測した。8比較中3比較のprocess範囲は重なる。近い先行構成・実用範囲・保護の弱さから、主発明の確立とは扱わない。[固定計画](saturation-anchor/plan.md)、[測定修正](saturation-anchor/measurement-amendment.md)、[実測表](../results/invention-20261021/saturation-anchor-report-v1/comparison.md)。

重複cell表現の追補（実験2026-10-19、記録2026-10-21）：[隣接pairの整合supportによる回復](overlap-cells/README.md)を実Wasm変換・回復器へ実装した。主・追加120条件、754,992呼出し、別VM1,197照合で不一致0、12負例、180本のbyte再現を保存。全96符号化条件は独立cell表へ回復した。診断処理を除いた最終計測でsingle比は解析本体約2.11–3.05倍、reader込み約1.02–1.40倍、実行約1.16–1.40倍、binary約2.62–2.87倍。費用増加はあるが、偽値・再符号化の追加優位性は未確認。符号化表、無効領域処理、common information分解の先行性を確認し、主特許候補には未採用。独立した新規性・有用な保護効果の主目標は未達。

resource破棄の追補（2026-10-19）：[Component Modelの所有handleによる計算移動](resource-trigger/README.md)を実coreからcomponentへ変換する形で実装した。主72条件・318,240呼出し、追加32条件・141,440呼出しで不一致0。主元/回復coreのBinaryen567照合、誤破棄順9反例、非対応5拒否、主144本のbyte再現を保存。104条件を公開canon結線・handle・内部slotの記号追跡で回復した。deferred/directは解析本体約1.10–1.29倍、実行約0.99–1.41倍だが、deferred/immediateは解析約0.95–1.09、実行約0.95–1.05で、生成順変更の追加効果は未確認。Jcoのrep bit30の不一致はslot番号を渡す設計へ修正し、失敗ログも保持した。実行形式の境界移動・標準destructorとの独立した差が弱く、主特許候補には不採用。新規で有効な主発明の確立は未達、研究を継続中。

分割carry-saveの追補（2026-10-19）：[マスク分割片のSIMD混載と総和の回復](carry-weave/README.md)を実装した。主90条件・574,830呼出し、追加40条件・255,480呼出しで不一致0。Binaryen1,260照合、縮小モデル124,828比較、誤carry9反例、180本の主byte再現を保存。全130条件から元項を回復。分割なしCSA比で解析本体約1.76–2.06、実行約1.35–1.59の費用増加はあるが、総和の保存則を逆に辿れば探索せず戻せる。CSA・MBA・既存圧縮木研究との独立した差が弱く、主特許候補には不採用。zero-paddingの4件は回復器の不足として修正し、耐性に数えない。主目標の新規性・有効性の確立は未達で、研究を継続中。

時間差SIMDの追補（2026-10-19）：[異なる論理時刻のlane混載と反証](temporal-lanes/README.md)を追加した。主72条件、34,560呼出し（期待trap2,160）で不一致0。Binaryen756照合、縮小モデル263,376比較、誤mask9反例、216本のbyte再現を保存。mixed/未変換の実行比1.228–3.732、mixed/自然配置の回復本体比0.894–1.089。主回復36/36に加え、phase値を使わず依存鎖からも36/36を元binaryへ回復した。時間変更・SLPの先行性と、追加保護効果が未確認であることを分けて記録し、主特許候補には不採用。readerのstack処理・shuffle重複処理による中断は耐性に数えない。主目標の独立した新規性・有効性は未達で、研究は継続中。

可逆混合レコード更新の追補（2026-10-19）：[read/write別局所計画と反証](cone-patch/README.md)を追加した。48条件32,256呼出し（期待trap9,216）で不一致0、Binaryen336照合、縮小モデル202,752比較。N=128で全回路/局所計画の実行比8.59–20.69、局所計画/未変換比1.54–11.57。ただし公開バイナリから係数を抽出し、符号化36条件の全snapshotを回復した。回復成功だけで棄却せず、計画による保護上の優位が未確認であることと、可逆回路書換え・EOC・WO2023077167A1との先行性を分けて記録した。主特許候補として不採用。主目標の独立した新規性・有効性は未達で、研究は継続中。

SIMD符号化表の追補（2026-10-19）：[全単射を合成した表と群の回復](isotope-swizzle/README.md)を実装・反証した。主30条件、708,480呼出しで不一致0、Binaryen480照合も一致。表12条件の全24表を元seedなしで回復。O3 table/decode実行比2.47–4.71、サイズ比3.72–5.72、回復本体0.79–3.39ms。解析費用の増加はあるが、局所的な群正規化で分割でき、Chowらの符号化表とSIMD表参照への直接の先行性も強い。主特許候補として不採用。実装不備・非対応を耐性に数えず、独立した新規性と有効性を備える主目標は未達、goalはactive。

型同値状態の追補（2026-10-19）：[再帰型groupへの状態識別の移動](type-identity/README.md)を実Wasmへ実装した。主42target＋42回復、203,490呼出し、追加12target＋12回復、58,140呼出しで不一致0。主GC系30/30を既存型正規化と整数ラベル化でMVPへ回復。group系24条件の22は通常GC版の回復先とbyte一致。126 fresh processでgroup数8・兄弟型32の通常GC比は実行約0.96–1.04、reader込み解析約0.90–1.05、後処理約1.09–1.25。追加保護優位性は未確認。Binaryen API648照合、全状態・記号/受理519照合とNodeの同じ519照合、3誤group反例、6非対応拒否、42target＋42回復のbyte再現を保存。解除器のnullable local初期値不備を別反例で検出・修正し主実験を再実行した。既知の型同値性・型変換との差は弱く主案に不採用。新発明3案には数えず、主目標は未達、goalはactive。

copy成立条件の追補（2026-10-19）：[未変更bulk copyと表現変換](copy-commutation/README.md)を検査。全域の固定表現が任意1セルcopyと可換なら全位置共通の1セル写像に限られることを紙上導出し、小モデルの全列挙で確認した。実Wasm32target、255,552呼出しで正の20targetは不一致0、意図的な負の12target全てに反例。整列pairの正例と、一方向copyだけでは48置換が残る小モデルを保存。WABT/Node128照合、32target＋32観測版のbyte再現、copy関数32/32不変を確認。初回の最適化器機能フラグ不足は設定エラーとして別記録。今回は新しい保護方式の評価ではなく、メモリ表現案の成立条件を絞る結果である。既知data refinementとの差と解析費用上の優位性は未確立。新発明3案には数えず、独自で有効な主発明と特許を目指す目標は未達、goalはactive。

並行演算グラフの追補（2026-10-19）：[共有memoryとatomicの早期反証](concurrent-frontier/README.md)を実Wasm変換器・実worker・方式既知の回復器へ実装した。主36target＋24回復、101,376呼出し、追加31target・72,912呼出し、WABT240呼出しで不一致0。24/24の主VM条件は依存順の展開で元と同じSSA式へ回復。108 fresh processでatomicの逐次VM比は実行約1.25〜2.07倍、解析約0.94〜1.08倍で、並行化の追加保護効果を未確認。2/4workerに複数担当者の実行を確認したが、全合法順の列挙は解析に不要だった。SCの小モデルと誤変換反例、4非対応拒否、36target＋24回復のbyte再現を保存。host待機、測定wrapper、循環fixtureの実装不備は修正し耐性に数えない。既存thread/Petri-net論文とUS11403372B2に対する独立した新規性も弱く主案に不採用。新しい発明3案には数えず、特許を目指す主目標は未達、goalはactive。


例外参照packetの追補（2026-10-19）：[条件の遅延解釈と共有](exception-packet/README.md)を実Wasmへ実装した。3方向を比較し、二タグの例外参照をSSA条件ごとに共有する案を検査した。主72 target＋72回復、147,456呼出しで不一致0。追加mutable条件等24,864呼出し、互換性・宣言順9,216呼出し、WABT288呼出しも一致。packet方式36/36を通常selectへ回復し、主全体でもcontrol outcomeは最大2。108 fresh processでK=48の共有はfreshより約6.6–12.4倍高速だが、通常helperより約81–143倍遅く、解析の追加費用は約2.5–3.5倍。SMTのscalar比較は68/72がunsat、4はunknown。別の交換・結合則照合が当該4を含む60/72で一致し、両検査の和集合は72/72。全binaryの形式証明ではない。72本の再生成byte一致、誤handler・nullの反例、4拒否対照を保存。DAG処理の不備、確認器のlocal上限、WABTの非null block型未対応は保護効果に数えない。例外難読化と通常の共通化に対する独自性・効果が弱く主案には不採用。新規で有効な主発明と特許性の確立は未達、goalはactive。

差分メモリ境界修復の追補（2026-10-19）：[符号化したままのbulk copy](difference-boundary/README.md)を限定した実Wasm変換器へ実装。隣接byteのXOR差分、copy前の2区間補正、copy後の境界2点修復と区間共有を検査した。主・追加120 targetと各観測用版の計256,080呼出し、20,080 trapで値・状態の不一致0。WABT360 check、112,130小幅モデル比較、4誤変換反例、3拒否対照を保存。60主binaryのbyte再現も一致。45 fresh processで8KiB近接copyの全復号版約5067nsに対し境界版約39ns、遠いcopyの区間共有は約2429→1249nsと高速化した。しかし累積XORで変換48条件すべてを元binaryへ回復。公開profileの索引化により照合順の費用を除いても追加の保護効果は未確認。索引v1のdata-count照合不備は修正し耐性に数えない。差分・scan・符号化計算の先行性と具体規則の未確立な新規性を区別し、主発明には不採用。独自で有効な難読化・特許候補の確立は未達、goalはactive。

入力依存の置換列書換えの追補（2026-10-19）：[支持制限付きHurwitz変換](hurwitz-support/README.md)を実Wasmへ実装。既知の幅5置換計算・固定基底変更・局所表融合と比較した。主100本と追加36本、計2,943,776呼出しで不一致0、WABT600呼出しも一致。主4非定数例＋1定数対照、追加2非定数例を分けて記録した。全66回復条件（非定数56、定数10）で元式と同じ正規ROBDDを得た。局所逆書換えが止まっても、出力に必要な5値の意味状態を追えば回復できる。通常O3後も変換は残るが、固定基底変更に対する意味解析時間比は約0.97–1.29、binaryは約3倍で、明確な追加優位性は未確認。90 fresh process、100主binaryのbyte再現、28,800＋8,192代数検査、誤交換反例と4拒否対照を保存。v1の再帰処理不備による中断は解析耐性に数えない。US20240045670A1・US9654280B2の関連記載と請求項を読んだ範囲を明記した。独立した新規性と効果が弱く主発明には不採用。主目標は未達、goalはactive。外部公開・push・出願は行っていない。

有限環の4点実行の追補（2026-10-19）：[次数によらない4点合成](nilpotent-stencil/README.md)をWasmへ実装。256の倍数の入力摂動により評価点変数の4次以上が消える性質を使い、各laneが非単射でも4結果から元出力を得る。主70本・300,160呼出し、追加60本・257,280呼出し、WABT420呼出しで不一致0。誤変換3種の反例、非単射4組、正の追加対照6本・25,728呼出しを検査。方式既知の定数係数射影で30/30条件を回復し、そのscalarモデルはSMTで同値。主70本のbyte再現も一致。共通Wasm内部loopの105 fresh processでは動的版が元の約4.1–5.7倍の時間を要し、元次数を増しても解析は保持次数3に閉じる。既知の自己還元・符号化計算との差と追加保護優位性が弱く主方式には不採用。独立した新規性の確立と特許を目指す主目標は未達、goalはactive。


入力依存SIMDレーン移送の追補（2026-10-19）：[4つの仮入力と動的レーン移送](lane-demand/README.md)を実Wasmへ実装。主56本・240,128呼出し、追加60本・257,280呼出し、WABT336呼出しで不一致0。回復24式のscalarモデルはSMTで元式と同値、主v2/v3の56本はbyte一致。通常O3後も移送は残るが、方式既知の解析では親子frameの差が相殺され、24/24条件を1レーン需要からscalarへ回復できた。動的版の有限な解析費用増は測定したものの、独立した新規性と十分な追加保護効果は未確立で主案に不採用。既存のSIMD VM・vector化・demanded-elements解析を近い先行技術として記録。独創的な新候補の数には加えない。位置を動かすだけでなく、必要な値を安く分離できない機構が次の検証課題。新規で有効な主発明・特許性の確立は未達、goalはactive。


出力履歴による状態消去の追補（2026-10-19）：[内部状態yを消す限定Wasm変換](output-recurrence/README.md)を実装。主32本・66,080呼出し、追加9本・18,585呼出し、WABT224呼出しで不一致0、主再実行32本byte一致。異なる元状態から同じ変換binaryになる3組を生成したが、8/8条件でw=b*yを持つ短い等価実装を回復し、共通検査器の24条件も同じcanonical binaryへ戻った。高次多項式への拡張でも商状態は閉じることを導出・97,380組で検査し、rotateは31条件でその閉性を壊す反例を保存。状態実現の既知原理との差と追加保護効果が弱く主案には不採用。独創的な新候補の数には加えない。新規で有効な主発明・特許性の確立は未達、goalはactive。


Relaxed SIMDの追補（2026-10-19）：[仕様上の選択をmaskへ運ぶ限定案](relaxed-carrier/README.md)を実Wasmへ実装。主48本・249,456呼出し、適応的解析等の追加54本・280,638呼出し、WABT計612呼出しで不一致0。主再実行48本byte一致。通常最適化には残るが、方式既知の共通解析ではdynamic maskと近い費用で6組すべてbyte一致の回復先へ戻った。直接maskを返す負の対照で、一般同値変換ではないことも確認。既知Boolean maskingとの技術差と追加の保護優位性が弱く主案には不採用、独創的新候補の数には加えない。新規で有効な主発明・特許性の確立は未達、goalはactive。


状態被覆の追補（2026-10-19）：[状態複製と商の回復費用](quotient-lift/README.md)を実Wasmへ実装。40主条件＋静的32/公開学習40 clone、112本・231,280呼出し・30,688 trapで不一致0。WABT672呼出し・2,688 memory probeも一致、再現112本byte一致。全状態解析費用は増えたが、95継続語の代表解析では最大33物理状態で全32条件を回復し、公開I/O学習のquery transcriptは複製数を変えても同一だった。長い例外語を見逃す負の対照も保存。既知の状態分割との技術差が弱く主案には不採用。新規で有効な主発明・特許性の確立は未達、goalはactive。


零長副作用述語化の追補（2026-10-19）：[追加memoryを使わないbulk述語化](zero-extent/README.md)を実Wasmへ実装。48主条件＋48回復、239,616呼出し・177,785 trapで値/trap/全memoryの不一致0。WABT384 writer・7,296 memory probeも一致し、再現で96本のbyte一致を確認。4つの誤変換を反例で検出。方式既知の解析はlengthから効果条件を露出でき、O3 mixedのflat比で実行約1.73–8.56倍・解析約1.68–4.90倍。費用増加を無視しないが、EP1947584B1/MERIT/GCCとの具体差が弱いため主案には不採用。新規で有効な主発明・特許性の確立は未達、goalはactive。


書込み失敗境界の被覆候補（2026-10-18）：[書込み被覆の測定](write-frontier/analysis.md)を追加。72主条件、静的回復72本、216 fresh process、bit/byte解析、同store数の乱択対照を比較。400モデル132,000比較、誤変換2件、拒否3件、最小被覆の独立BFSも保存。公開I/O回復72本の82,098比較は主実験と入力が重複するため独立標本数には合算しない。

共同多項式更新候補（2026-10-18）：[共同多項式候補の実測](polynomial-carrier/analysis.md)を追加。3カーネル×4方式×raw/O2/O3、108 fresh process、36更新則回復、主72本75,024呼出し、WABT 288呼出し、3,072任意状態、追加72基底条件を保存。coupled O3未変換側の旧抽出未対応1件を修正し、最終条件の未対応・crash・timeout・誤答を各0とした。

状態重なりNFA候補（2026-10-18）：[状態重なり候補の実測・再現](overlap-automata/README.md)を追加。3カーネル×4方式×raw/O2/O3、回復36本、4解析経路、3 fresh process/条件を比較した。70モデル条件と120例のsimulation簡約検査、unsafe mergeとbit63の対照も別記録。旧screenのdead-state得点、旧解析器の未対応4件、同時実行された旧性能ログを主結果から区別する。

2026-10-18追補：[typed-relayの計画](typed-relay/plan.md)・[結果](typed-relay/README.md)。54主条件＋54回復、123,120呼出しの値/trap/全memory一致、Binaryen interpreter432呼出し一致。WABT99一致・6値不一致・3timeoutは別集計。270のcall-string解析条件、54summary回復、raw18条件のAST一致、162 fresh processを保存。別出力先の再現で108バイナリ一致。繰返し実験の呼出し数は独立標本に合算しない。

2026-10-18追補：[区間上書き候補の早期計画](interval-write/plan.md)と[実測](interval-write/README.md)。48本＋回復48本、1,975,680呼出し、WABT384呼出しで不一致0。5拒否対照、48/48の式同値性、144 fresh process、memory/RSS/変換時間を保存した。主値は対照の解析を改善した[interval-write-v3](../results/invention-20261018/interval-write-v3/comparison.md)。v1から96主バイナリは同一だが、反復実験の呼出し数を独立標本に合算しない。

2026-10-18追補：[suffix輸送の事前計画](suffix-transport/plan.md)と[実測・再現](suffix-transport/README.md)を追加。6例×3方式×raw/O2/O3、54本と回復54本、249,804呼出し、WABT432呼出しで不一致0。54/54のDFA回復と言語同値性、162 fresh processの性能、RSS、変換時間を保存。追加監査付き[全再現](../results/invention-20261018/suffix-transport-replay-v2/audit.json)で108バイナリ一致、保護36条件の代数関係と3種の拒否対照を確認した。解析と実行の費用を分けて評価し、過去の実験件数には合算しない。

2026-10-18追補：[SIMD非正規mask](simd-quotient/README.md)の実測を追加。3kernel×3表現×3最適化の27本と回復27本、3,649,536呼出し。WABT108呼出し、byte代数590,080比較、81 fresh processを保存。全27条件を元と同じ条件式へ回復し、実行コストと解析コストを独立に比較。replayでは54バイナリが一致し、誤ったwrap減算の対照を検出した。主データは[simd-quotient-v2](../results/invention-20261018/simd-quotient-v2/)、一括再現は[replay-v1](../results/invention-20261018/simd-quotient-replay-v1/)。

2026-10-18追補：[bit依存フィードバックの事前仕様](bit-feedback/plan.md)と[実測](bit-feedback/README.md)を追加。主144条件646,272呼出し、補助121,176呼出し、WABT288呼出し、小幅全列挙209,664組で不一致0。72/72の同一Boolean DAG回復、更新数不足の負例拒否、216 fresh process、解析時間9反復を保存。主データは[bit-feedback-v3](../results/invention-20261018/bit-feedback-v3/)。v1の読取クラッシュ、v2の更新上界未検査版を区別する。

継続する別候補の実測：[stack-cycle](stack-cycle/README.md)。4カーネル×7方式×3最適化=84条件、復元84本。611,730主呼出し、30,990補助型呼出し、WABT336呼出しで値/trap/全memoryの不一致0。trap理由差52件を別記録。DP全列挙200小例、誤state対照、方式既知の解析、252 fresh processの性能を保存。再現先でも生成から監査まで完走した。これらを以下の旧候補の件数へ合算しない。

追加試作：[丸め補正の領域変換の事前計画](rounding-region/plan.md)と[実測・再現方法](rounding-region/README.md)。5式×3方式×3最適化の45本、復元後45本、404,388呼出しとWABT180呼出しで不一致0。誤り対照・範囲外拒否・方式既知の抽出・135 fresh-process性能を検査し、別出力先で一括再現した。以下の式再合成実験とは別の条件で、件数を合算しない。

継続探索：[接続表現の実行前計画](connectivity-elimination/plan.md)に基づき、実Wasm75条件・復元後75条件、アブレーション、BDD復元、性能・memory・変換時間、別エンジンを検査した。[結果と限界](connectivity-elimination/README.md)。一括再現も別出力先で完走した。以下の式再合成75条件と別の研究区間で、件数を合算しない。

別の探索的実験：[メモリ射影の設計](memory-quotient/design.md)を先に保存して実行した。[結果](memory-quotient/README.md)は54条件・3,553,335実行、18条件の公開I/O復元、162fresh processでの性能・RSS、別エンジン・境界・逆像数の監査を含む。局所XORが非単射でも全体から復元可能な場合と、非一意な代表から等価実装へ戻せる場合を分けた。本文の75条件とは別の探索である。

追加の探索的検査：[更新の2回合成](checkpoint-composition/README.md)。係数根の全数・ランダム検査、54実Wasmのvalidateと14,256実行、18条件の公開I/O cloneの4,752実行を保存した。全18条件で係数から再分解できるため早期棄却。一般の変換器、実行性能・RSS・変換時間の本測定は行っていない。以下の75条件への追加・差し替えではなく、別の探索記録である。

最新の探索的実験：[GC参照共有回路](alias-circuit/README.md)。27条件・115,776実行、全共有パターン135実行、最適化後の適応的解除、81個の独立processでの時間・RSS測定、公開I/O回復と式同値性照合を保存。事前登録ではなく、以下の75条件とは別の研究区間である。小例が公開I/Oから学習可能であるため、主たる強度比較には用いない。

継続研究は別計画で実施：[可変table](table-transport/design.md)、[対称状態縮約](symmetric-state/design.md)。後者の正当性・適応的解除・性能・RSS・変換時間・再現結果は [報告](symmetric-state/README.md)。以下の式再合成の事前計画や数値には混ぜない。

2026-10-18に固定した計画。以下の仮説・成功条件を変更せず実行し、末尾に結果と逸脱を追記した。過去の2bit実験と2つの棄却ゲートは別の探索的結果として保持する。

## 仮説

H1：出力だけで1代表を選ぶ探索に比べ、観測文脈を保持する方法は、同じ生成・実行コストの範囲で、事前固定した実在の中間計算の復元を難しくする候補を残せる。

H2：その差はi32意味保存、O2/O3後の実Wasm、方式を知る解析を通しても残る。

H1のみが成立しても実用的な保護とは呼ばない。探索数やprofile次元は主指標にしない。

## 比較とアブレーション

同じ入力バイナリに対して、plain、通常の出力・コストのみの代表選択、同値候補からseed固定で選ぶ方式、観測集合による選択、基本MBAを比較する。基本MBAは著者ツールの再現ではない。全方式を同じWABT/Binaryen・raw/O2/O3条件に置く。対象領域や関数境界を変えて見かけのコストをそろえない。

同じ候補poolでの選択比較と、候補生成中の枝刈り比較を別にする。前者は選択方針の効果、後者は探索の効率・候補欠落の効果を測る。予算や候補poolが異なる結果を一つの改善率に混ぜない。

## 正当性

入力・出力とも標準validatorを通す。変換式はmod2^32の係数辞書が一致したもののみ。境界値、overflow、乱数、繰り返し呼出しで差分検査。式外のstore/call/trapがある対照も含め、変換境界を越えた評価の複製・移動を検出する。別エンジンが利用できれば実行し、利用できなければ未実施とする。

## 解析

対象は元プログラムの実在する内部計算として候補生成前に凍結する。全入力・定数・途中値・最終出力を観測に含む。構文木から正確に式を抽出した解析と、実測値からの復元を区別する。0/1/2演算の復元、代数正規化、因数分解可能性、元入力からの再計算を比較する。未知の汎用逆コンパイラを破ったとは主張しない。

成功、誤答、未対応、crash、timeout、資源上限、変換適用箇所なしを別列にする。保護対象の復元率と費用が主指標で、命令数は補助指標。正解式の検証は未使用入力と、可能な場合は正確な式同値判定で行う。

## 性能

サイズ、変換時間、生成時メモリ、実行時線形memory、プロセスpeak memory、実行時間を区別する。実行時間はWasm内batchでホスト境界を減らし、warmup後に同一入力の9反復以上、均衡した順序を使う。中央値・四分位範囲・生値を保存する。最初の試行で固定した回数を変更する場合は理由と旧値を残す。

同じ演算数だけを「同程度のコスト」とせず、実時間とサイズのtrade-offを報告する。機械・エンジン・flags・全SHAを保存し、他のプログラムや機械へ一般化しない。

## 成功条件と失敗時の処理

候補保持の差、実在する対象への差、通常最適化後の差、適応的解析後の差を順に判定する。少なくとも3つの異なる入力プログラムで、元や基本MBAより有用な差が観測できなければ、一般的な有効性は支持しない。3例だけで一般性を証明したとはしない。

未達の場合は理由を、生成器の未完成、候補の欠落、そもそも候補poolに効果がない、最適化による消失、適応的復元、許容できないコストに分ける。成功条件を後から小さくしない。負の研究成果も、必要な実装・比較・草稿をそろえた後に最終監査する。

## 実行した固定条件

主記録は`results/invention-20261018/observation-suite-v2/plan.json`。候補生成前にプログラムと保護対象を保存し、manifestに計画のSHA-256を記録した。5個の人工整数カーネル×5方式×raw/O2/O3、75条件。4個に保護対象があり、determinant-controlは対象なし。方式はplain、output-only、seed固定random、frontier、基本MBAである。MBAはaddをxor/and/shiftへ置換する自作対照で、SaMBA/LOKI/WASMixerを実行したものではない。

各条件で境界6値の3重直積216と乱数512、計728入力。独立BigInt参照と通常run、観測用runを比較し、checked関数では先行store、返り値、範囲外loadのtrap、全65,536byteを照合した。75×728=54,600入力条件、3種類の関数呼出し計163,800件。trap条件26,250。不一致0。入力は方式間で共有し、独立乱数54,600個とは数えない。別エンジンWABT wasm-interpでは32入力×75条件=2,400件のrun出力が一致した。

実観測の復元には12訓練・128holdout入力、最大2演算、100万試行上限を固定した。target-value oracleを持つモデル。全60対象条件が成功し、15条件は対象なし。失敗・未対応・crash・timeout・予算上限はそれぞれ0。全復元式を独立SymPy実装で正規化し、対象とのmod2^32係数一致を確認した。75出力にも同じ照合を行った。Z3の負の対照3件は不一致を検出した。

## 性能設定

Windows build26100、Intel Core i9-11900K、Python3.9.0、Node24.15.0/V8 13.6.233.17-node.48、WABT1.0.42、Binaryen133。Node flagsは`--no-liftoff --no-wasm-tier-up --no-wasm-lazy-compilation --trace-wasm-compilation-times`。全moduleを同期コンパイルし、12batchのwarmup後、200,000反復/batchを15block。各カーネル内の15条件を循環Latin順序で測り、全条件が各順序位置を1回占める。計測区間内にコンパイルのログは0件。CPU固定・専用機ではない。

実行時間はWasm batch内の反復単位であり、純粋な関数呼出しlatencyではない。LCG、入力生成、累積、loopを含み、Binaryen/V8のinlineも含む。同一blockのplainとの比と中央値・Q1・Q3を保存。単一host・単一process sessionの探索的測定なので統計的優越性を主張しない。

線形memoryと、別の75個のfresh Node processのpeak RSSを測定した。Node全体のpeak41,532–42,428KiBには起動・compilerが含まれ、Wasmだけの消費ではない。変換は方式×カーネルごとに3 fresh Python process、60試行。Python親のpeak working setと経過時間を測ったが、WABT子プロセスのpeakの合計は未測定。最大値・生値・単位を保存した。

## アブレーションと原因診断

同じ96候補poolで、出力/コスト選択、random、frontierを比較。さらに事後診断`ablation.json`で、対象復元の採点は残し、frontierフィルタのみを外した。4例とも選択式の演算数と復元追加演算数は同じで、3例では式も一致した。最大構文サイズを選ぶ対照は式モデルのみで、SaMBAの再現ではない。

|カーネル|pool|非支配候補|pool全体の復元0/1/2演算|frontierとフィルタなしの候補演算数/復元演算数|
|---|---:|---:|---|---|
|product|96|12|66/26/4|9/2|
|score-square|96|4|96/0/0|10/0|
|interpolation|96|17|95/1/0|10/1|
|cubic-product|96|6|52/40/4|8/2|

候補生成中の枝刈り比較は実装していない。本実装は生成後のフィルタなので、合成探索自体を高速化したとは主張しない。CLIのoutput-only/randomも共通の診断としてfrontierを計算するため、変換時間は各方針の理想実装同士の速度比較ではない。

## 仮説の判定と変更履歴

H1の弱い形（1代表より復元演算数の大きい式がある）は3例で観測したが、同一実行費用での有用性という成功条件は未達。H2について、0–2演算という小差はO2/O3後にも残ったものの、全件を適応的に復元できた。実用的解析耐性は支持されずCは不採用。

失敗の主因は、選択が有用な候補を捨てたことではなく、今回のpoolに強い候補がないこと。全出力は代数正規化可能だった。新規性のないビット演算追加や探索予算増加で延命せず、上位案を無条件に2つ実装することもしなかった。A/Bの既存反証を覆す規則がないためである。

- suite-v1：非同期WebAssembly.instantiateを用いた。固定flags下でPromise解決前にprocessが終了し、出力が未完成になった。この環境で単体再現もした。Node一般の不具合と断定せず、測定には使わない。
- suite-v2：同期Module/Instanceへ修正して全結果を取得。v1を上書きしなかった。
- 追加変換資源測定の初回はcross-engine検査と冒頭が重なったため、`transform-resources/`は診断用とした。`transform-resources-sequential/`を単独で再実行し主表に採用。
- アブレーション・独立式検証・別エンジン検査は主計画を実装した後の追加検証。初回の事前登録済み実験に見せかけない。

全条件の数値は[比較表](../results/invention-20261018/observation-suite-v2/comparison.md)、[CSV](../results/invention-20261018/observation-suite-v2/comparison.csv)。機械集計・raw logs・ハッシュは同じディレクトリにある。

## 追加比較：既知point方式のexactなWasm実装

2026-10-21の別系列：[位置依存表現のcopy後補正](bulk-rebase/README.md)。44targetの34,144呼出しと11,220全memory状態、WABT120呼出し、小モデル112,130件、4誤変換、8拒否対照、44byte再現を保存。適応復号は31問い合わせで44/44回復。270 fresh processの54条件で直接SIMD対照への速度優位を未確認、コードサイズ354bytes減。主方式への不採用理由と測定の範囲は[分析](bulk-rebase/analysis.md)。本文の75条件に合算しない。

[群上rolling照合](rolling-point/README.md)は別の比較区間として保存した。主27条件、端点24条件、多倍長演算、WABT別engine、方式既知でprefix/suffixを与えた54回復、81 fresh-process性能測定を含む。本文の75条件には合算しない。普通の検索に対する効率の達成や独立した新原理を示せず不採用。初回の検証器エラーと修正後の実行を分け、低entropyでの回復と完全未知patternの回復を混同しない。

## 2026-10-23：有限回更新系の追加実験

[再現手順](hidden-filtration/README.md)、[実測表](../results/invention-20261023/hidden-filtration-report-v1/report.md)。主307,656呼出し、追加回復153,828呼出し、scratch4,608、WABT96が一致。SMTは回復18pureモデルについてUNSAT。36process・252batchの時間/size/memory/変換時間を保存。初期解析器のtimeoutを保護成功に数えない。

## 2026-10-23追補：Boolean補正器3段階

[再現手順](boolean-feedback/README.md)と[集計](../results/invention-20261023/boolean-feedback-report-v1/report.md)。bitwise主179,466、word主194,502、切替主102,552呼出しで不一致0。各回復版・SMT・WABT・任意scratchを別集計した。wordは元版約237–266倍、切替版は固定補正約3.5–3.7倍の実行費用。全数分類と実binaryの効果を分離して報告する。

## 2026-10-23追補：状態付き切替グラフの全体合成

[実験前計画](rotor-synthesis/plan.md)と[実測](../results/invention-20261023/rotor-synthesis-report-v1/report.md)。共通評価器と直接命令化の各24binaryを115,992呼出しずつ比較し、不一致0。別BDD回復6binaryは28,998呼出し一致。入力再利用を独立標本として合算しない。byte再現18本、WABT72呼出し。主性能45fresh process×7batch、tightのO3を0.464〜0.714msで回復。xor3の有限合成UNSATを一般的不可能性と扱わない。

## 更新状態の商と公開更新による回復（2026-10-23）

[実測・証拠823ファイル](../results/invention-20261023/mutation-quotient-report-v1/report.md)。主90本448,230呼出し（trap16,110）、診断54本268,938呼出し（trap9,666）、I/O回復54本268,938呼出しが一致。WABT324呼出し、90本byte再生成、6件SMT閉性、小幅1,118,464比較も確認。36 fresh process/252batchでcanonicalは元の約1.58〜1.78倍、representativeは約0.998〜1.013倍。linear memoryは全版64KiB。入力再利用・サイズ違いを独立ベンチマーク数にしない。

## 部分文字列をまたぐ文法変換と三次係数からの解除（2026-10-23）

[実測レポート](../results/invention-20261023/substring-shear-report-v1/report.md)。主120本49,640呼出し、四次追加28本9,968呼出し、不一致0。診断66本27,302呼出しでtrap前後の全memory不変、別WABT330呼出し一致。回復は主54/54、追加12/12。主3文法の実行時間は元の約1.43〜1.65倍、108process/756batch。有限系432件と小幅算術5,460対も検査。旧不完全run、再利用した入力、未測定範囲を区別した。

## コピーの観測引戻しの初期ゲート（2026-10-23）

[range-pullbackの実測](../results/invention-20261023/range-pullback-report-v1/report.md)。主36本92,544呼出し、11,760期待trapで不一致0。小モデル1,115,334 origin比較、別WABT144呼出しも一致。誤変換12本全てで反例。回復12/12は元rawとbyte一致。性能27process/189batchでは疎な1byte読出しに限定した最適化効果を測った。初回の短い計測batchは採用せずruntime-v2を確定値にした。

## 可変二表の接続更新と履歴なし回復（2026-10-23）

[mutable-factor実測](../results/invention-20261023/mutable-factor-report-v1/report.md)。主60本126,300呼出し、診断36本75,780呼出し、計202,080で不一致0。全小モデル1,586,115比較、Z3一更新UNSAT、別WABT240呼出し。負例6個は全て検出。回復24/24は元rawとbyte一致。108process/756batchの実行費用は元の約1.40–1.99倍で、追加保護は未確認。

## 剰余表現とWasm整数wrapの成立性ゲート（2026-10-23）

[実装・測定](residue-wrap/README.md)。既知RNCの明示した移植規則を検査し、odd版全6条件で誤答、二修正版を含む正24条件101,208呼出しで一致した。aligned版はraw/O3全6条件を元とbyte一致するWasmへ回復。修正版は元の約2.76–15.25倍の実行時間となり、主特許候補には不採用。著者実装のバグ、RNS一般の不可能性、新しい環の定理は主張しない。 別WABT正192・負48・回帰16呼出し、30本byte再現、8拒否対照、縮小幅524,256比較、6補題UNSAT、36process/252batchを保存した。

## 現memoryを使う共有退避の生成（2026-10-23）

[共有退避の生成器](side-save/README.md)を実装。同じBを保ち、入口保存次元を4→1、32→4、10→1へ削減した。正37,184呼出し・期待trap19,152で一致し、rotate32の実行中央値は同じBのbasis対照より約13.8%短縮。一方temporaryとcode sizeは増え、既存回復器がbasis/side各12条件を元Wasmへ戻した。coded side-informationとの近さから独立した新難読化・特許性は未確立。総メモリ削減とは主張せず、費用改善の補助部品として保持する。 小モデル6,048問題と追加1,000問題で最小subspace探索と一致。WABT294呼出し、168trap、54本byte再現、3未対応拒否、27process/189batchを保存した。


## Disrobe v0.10.6 baseline (2026-10-23)

[実測と再現方法](../results/invention-20261023/disrobe-report-v1/report.md)。Disrobe v0.10.6を公式checksum確認後に27入力へ適用した。新発明の件数には加えない。


- 未変換リスト9本：C/JSON/WAT生成は正常終了。生成WATはvalidationを通るが初期dataが欠落し、5,148呼出し中504が不一致。正解dataを戻す診断は全件一致。
- 整数式18本：生成WATの75,906呼出しで不一致0。別deob処理の18出力は入力とbyte一致し、既存の適応射影による回復を否定しない。
- Cは固定offsetのi32 loadと局所変数へ戻るが、リストのnext pointer型・record strideの回復は確認できない。Cの再コンパイルは未実施。

この測定により『出力ファイルがある』『Wasm validationに通る』『正しく実行する』『構造を回復する』を別の項目として管理する。NotDecの代替実測とは扱わない。


## 遷移二乗による双模倣評価（2026-10-23）

[遷移二乗と双模倣評価](transition-square/README.md)を実Wasmへ実装した。主54条件106,488呼出し、境界48条件24,960呼出しは一致したが、公開行列の平方根とBoolean抽出で主24条件・境界12条件をすべて回復。同じgraph評価器に対して約26–37%高速化した一方、元の式比約811–8,643倍の実行費用。回路還元・行列関数の先行性と公開逆算から主特許候補には不採用。[実測](../results/invention-20261023/transition-square-report-v1/report.md)。

682小graph・32,916partitionの全数検査、source式と抽出BDD24件のSMT UNSAT、別WABT162呼出し、3拒否対照、36process/252batch、反復counter8,736呼出しを保存。v1のflag不足、v2のO3未対応は保護効果に数えず、v3を主値とした。


## 有限精度の観測閉包と選択入力回復（2026-10-23）

[有限精度の観測閉包](observer-closure/README.md)を自動生成し、実Wasmへ実装した。主30正条件780,090 API呼出しは一致したが、全12変換を10step観測で小さな更新へ回復。reset/peekを削った追試でも全12変換を22stepで回復し、491,520stepは一致した。実行費用は元の約5.18–10.05倍で、既知の観測実現・多項式持上げを超える新規性と保護優位は未確立。主特許候補には不採用。[実測と再現](../results/invention-20261023/observer-closure-report-v1/report.md)。

3人工kernel、raw/O3、full/quotient、正当性を破るbad対照を比較。小幅42閉包524,256状態入力対、主12+追試12の関数係数証明、WABT360step・90最終観測、36process252batchを保存。回復器のcandidate出力と別途の証明を区別する。


## 非線形共有退避の生成と限界（2026-10-23）

[非線形共有退避](nonlinear-save/README.md)を実Wasmへ実装した。探索600例中1例と独立holdout600例中1例で、最良線形保存2bitに対して1bitを達成。主42条件40,362呼出しと追試14条件12,614呼出しは一致した。ただし公開APIから全24変換条件を同等遷移表へ回復でき、既知のfunctional index coding・cographとの差も弱い。表生成の補助的最適化として保存し、主たる難読化発明には不採用。[実測と再現](../results/invention-20261023/nonlinear-save-report-v1/report.md)。

全8!の3bit置換40,320例は線形に対するbit削減0。主・holdoutの正条件56件は一致、負対照8件は反例あり。WABT420run・294期待trap、性能45process315batch。改善主例のrepair表192→96byte、O3 binary649→606byteだが、saved i32 local一つ・1page memoryは変わらず。


## 非可逆な解釈状態の同期（2026-10-23）

[重みを伴う解釈状態の同期](synchronizing-decoder/README.md)を実Wasmへ実装し、主54条件62,208呼出しと代表回復12条件13,824呼出しの一致を確認した。非可逆遷移で全入口を同じ計算へ収束できたが、代表状態一つで全12sync条件を全状態解析とbyte一致のコードへ回復。元の約3.71–30.80倍の実行費用に対して追加保護の根拠が弱く、weighted synchronizationにも先行性があるため主案に不採用。[実測と再現](../results/invention-20261023/synchronizing-decoder-report-v1/report.md)。

96gateの係数検査、縮小幅9,216組、WABT324呼出し、24回復のbyte再生成、12誤重み対照、profile外拒否、63process441batchを保存。元のifは維持し、任意CFGの合流を処理するcompilerまでは実装していない。原始操作段階の反証から拡張を見送った。
