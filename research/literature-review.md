# WebAssembly難読化の発明研究：文献調査

2026-10-23追補：[MOCCO 2026とdistorted interpreter講義資料の確認範囲](profile-boundary/literature-note.md)。構造指標の改善と実際の解析耐性、別評価器への移行と独立した生成規則を区別する。deep integration論文は書誌確認に留まり、本文・具体手順・評価数値は今回未確認。

2026-10-23追補：[span program・入力依存行列・LOKIとの対応](span-mask/prior-art.md)と、[差分計算・dirty ancilla・動的データ配置の先行性](span-mask/next-gates.md)を追加した。一次資料の実際の閲読範囲と未読部分を区別する。今回の主構成は既知原理との近さから新規と断言できない。[借用メモリの実験](catalytic-memory/README.md)はGidney2017の既知原理との対応も記録した。

2026-10-22追補：[循環共有の文献記録](conditional-causality/plan.md)。Neiroukh/Edwards/Song, *Transforming Cyclic Circuits Into Acyclic Equivalents*, IEEE TCAD27(10):1775–1787, 2008, DOI10.1109/TCAD.2008.2003305の導入・Prior Workに加え§V Theorem2、§VI冒頭、§VIII冒頭を読んだ。条件別scheduleの合成と任意初期値からの実行が今回の構成に直接近い。Riedel/Bruck, DAC2003の著者本文も今回取得し導入を確認した。著者実装や全評価の再現ではない。[追加読解と対応](conditional-causality/analysis.md)。

2026-10-22追加：[相互作用改良の関連資料](energy-descent/interactions-analysis.md)。Björklund–Sandberg–VorobyovのPSI2003関連公開版の冒頭・§2・§3冒頭を読み、擬Boolean局所改善の既知枠組みを確認。CUPBFの全face一意性を本試作へ誤って帰属しない。メモリ方向ではUS7975149B2とUS9117094B2の検索抽出にあるsplay/再配置、ChazelleほかSODA2004 Bloomier filterの著者書誌と本文導入を確認。全文未読・請求項未精査の範囲を明記し、法的判断や新規性の不存在証明にしない。

2026-10-22追加：[全体収束の改良と先行資料](energy-descent/relaxed-analysis.md)。Dechter *Bucket elimination: A unifying framework for reasoning*, Artificial Intelligence113(1–2),1999, DOI10.1016/S0004-3702(99)00059-4の著者側PDF§8・Figure25・Theorem11を確認。Odense–d'Avila Garcez *A semantic framework for neurosymbolic computation*, Artificial Intelligence340,2025, DOI10.1016/j.artint.2024.104273の書誌とHopfield/penalty logicにおける局所最小の議論を確認。両者は査読論文。今回の特定CEGIS生成器が既出と断定せず、一般的な正当性条件と回復原理の先行性を区別した。

2026-10-22追補：[energy評価の先行技術](energy-descent/prior-art.md)。Pinkasの1991年誌論文とWUCS-91-31/52の書誌・abstract、Pinkas–Dechter JAIR1995の導入とenergy/木DP部分、Lucas2014の制約weightに関する本文を確認。1991年report本文取得は403で、厳密な子重み式を読んだとは扱わない。継続案にはLu PEPM2019の公式abstractを比較。査読誌、Technical Report、本文未取得を区別した。

2026-10-22追補：[有限環上の状態と漸化式](torsion-state/prior-art.md)。Reeds・Sloane、SIAM J. Comput.1985 *Shift Register Synthesis (Modulo m)*（DOI10.1137/0214038）の著者PDFの要旨・§1–3・§4主要更新規則を確認。合成数modulusと非可逆要素を含む漸化式合成は既知である。Napp・Pinto・Rocha、LAA2022 *State representations of convolutional codes over a finite ring*（DOI10.1016/j.laa.2021.12.006）は出版社一次検索結果の書誌・要旨のみ。本文取得に失敗しており具体的な生成規則を同論文の内容と断定しない。

2026-10-22追補：[格納領域再利用の照合](lifetime-overlay/prior-art.md)。LLVM公式StackColoring sourceの導入・生存区間と分岐の例、MemorySSAのDef/Use/Phiとwalker、Wasm memory命令仕様を確認した。これらは一次実装・技術文書であり査読論文とは区別する。Baek・Lee、TSE2026 *Deobfuscation of Control Flow Flattening Based on Abstract Interpretation*（DOI 10.1109/TSE.2026.3659437）は出版社要旨・書誌と著者一覧のみ確認。本文の評価値・アルゴリズム詳細は未確認。今回の部分重複の生成と回復を、既知のstack coloring・到達定義と照合した。

2026-10-22追補：[差分評価と有限環補間の先行資料](dyadic-difference/prior-art.md)。Paige–Koenig TOPLAS1982の有限差分化、GeelenほかEUROCRYPT2023論文の著者博士論文収録章にあるfalling factorial・零多項式・縮約差分補間を確認。Singmaster1974は出版社由来の書誌・要旨だけで本文未取得と区別した。差分や係数の非一意性を新規原理に数えない。

2026-10-22追補：[情報損失と修復の先行資料](loss-flag/prior-art.md)。PLDI2018のOSR論文のlive/availとmemory補償、MSR2008 Data Randomizationの等価クラスを確認した。CC2012 Backstrokeは出版社の書誌・要旨を確認し、本文取得失敗を区別した。現在の値から必要状態を再構成して保存を減らす一般論と、制約による表現選択は先行する。本案はWasm copyの全trap prefixから具体的codecと修復器を生成するが、独立した新規性は未確立。

2026-10-22追補：[妥当性による条件計算の先行資料](validation-value/prior-art.md)。Wasm validation algorithmのunreachable/control frameとJS validate仕様、BABELの要旨・導入・§2、Pucella/Schneider 2010の表紙・要旨・導入を確認した。言語機構を計算媒体にする一般論は既知。type checkingと難読化を比較する論文を、検証器へ条件式を移す同一手法と誤認しない。具体的な生成規則の初出は未確定であり、今回の試作の全6条件はvalidatorの要約で回復した。

2026-10-22追補：[waitと共有field混合の先行資料](wait-partition/prior-art.md)。Wasm Threads公式提案のwait/notify、LLVM AtomicExpandPassの部分word更新とCAS loop、Tigress Encode Dataのautomatic、Burckhardt 2007博士論文のPacked Words節を確認した。packing・CAS化・演算に合う表現選択は既知。観測射影を保つ具体的規則との差分候補はあるが、同一先行例が検索で見つからないことを新規性の証明にしない。

2026-10-22追補：[再帰frame混合の先行技術比較](recursive-frame/prior-art.md)。Fukushima/Kiyomoto/Tanaka 2006の発行元PDFを今回取得し、複数変数のaffine混合、動的解析への限界、実験のoverflowによる機能差を該当箇所で確認した。Drape 2004の§3.2と§8.1.4、US8286251B2の説明と請求項1–5も照合。LuのCPS拡張プレプリント、MFCS2022 accessible-stack学習論文は今回読んだ範囲を区別した。call frameへ動的表現を置く一般論だけでは独立した新規性を支持しない。

2026-10-22追補：[小数部からの余り計算と先行技術](fractional-pair/prior-art.md)。Lemire–Kaser–KurzのSPE2019論文公開v3 §3/Theorem3.3、Drape2004博士論文§6.1、US7013320B2の概要・請求項1/10、Wasm unsigned div/rem仕様を確認した。可変除数・分子摂動・gcdに基づく範囲生成という具体的差分と、独立した新規性の未確立を区別する。取得できなかった別PDF、未照合の全特許ファミリーを読了扱いにしない。

2026-10-22追補：[飽和商表現に関する先行資料](saturation-buckets/prior-art.md)。Wasm SIMD公式仕様、Tigress Encode Data、US7171438B2の飽和認識に関する説明を確認した。演算適合codecやnative飽和への置換は既存技術である。Glesner–Blechの整数定数畳み込み論文は出版社由来の書誌・要旨のみで、本文未取得と区別した。今回の具体的生成則と同一の先行例の有無は未確定であり、検索で見つからないことを新規性の証明にはしない。

2026-10-22追補：[有限領域の同符号混合の先行研究](sign-coherent/prior-art.md)。MishkinほかICML 2022のactivation coneと同patternのmerge、WangほかICLR 2022の整列・分割を本文の指定箇所で確認。有限格子で非比例な係数を混ぜることだけでは独立した新規性の根拠にならない。WAMO本文未取得は未解決として明記した。

2026-10-21追補：[Hasse係数算術と微分関連特許](hasse-gate/prior-art.md)。Forbes–Shpilkaの公開版§5 Definition5.1/Lemma5.4を読み、可換環での係数伝播が既知と確認した。US8312260B2は検索で得た要旨・説明・請求項1の抽出のみで、全公報取得とは区別。微分を使っただけの新規性を主張しない。

2026-10-21追補：[観測履歴と状態実現の先行資料](rotation-history/prior-art.md)。Anantharaman–Sule, Observability of Nonlinear Dynamical Systems over Finite Fields（arXiv2404.02336v1）の要旨・導入・系の定義を確認。有限体上の出力実現も既存の研究対象であり、wordの回転に適用したことだけを新規性にしない。自律系の定理を今回の入力依存回転へ直接移さず、今回の履歴制限は別の構成で論証した。

2026-10-21追補：[丸め格子の近接先行技術](shifted-rounding/prior-art.md)。CPFloatの著者公開版の丸め処理と現行format定義、US6668325B1明細書§7.1.1の倍率符号化・型拡張、無害な二重丸めの資料、FLOB v3を照合した。CPFloat出版版と公開原稿、Roux論文の要旨確認と未取得の本文、特許明細書の局所確認と全請求項調査を区別する。既知の部品をWasmへ移したことだけを新規性にしない。

2026-10-21追補：[型回復の一次実装と既知loop peeling](type-language-gate/README.md)。NotDecのConstraintGenerator/NFAMinimize、GrammaTech Retypd commit 8f7f72be9a567731bb82636cc91d70a3551050bfの形状統合・経路列挙、LLVM公式LoopPeel.hの末尾反復展開APIを読んだ。Noonan–Loginov–Cok、Polymorphic Type Inference for Machine Code（PLDI2016）は今回は要旨・書誌のみ。Retypdの公開実装を実行した結果とNotDec本体の未実行を分ける。原本・GPLv3・固定commitを保持。

2026-10-21追補：[多項式lookupの先行資料](polynomial-lookup/plan.md)。Freedman–Nissim–Pinkas, Efficient Private Matching and Set Intersection, EUROCRYPT2004 §4.1の著者PDF、NTL公式ZZ_pXFactoringのFindRoots/RootEDF/CanZass、Wasm数値仕様のunsigned remainderを確認。集合の根による表現は既存。Galbraith–Li ePrint2022/1516は要旨・書誌のみ、EP1675031A1は一次検索抜粋のみで、本文・請求項を読了したとしない。暗号学的な保証を公開係数の本実装へ転用しない。

2026-10-21追補：[アトミック表現の一次資料](atomic-codec/prior-art.md)。Drape博士論文§3.2–3.2.1、Tigress Encode Dataのautomatic/poly1、LLVM AtomicExpandPassのCAS展開、Wasm ThreadsのRMW・整列・初期化条件を確認。演算に適合するcodec選択も既存と分かり、今回のWasm実装を独立した新原理とはしない。取得失敗したRust資料は根拠から除外した。

2026-10-21追補：[部分範囲外storeとBMOの先行資料](page-block-codec/prior-art.md)。2017年のspec issue438、Mozillaの高アドレス優先storeのdescription/review、WASMixer Algorithm1を実読。KSC2023のBMO簡約は著者研究室の発表記録まで、WeBMOは公式programまでで本文未読。関連公報KR103005503B1は検索抽出された請求項1–9を読み、取得経路・未読範囲を明示した。

2026-10-21追補：[trace/ABPの先行性ゲート](../experiments/odd-trace-gate/prior-art.md)。Ikenmeyer–Landsberg（JPAA2017）の定義2.1–2.2・Remark4.5をarXiv本文で確認し、計算全体の閉路・行列べき乗への変換を新しい原理とはしない。ECCC2018のmatrix-product難読化、2026年のexact neural arithmetic、WeBMOの読めた範囲と未読範囲も分けて記録した。

2026-10-21追補：[コピー残差表現の先行性](copy-fiber/prior-art.md)。冪等変換の中心化に関する2011年論文の書誌・要旨・§2冒頭抜粋と、EOC（2022プレプリント）の共役構成・非線形BDD構成を確認。前者の本文取得失敗と未読範囲を明記した。非線形化や共役融合の一般着想を今回の独立した新発明とはしない。

2026-10-21追補：[copy互換codecの先行技術](copy-centralizer/prior-art.md)。Data Randomizationの等価クラス・union-find、Data Space Randomizationのmaskとbulk関数の取扱い、Magmaの中心化代数APIを確認した。技術報告・査読会議・仕様資料を区別し、線形代数自体を発明としない。

2026-10-21追補：[制約伝播・変数消去の先行資料](propagation-projection/prior-art.md)。BABEL、Inprocessing Rules、Clause Elimination Procedures for CNF Formulasの指定箇所を確認し、計算モデル変更と伝播保存の先行性を記録した。CENSORは書誌・要旨のみ、本文は403で未取得。ROBDDとWasm bitwise仕様も既知部分として区別する。これらを使った[今回の試作](propagation-projection/README.md)の独立した新規性は未確立。

2026-10-21追補：[rANSと演算統合に関する確認範囲](selector-quotient/prior-art.md)。DudaのarXivプレプリントは書誌・要旨のみ、Giesenの作者解説は復号式等、公開実装はDecGet/DecAdvance等を確認した。LOKIの演算統合は過去の読解記録を参照する。未読の全文や検索結果だけから新規性を判断しない。本候補の最終判断は[成立性検査による棄却](selector-quotient/analysis.md)。

2026-10-21追補：[浮動小数点候補の先行技術照合](zero-sign-transport/prior-art.md)。FLOBのv1/v3の記述差、Obfuscator-LLVMの符号式置換、GCCの零符号最適化、作者によるFP例外VMの解説を区別して記録。codesomeのREADMEは確認したがソース取得は未完了。同一の零符号遅延修復手順の先行性は未確定。

2026-10-21追補：[位置依存表現のコピー後補正の先行技術](bulk-rebase/prior-art.md)。Data RandomizationのPDF表題・§4.3/5/6.1の一部、US8667301B2の書誌・位置maskの説明・請求項1–18、US11354420B2の指定説明と請求項1–20を照合。US20140189366A1は検索抽出と直接取得失敗を区別した。既知の位置mask・再符号化に対する本案の具体差と、著者資料の脅威モデル・実測との相違を記録した。

2026-10-21追補：[Hamburg, Accelerating AES with Vector Permute Instructions (CHES2009)](saturation-anchor/prior-art.md)の書誌と著者PDFの指定節を確認。特殊値表現・permute零出力・飽和加算と表の共同設計が、零割当案に近い。Ristrettoのpacked counter実装も一次コードで確認し、[飽和カウンタ試作](saturation-anchor/README.md)の動機と比較範囲を記録した。両資料の著者実装の性能再現はしていない。

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


書込み失敗境界の被覆候補（2026-10-18）：[書込み被覆の先行技術照合](write-frontier/prior-art.md)を追加。GCCの2016年store mergingパッチ本文、Su/Lipasti VEE2007の該当節、US20190163475A1の本文と請求項1–20、Wasm store規則を確認。byte像の合成、正確な例外を守る融合・再実行を既知要素として認める。各資料の精読範囲・未確認範囲を区別した。

共同多項式更新候補（2026-10-18）：[多項式構成と公報の照合](polynomial-carrier/prior-art.md)を追加。ASPIRE D2.01（2014公開技術報告）の§11.1.2–11.1.4とUS7966499B2の本文・請求項1–22を確認した。可逆変換の前後合成、多項式展開、単項式共有、有限環上の同値式置換を既知要素として認める。全公報調査・審査経過の確認とは区別する。

状態重なりNFA候補（2026-10-18）：[追加の文献・公報照合](overlap-automata/prior-art.md)を保存した。Brzozowski/Tammの2013年プレプリント§4–5、Clemente/MayrのLMCS2019誌面§7.2等、US11657127B2の請求項1–17とFSM重畳の記載を確認。Kameda–Weiner原論文の直接精読、上記公報の請求項18末尾・全図面の精読は未完了として区別する。状態共有・合法な商の構成だけを新規性としない。

2026-10-18追補：[CPSと型付き共有relayの照合](typed-relay/prior-art.md)。LuのFJ拡張版§2/§5–7、Palsberg/Wandの著者版導入・§2、Damian/Danvyのlinear beta reduction・Theorem4.4/Corollary4.5、call routing論文の書誌・§4.4を確認した。CPS変換でflow情報が保存される条件と、共有combinatorで集合が合流する条件を混同しない。出版前版・査読発表・標準提案を区別し、読めていない実験値は埋めない。

2026-10-18追補：[区間上書き候補の先行技術](interval-write/prior-art.md)。DomasのREcon2015一次スライドのscratch比較部分と実装README、Kirsch/JonischkeitのDemovfuscator README、Wasm bulk/multi-memoryの公式提案文書を確認。査読論文・著者実装の独立再現とは区別する。US20070234070A1等の公報は検索抽出のみで請求項照合済みとはしない。

2026-10-18追補：[suffix輸送と重み付きオートマトンの比較](suffix-transport/prior-art.md)を追加した。Kiefer（2020、arXiv:2009.01217v1、既知結果を整理するノート）の§1〜§3の指定範囲を確認。Anderson（2008、ePrint 2008/184）は抄録等の部分確認で秘密oracleモデルを区別し、査読発表先は未確認。Emscriptenのswizzle対応表も確認した。実装と双対回復は[別記録](suffix-transport/README.md)であり、文献のアルゴリズムを新規と称さない。

2026-10-18追補：[複数変数・関係式の一次資料の確認範囲](patent/joint-relations.md)を追加した。Fukushimaほか2006（IPSJ Digital Courier、DOI 10.2197/ipsjdc.2.498）は部分確認で、評価表未読。JP2008090668AとUS20210319125A1は明細書の指定部分・請求項を確認。取得失敗、family未読、実験未再現を区別した。

2026-10-18追補：[SIMD非正規maskの先行技術](simd-quotient/README.md)を追加。RamanほかHSCC2015（査読会議、DOI 10.1145/2728606.2728628）の要旨・§2.2のmin/maxによるrobust semanticsを確認し、Boolean値を数値域へ移す既知の構成と比較した。[US8645930B2の請求項1–17](patent/signature-and-simd.md)は共通prototype・関数統合方向の先行記載。WASMixer §4.2.2も再確認。いずれも著者実装の新しい実行ではない。

2026-10-18追補：[公開特許5件の読了範囲・構成対応](patent/README.md)と[循環回路・固定点実行との比較](bit-feedback/README.md)を追加。ShamsiほかGLSVLSI2017の本文・Algorithm 1・評価を確認した。Riedel/Bruck DAC2003の論文本文は今回未取得で、関連US7249341B2の一次検索抽出との比較に限定する。未読を照合済み扱いにせず、特許性やFTOの結論も出さない。

継続調査（2026-10-18）：[stack-cycleの比較記録](stack-cycle/paper-note.md#related-work)。WASMixer（Shangtong Cao, Ningyu He, Yao Guo, Haoyu Wang, 2023, arXiv:2308.03123v1）の§4.2.1 Algorithm 2/3を確認し、stackのlocal保存・復元と比較した。WebAssembly Design RationaleのControl Flow Instructions with Valuesとmulti-value提案のOverviewも確認。値付き分岐によるlocal削減、loop引数とSSA phiの関係は既知であり、これらの使用を新規性に数えない。今回は著者WASMixerの再実行ではなく、自作の退避dispatcherとの同条件比較である。

数値技法の追加照合：Victor Shoup, *Arithmetic Software Libraries*, January 2020 author chapter draft（Computational Cryptographyへの収録予定と記載、正式版・査読状況は今回未確認）、[著者PDF](https://www.shoup.net/papers/akl-chapter.pdf)。p.1書誌、§2/Fig.1のaddmulpを確認した。整数の下位剰余とfloat積を併用する既知技法を説明する。著者実装の再現・性能数値の追試は行っていない。[今回の領域変換との関係](rounding-region/plan.md)。FLOBの逆方向に見えることだけを新規性の根拠にしない。追加検索は `floating point rounding error residue exact dot product`、`floating-point modular correction integer multiplication`、`obfuscation residue floating`。Debian掲載Mlucasコードは検索断片のみで、本文取得が失敗したため算法の根拠として使わなかった。

接続表現の追加比較：Mokhov（2015、IET Computers & Digital Techniques、査読誌）の一次本文を確認した。[書誌・読んだ範囲](connectivity-elimination/plan.md)、[実Wasm試作と反証](connectivity-elimination/README.md)。既知の接続代数と、今回の保護用途の仮説を区別する。

状態遷移方向の追加照合：Li/OrailogluのWBLO（ASP-DAC 2025招待論文）について、公式プログラムと著者発表スライドの鍵更新・合流修復・評価説明を確認した。[書誌、確認範囲、限定した次候補の成立条件](structured-key-consistency/README.md)。本文・著者実装は未取得で、今回のグラフ検査を著者方式への攻撃と混同しない。

2026年の追加照合：Wei/Liu/Wang/HuのA²-MBA（Computers & Security 167, 104866）について、出版社の要旨・導入を確認した。[書誌・確認範囲・未確認事項](stateful-hardening-review.md)。全文・実装は未取得で、数値を本研究との優劣に転用しない。状態を省略する解析の誤答と、正しい意味の解析に対する復元費用を区別する。

型付き制御変換の追加照合：Foket/De Bosschere/De Sutterの *Effective and efficient Java-type obfuscation*（SPE 2020、査読誌）について、著者公開本文の変換・評価説明を確認した。[書誌、読んだ範囲、評価の限界とFへの含意](typed-transport-review.md)。型を曖昧にする一般発想と、具体的なWasm変換算法の新規性を区別する。今回の追加実装・実験はない。

GC方向の追加調査：Collberg/Thomborson/LowのPOPL 1998とWang/Hill/Knight/DavidsonのCS-2000-12について、一次資料の書誌・要旨と取得限界を確認した。[出典・確認範囲・GC試作との差](alias-circuit/README.md)。参照共有による難化は先行しており、GCへの移植を新原理とは数えない。本文未取得の評価値は補完していない。

追加調査（メモリ方向）：Drape博士論文（2004）の§7.2、Rupprecht博士論文（2020）の§15.1.2・17.2.6、Practical Data Location Obfuscation（MSR-TR-2009-3）の要旨を確認した。[書誌・確認範囲と対照実験](memory-trace-audit/README.md)。値依存配置やpointer scramblingだけを新原理とせず、動的な接続回復も評価対象に加える。NotDec本体は未実行であり、自作のtrace規則と区別する。

追加調査：飽和min-plus候補では、Kim/Roush（2005）とLin/Tran（2017、改訂2019）の熱帯多項式因数分解を確認した。[書誌、確認範囲、適用限界](saturating-frontier/design.md)。一般の困難性を保護根拠に使わず、実際の生成集合へ再分解攻撃を実装したところ4例すべて元と同じ演算数へ戻せた。[実験](saturating-frontier/README.md)。

継続研究の追加文献：対称状態縮約に近接するPEPM 2012（Giacobazzi/Jones/Mastroeni）とSAS 2004（Rodríguez-Carbonell/Kapur）、確認済み箇所・PDF取得の限界・DOIは [追加設計の文献欄](symmetric-state/design.md) に記録した。対称式の算法自体を新規性とはしない。

調査日：2026-10-18（日本時間）。指定6文献と、設計の新規性を反証し得る文献を一次資料で確認した。全論文の精読・著者実装の再現・関連研究の網羅は未完了。検索ヒットの不在を新規性の証拠にはしない。CSEC原稿とは別研究である。下表は初回確認の範囲、後半は追加で確認した本文と、最終的な最近接研究を記録する。

|文献・著者|年・発表区分・一次資料|確認した内容と範囲|結果・限界と本研究への含意|
|---|---|---|---|
|WASMixer: Binary Obfuscation for WebAssembly; Shangtong Cao, Ningyu He, Yao Guo, Haoyu Wang|2023、今回確認した版は[arXiv v1](https://arxiv.org/html/2308.03123v1)。査読会議版の書誌確認は未完了|要旨、§4.1、§4.2冒頭。load/storeのXOR符号化、識別名変更、スタックを考慮した分割・再構成|著者は正当性・効果・効率を報告。数値表の再点検と再現は未実施。単にブロック分割や暗号化をWasmで実装しても差分にならない|
|Wobfuscator: Obfuscating JavaScript Malware via Opportunistic Translation to WebAssembly; Alan Romano, Daniel Lehmann, Michael Pradel, Weihang Wang|2022、IEEE S&P査読会議。[著者PDF](https://weihang-wang.github.io/papers/Wobfuscator-sp22.pdf)、[DOI](https://doi.org/10.1109/SP46214.2022.00064)|著者PDFを取得・閲覧、今回の要約根拠は要旨。JSの一部をWasmへ移す方式|論文の検出回避評価を本研究の目標にはしない。Wasm内部の復元タスクとは異なる。意味保存と低負荷は著者の報告であり今回の再現結果ではない|
|NotDec: WebAssembly Decompilation With Inter-Procedural Type Recovery; Jikai Wang, Ningyu He, Tianming Liu, Junhai Wang, Haoyu Wang|2026、ICSE ’26査読会議。[著者公開本文](https://arxiv.org/html/2608.03286v1)、DOI 10.1145/3744916.3787762|書誌、要旨、§3の構成・前処理の一部。スタックをSSAに移しRetypd、pointer/numeric区別、Memory SSAを利用|著者報告：Juliet 5,241例とHoward全例で再コンパイル成功、構造体アクセス回復85.33%。再コンパイル成功と意味保存は同義ではない。大規模な関数間解析のスケーラビリティに制約。今回未実行|
|StackSight: Unveiling WebAssembly through Large Language Models and Neurosymbolic Chain-of-Thought Decompilation; Weike Fang, Zhejian Zhou, Junzhou He, Weihang Wang|2024、ICML査読会議、PMLR235:13010–13028。[会議公式ページ](https://proceedings.mlr.press/v235/fang24e.html)|公式要旨・書誌のみ。スタック追跡とLLMを組み合わせC++を生成|改善とユーザー評価を著者が報告。本文のデータ分割、モデル、評価値は未読のため転記しない。スタック操作増加だけで耐性を主張できない|
|Evaluation Methodologies in Software Protection Research; Bjorn De Sutter, Sebastian Schrittwieser, Bart Coppens, Patrick Kochberger|正式版の表紙は2024年12月、ACM Computing Surveys57(4),86、査読誌。[著者機関版](https://eprints.cs.univie.ac.at/8227/1/3702314_Sebastian%20Schrittwievaluation_methologies.pdf)、DOI10.1145/3702314|正式版表紙・要旨・導入、プレプリント検索で評価上の課題を確認|571論文の113側面を調査。今回全項目は再集計していない。単一ツールやコストだけを強度評価に使わない|
|A New Framework of Software Obfuscation Evaluation Criteria; Bjorn De Sutter|2025、今回確認したのは[arXiv v1](https://arxiv.org/abs/2502.14093)。査読版未確認|要旨・書誌。relevance、effectiveness、robustness、concealment、stubbornness、sensitivity、predictability、costを提案|本実験に数値的効果を与える論文ではなく評価枠組み。通常の最適化と方式依存の解除を分ける動機となる。全文精読は未完了|

## 反証検索

2026-10-18に英語で上記完全タイトル、`WebAssembly obfuscation multi value block branch stack obfuscation`、`software obfuscation implicit flow exception bounds check opaque predicate` 等を検索した。

追加の近接研究として **Using Exception Handling to Build Opaque Predicates in Intermediate Code Obfuscation Techniques**（JCS&T 8(02), 2008）が[出版社検索結果](https://journal.info.unlp.edu.ar/JCST/article/view/744)で見つかった。ページ・PDFの直接取得はエラー。著者全員・本文アルゴリズム・評価値は未確認で、推測しない。例外をopaque predicateへ利用する一般発想の先行例が存在するため、今回のtrap carrierを新規原理とは主張しない。次回は取得可能な著者版を探す。

さらに[Control-Flow Deobfuscation using Trace-Informed Compositional Program Synthesis](https://doi.org/10.1145/3689789)を発見した。現時点は検索抜粋のみで、本文の比較と実行は未完了。

## 過去の資産の扱い

### 2026-10-18の本文追跡

NotDec §3.1–3.3、§4の実験設定を追加確認。型付きスタックからSSAへ移し、load/storeのアドレスをPtr、乗除算等の値をNumとしてPNDiffを初期化し、加減算の制約を伝播する。固定offsetはフィールド推定に使われる。通常のmemcpy/memset検出は最適化後に行う。Howard向けの一部ビルドは依存関係の代用により実行できないと記載されており、同論文の再コンパイル率を実行同値性の証拠としない。[本文](https://arxiv.org/html/2608.03286v1)

StackSight §4.3.2、§5.1、Table2を追加確認。使用モデルはGPT-3.5、GPT-4、Code Llamaの版を指定。評価は再コンパイルに加えテスト通過を使う。GPT-4条件でHumanEval-Xのcorrectは36.5%、MBXPは59.6%と報告される。引数の参照渡し調整に手作業を含むため、全自動の一般同値性証明と解釈しない。今回のローカル再現は未実施。[本文](https://arxiv.org/html/2406.04568v1)

LLVM公式の[SLPベクトル化](https://llvm.org/docs/Vectorizers.html#the-slp-vectorizer)も確認。複数scalar演算をまとめる既存の仕組みであり、memoryアクセスやPHIも対象と説明される。新しいaccess-fusionの2word規則は、この一般原理から独立した発明とは判断しない。

**Implicit White-Box Implementations: White-Boxing ARX Ciphers**, Adrián Ranea, Joachim Vandersmissen, Bart Preneel、CRYPTO2022、査読会議、DOI10.1007/978-3-031-15802-5_2。[会議PDF](https://crypto.iacr.org/2022/papers/530630_1_En_2_Chapter_OnlinePDF.pdf)の書誌・要旨・導入を今回確認。暗黙関係・self-equivalence・大きい符号化を組み合わせる。鍵抽出に関する著者の主張を一般プログラムの式復元耐性へ転用しない。過去の非単射残差案については、保存済みのより詳細な節別照合を参照し、今回全証明を再検証したとはしない。

`experiments/research-evidence-audit/README.md`、`tmp/typed-dispatch-controls/README.md`、`tmp/simd-layout-design/README.md`、`tmp/trap-prefix-recovery/README.md`、`tmp/memory-representation-audit/README.md` を読んだ。既知の値受け渡し、線形符号化、遅延store、単純なSIMD置換を新発明として再利用しない。過去の件数を今回の実行件数へ加算しない。

## 最終実験に向けた追加調査

WASMixer §5.2–5.5を追加確認。正当性試験は20プログラムに14変種ずつを加えた計300条件。validatorと同一入力の出力一致を著者が報告する。300すべてが変換後の独立プログラムではなく、有限テストも全入力の証明ではない。本文の構文複雑度・検出率を、内部計算の復元費用と同一視しない。[本文](https://arxiv.org/html/2308.03123v1)

Evaluation Methodologiesの書誌には、オンライン公開2024-12と、巻号57(4)の2025という年の違いがある。前者は[著者機関の書誌](https://informatik.univie.ac.at/en/research/publications?cHash=810ac282e1f9fce08d9b1de62764b1b0&tx_univiepure_pi1%5Bcobjuid%5D=3691&tx_univiepure_pi1%5Bcontroller%5D=Pure&tx_univiepure_pi1%5Bcurrentpage%5D=36)でも確認。別論文として二重計上しない。

|タイトル・著者|年・発表先・一次資料|提案・確認範囲・著者の結果|本案との差と限界|
|---|---|---|---|
|SaMBA: Increasing Mixed Boolean-Arithmetic Complexity Through Equality Saturation — Caroline König, David Schmidt, Philip König, Patrick Felbauer, Sebastian Schrittwieser|2026、ASIA CCS、査読会議。[著者機関PDF](https://eprints.cs.univie.ac.at/8730/1/2026_samba.pdf)、[DOI10.1145/3779208.3785382](https://doi.org/10.1145/3779208.3785382)|要旨、§2–3、§4.2–5を確認。e-graphとnegative-size費用で同値式を選ぶ。1,000例のbatch評価ではGAMBA/ProMBAが式を縮めても元のDAGサイズまで戻らない。sha512sumで約66%実行時間増を報告|Cに最も近い探索・抽出方式。中間関数の集合包含と固定対象の復元採点が差分の候補。式を大きくする一般論は先行済み。本文のDAGサイズを全同値表現での最小計算量と解釈しない。今回SaMBA未実行で勝敗不明|
|Loki: Hardening Code Obfuscation Against Automated Attacks — Moritz Schloegel, Tim Blazytko, Moritz Contag, Cornelius Aschermann, Julius Basler, Thorsten Holz, Ali Abbasi|2022、USENIX Security31:3055–3073、査読会議。[公式書誌](https://www.usenix.org/conference/usenixsecurity22/presentation/schloegel)、[本文](https://synthesis.to/papers/usenix22-loki.pdf)|§4.4–4.5、§5、Experiment11–13を追跡。検証付きMBA合成、依存するsuperoperator。Syntiaが10,000件中1,888件のLOKI式を合成したと報告|中間計算を独立した簡単な課題へ分割させない問題意識は先行済み。本案は観測集合による選択に限定。鍵選択・VMは再実装していない。著者の19%と本実験の100%は課題・予算・データが違い直接比較不可|
|Program Synthesis with Equivalence Reduction — Calvin Smith, Aws Albarghouthi|2019、VMCAI、査読会議。[著者PDF](https://pages.cs.wisc.edu/~aws/papers/vmcai19.pdf)|§1–2、§4、§5.2、§6を確認。等式とterm rewritingで正規代表だけを探索し、合成時間削減を評価。今回Table2の数値再現なし|出力同値類の重複削減は既知。本案は中間関数も区別する。本文は非効率な正規形が選ばれる可能性にも言及する。具体的な観測集合の規則が他文献にないとの網羅的確認はできていない|
|Synthesis of Masking Countermeasures against Side Channel Attacks — Hassan Eldib, Chao Wang|2014、CAV、査読会議。[著者PDF](https://chaowang-vt.github.io/pubDOC/EldibW14CAV.pdf)|§1–4を確認。入出力等価性と中間値の統計的独立性を検証する反例誘導合成。LLVM/Yices、AES/MAC-Keccak等への適用を著者報告。今回評価表の再現なし|「途中の情報も評価する合成」全体は新規ではない。隠された乱数・鍵と部分的な物理観測を仮定するマスキングを、全内部値が見える白箱保護へ転用しない|

追加の反証先として **Control-Flow Deobfuscation Using Trace-Informed Compositional Program Synthesis**、Benjamin Mariano, Ziteng Wang, Shankara Pailoor, Christian Collberg, Işıl Dillig、2024、PACMPL 8 (OOPSLA2)、Article 349、査読論文、[DOI10.1145/3689789](https://doi.org/10.1145/3689789)を確認した。初回の著者欄で欠落していたBenjamin Marianoを表紙に基づき訂正した。初回は要旨と§4.4取得部分に限ったが、後続で§3.2・§4・§6・§7を追加確認した。確認範囲と著者報告は[追加照合](nonlocal-literature-audit.md)を参照。本体は未実行。

**Generating Adversarial Computer Programs using Optimized Obfuscations**、2021、[arXiv2103.11882](https://arxiv.org/abs/2103.11882)は要旨のみ。著者・査読先の精査未完了の探索候補として残し、確定書誌には数えない。FLOB、QSynth、Drape博士論文の過去の節別調査は`tmp/semantic-fusion-audit/README.md`と`experiments/tensor-quotient-gate/README.md`を参照。今回独立に全てを再読したとはしない。

意味保存については[Wasm仕様・実行規則](https://webassembly.github.io/spec/core/exec/instructions.html)のi32剰余演算とmemory trapを前提にする。validatorは型・構造を検査するもので、意味同値性を証明しない。今回はその上に局所式の係数一致、独立実装の式照合、実行差分試験を重ねた。

## 最近接研究と調査の限界

追加検索語は `program synthesis obfuscation Pareto`、`obfuscation observations equivalence synthesis`、`LOKI synthesis dependent obfuscation`。この反証検索からSaMBAを追加した。第三者要約や未検証GitHubの強度主張を根拠にはしない。

Cの探索・抽出に対して最も近いのはSaMBA、依存した意味の統合にはLOKI、AにはImplicit White-Boxである。Bは可逆基底変更・白箱表現の一般原理に属するが、tensor構成そのものと一致する先行論文までは同定できなかった。それは新規性の証明ではない。A/B/Cのどれにも、独立した学術的新規性と有効性を同時に確認できていない。

継続する合成・中間状態消去の探索では、[Chisel、ASPIRE D2.01、XSmirの追加照合](nonlocal-literature-audit.md)を行った。ASPIREは技術報告であり、査読論文と区別する。XSmirの著者公開artifact案内は確認したが取得・実行はしていない。WAMOは本文未取得の反証候補として残る。今回の2回合成が新原理であるとの主張は支持されない。

メモリ射影の探索では、Hawkins/Aiken/Fisher/Rinard/Sagivの *Data Representation Synthesis*（PLDI2011、査読論文、DOI10.1145/1993498.1993504）の著者PDF表紙・要旨・導入を確認した。[書誌と照合範囲](memory-quotient/design.md)。関係・関数従属性と具象表現の合成が先行する。今回の限定Wasm射影と同一算法とは確認していないが、表現を消す・合成する一般発想を新規性としない。著者の性能結果は独立再現せず、今回のWasmへの優劣へ転用しない。

固定文字列の探索では、Lynn/Prabhakaran/SahaiのEUROCRYPT2004、Galbraith/ZobernigのSAC2020改訂会議録、Bishopら6名のePrint2019/463、およびPohlig/HellmanのIEEE TIT1978を追加照合した。[各書誌・URL・確認した節・本案との違い](rolling-point/design.md)。査読会議・雑誌とePrint解説を区別する。群上の点関数、秘密substring、smooth-orderの対数回復が先行しており、この組合せを新発明とは認定しない。今回の実測は独自の限定実装の値であり、これら著者実装の再現や性能比較ではない。

## 2026-10-23：座標変換・有限回収束・観測の持上げ

[読了範囲と書誌一覧](hidden-filtration/prior-art.md)を追加。近接公報はHriljacのWO2012040383A1。有限回収束はRichard（Discrete Applied Mathematics,2019）、観測の持上げはMauroy/Goncalves（CDC2016, DOI10.1109/CDC.2016.7799269）を照合。公報の説明読了と論文の要旨のみの確認を区別し、既存評価を再現したとはしない。

## 2026-10-23追補：Boolean dynamicsと切替系

[書誌、読了範囲、評価未確認の区別](boolean-feedback/prior-art.md)を追加。Gadouleau/Richard（TCS2016）、Anashin/Khrennikov/Yurova（DCC2014、preprint2011/2012）、Li/Pang（Automatica、DOI2023）、F. F. Li（Neurocomputing2014）を照合した。sandpile/abelian networkは既知計算原理との近さを早期確認し、追加実装済み発明とは扱わない。

## 2026-10-23追補：状態付き切替グラフの全体合成

[追加照合](rotor-synthesis/prior-art.md)：Propp2010の著者版導入・§2.1、GärtnerほかICALP2018の書誌/要旨/定義、HaslebacherICALP2025の導入・定義、HolroydほかCPC2019の著者版pp1–5、GulwaniほかPLDI2011とJhaほかICSE2010の要旨・導入抜粋を確認。全論文を通読・再現したとは表現しない。

## 更新状態の商と公開更新による回復（2026-10-23）

[更新状態の先行性](mutation-quotient/prior-art.md)を追加。HawkinsほかPLDI2011の著者PDFの導入・§4.1–4.2、Wahl/DonaldsonのSymmetry2010の著者PDFの導入・§5.4冒頭、Wasm公式relaxed laneselect仕様を確認した。商・代表状態・表現合成という一般原理の先行性と、今回の限定した合同条件を区別する。特許の請求項全文との対応は未精査。

## 部分文字列をまたぐ文法変換と三次係数からの解除（2026-10-23）

[substring-shearの文献照合](substring-shear/prior-art.md)を追加。CohenらACL2012のテンソル内側計算、RabusseauらAISTATS2016のWTA、BonsangueらCMCS2012のproper algebraic system、HriljacのWO2012040383A1と照合した。読了範囲と未読の評価を分け、検索に現れなかったことを新規性の証拠にしない。

## コピーの観測引戻しの初期ゲート（2026-10-23）

[range-pullbackの照合](range-pullback/prior-art.md)を追加。Kamath/PeterのISCA2024 (MC)²はlazy memory copyとsourceへのread転送を扱う直接近い先行機構。公式Wasm仕様の零長・範囲検査順を確認した。BAR2026のLLM/CTF分析論文も要旨と設計冒頭まで確認したが、未読結果を実測扱いにしない。

## 可変二表の接続更新と履歴なし回復（2026-10-23）

[mutable-factorの照合](mutable-factor/prior-art.md)を追加。US9117094B2 Data location obfuscationの書誌・説明概要・請求項1–19を読み、実行中の配置交換とpointer scramblingの先行性を確認した。DrapeのGeneralising the Array Split Obfuscationは査読誌書誌・出版社要旨まで。本文未読と実験結果を区別し、動的indirectionだけを新発明としない。

## 剰余表現とWasm整数wrapの成立性ゲート（2026-10-23）

[RNCと有限語長意味論の追補](residue-wrap/prior-art.md)。Demissie/Ceccato/TiellaのSPRO2015著者論文、PhatakのRNS公開特許、Spielmann/Kuncakのtransducer構成について読んだ範囲を明記。RNC原理とdecode/operate/encodeは既知であり、今回の反例を先行著者実装へ帰属しない。

## 現memoryを使う共有退避の生成（2026-10-23）

[coded side-informationの追補](side-save/prior-art.md)。Lee/Dimakis/Heathの2014 preprintの問題定義とTheorem 1、Byrne/Calderiniの2017誌面Abstractを確認。共有送信と各受信者の線形副情報という既知条件が今回の共有退避へ対応する。nestedなWasm copy列への具体化との境界を記録した。


## Disrobe v0.10.6 baseline (2026-10-23)

[実測と再現方法](../results/invention-20261023/disrobe-report-v1/report.md)。Disrobe v0.10.6を公式checksum確認後に27入力へ適用した。新発明の件数には加えない。


- 未変換リスト9本：C/JSON/WAT生成は正常終了。生成WATはvalidationを通るが初期dataが欠落し、5,148呼出し中504が不一致。正解dataを戻す診断は全件一致。
- 整数式18本：生成WATの75,906呼出しで不一致0。別deob処理の18出力は入力とbyte一致し、既存の適応射影による回復を否定しない。
- Cは固定offsetのi32 loadと局所変数へ戻るが、リストのnext pointer型・record strideの回復は確認できない。Cの再コンパイルは未実施。

この測定により『出力ファイルがある』『Wasm validationに通る』『正しく実行する』『構造を回復する』を別の項目として管理する。NotDecの代替実測とは扱わない。


## 遷移二乗による双模倣評価（2026-10-23）

[遷移二乗と双模倣評価](transition-square/README.md)を実Wasmへ実装した。主54条件106,488呼出し、境界48条件24,960呼出しは一致したが、公開行列の平方根とBoolean抽出で主24条件・境界12条件をすべて回復。同じgraph評価器に対して約26–37%高速化した一方、元の式比約811–8,643倍の実行費用。回路還元・行列関数の先行性と公開逆算から主特許候補には不採用。[実測](../results/invention-20261023/transition-square-report-v1/report.md)。

最も近い核はChen / van Breugel / Worrell, FoSSaCS 2012, DOI10.1007/978-3-642-28729-9_29の確率的双模倣への回路還元。著者版§2と書誌を閲覧した。主平方根・三角漸化式にはHighamの一次解説を確認し、[閲覧範囲と特許検索](transition-square/prior-art.md)に記録した。


## 有限精度の観測閉包と選択入力回復（2026-10-23）

[有限精度の観測閉包](observer-closure/README.md)を自動生成し、実Wasmへ実装した。主30正条件780,090 API呼出しは一致したが、全12変換を10step観測で小さな更新へ回復。reset/peekを削った追試でも全12変換を22stepで回復し、491,520stepは一致した。実行費用は元の約5.18–10.05倍で、既知の観測実現・多項式持上げを超える新規性と保護優位は未確立。主特許候補には不採用。[実測と再現](../results/invention-20261023/observer-closure-report-v1/report.md)。

Sontagの2026年プレプリント（1976年博士論文の更新）、Iacob/Schoukens/TóthのIFAC2023有限Koopman構成、BruntonほかPLoS ONE2016、WO2013142979A1の関連箇所を実際に閲覧。[書誌・既読範囲・技術差](observer-closure/prior-art.md)。


## 非線形共有退避の生成と限界（2026-10-23）

[非線形共有退避](nonlinear-save/README.md)を実Wasmへ実装した。探索600例中1例と独立holdout600例中1例で、最良線形保存2bitに対して1bitを達成。主42条件40,362呼出しと追試14条件12,614呼出しは一致した。ただし公開APIから全24変換条件を同等遷移表へ回復でき、既知のfunctional index coding・cographとの差も弱い。表生成の補助的最適化として保存し、主たる難読化発明には不採用。[実測と再現](../results/invention-20261023/nonlinear-save-report-v1/report.md)。

Gupta/Rajanのfunctional index codingの定義・命題1–2・Algorithm 1を実読し、今回の副情報/要求関数の条件と直接対応することを確認。LDT graphのcograph性も既知。[書誌・既読範囲](nonlinear-save/prior-art.md)。


### Nonlinear-save: supplementary patent comparison (2026-10-23)

[Read claim-level comparison](nonlinear-save/patent-followup.md): US9436447B2 claims 1-8 and US9235433B2 claims 1-6 were inspected, together with the relevant reconstruction descriptions. This documents technical differences, not patentability or clearance. The experiment decision is unchanged.


## 非可逆な解釈状態の同期（2026-10-23）

[重みを伴う解釈状態の同期](synchronizing-decoder/README.md)を実Wasmへ実装し、主54条件62,208呼出しと代表回復12条件13,824呼出しの一致を確認した。非可逆遷移で全入口を同じ計算へ収束できたが、代表状態一つで全12sync条件を全状態解析とbyte一致のコードへ回復。元の約3.71–30.80倍の実行費用に対して追加保護の根拠が弱く、weighted synchronizationにも先行性があるため主案に不採用。[実測と再現](../results/invention-20261023/synchronizing-decoder-report-v1/report.md)。

Iván, Synchronizing weighted automata（AFL 2014）の定義と、Kilger/Auer/Andreas, VMSpec（2026-10-21 preprint）のVM context・handler要約・限界を実読。[書誌と既読範囲](synchronizing-decoder/prior-art.md)。著者の評価と本研究で実行したツールを区別する。
