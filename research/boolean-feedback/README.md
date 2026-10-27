# 非線形Boolean補正器の全数合成とWasm試作

2026-10-23。可逆な座標変換を使わない候補を実装した。**bitwise版は全12条件、carryを含む整数版も全6条件を回復でき、主特許候補には採用しない。** 普遍補正器の有限分類と整数への持上げは、構成上の知見として残す。新規性・特許性は未確立。

## 構成と区別

第3段階では、[後続状態で補正器を切り替える構成](coupled-results.md)も試した。最大SCCは6/9/10語となったが、公開Hから意味上の小部分を探索するとraw/O3全6切替条件を0.05–0.85秒で回復した。同じ解析器で固定補正より約3倍の解析費用、約3.5–3.7倍の実行費用で、主案には不採用。[先行資料の読了範囲](prior-art.md)を併記する。

Fを3座標の厳密三角Boolean写像、e=s XOR F(s)とし、H(s)=F(s) XOR N(e)を生成する。N(0)=0を満たす全2^21個の写像について、全128個のF・全8初期stateから正しい固定点へ有限回で到達するかを分類した。これは無限のnやword32の全数列挙ではない。

結果は25,968個合格、従来のprefix誤差を後方へ送る十分条件を満たすものは1,024個。最悪収束回数3/4/5/6/7の個数は1,024/5,776/10,776/7,224/1,168。選定N3=[0,2,3,0,0,2,0,0]は4回以内、2座標用N2=[0,0,1,2]は3回以内。パラメータ選択と全数検証は攻撃測定前。

F=0という定数写像の場合、Fの像の大きさは1だが、N3を使うH=N3の像は3。共役変換は像の大きさを保存するため、この構成全体は単なる可逆座標変換では表せない。この数学的な差だけで新規性・難読化効果・特許性を主張しない。

実Wasmを式DAGへ変換し、AND/XOR/ORの連続する最大3節点を群にする。回転は単独節点として群の境界へ置く。群の外部入力が固定された後は各bitが全数検査の対象となるため、全bitが群の上限回数で収束する。群DAGの非循環性から、各群上限の和で全体が収束する。出力では元FとNの分解を消し、展開したHと共通評価器だけを配布する。

## 実測と反証

- catalog-v1：2,097,152補正器、6,245,936組のN/F検査（失敗時打切り）、約20秒。全合格一覧とhashを保存。2bitは64個中10個合格、prefixは4個。
- main-v1：3関数、plain/pipeline/feedback、raw/O3と回復版の42binary、179,466呼出し、不一致0。
- 解析：12/12回復。feedbackのO3で約5.60/4.57/13.56ms、pipelineは約0.10/0.13/0.14ms。公開更新式の依存から強連結成分を求め、各小成分の8状態を列挙して固定点をBoolean条件式へ消去した。解析器は元F・N・seedを読まない。kernel再生成によるbyte照合と、有限回収束の記号検査も行う。
- audit-v1：6byte再現、回復12モデルがSMT UNSAT、scratchを変える3,072呼出し一致。既知N²=0写像を残差へ誤適用すると周期1→6→1になる反例をWABTで確認。唯一固定点だけを持つがround数が不足する改変版も拒否。
- runtime-v1：27process×7batch、warmup16,384、20ms校正。同じANF評価器と同じWasm wrapperを使用。全値・RSS・ばらつきはsummary.json/raw.jsonに保存。

今回の制約はpure i32、最大24節点、flush最大24回、単一run、2入力の評価fixture3個、1seed。trap・元memory・一般CFGを処理しない。WASMixer/NotDec等の独立ツール比較や人間の解析費用は未測定。候補の局所成分をそのまま大きくするだけでは別原理と数えない。

## 再現

整数版は3演算のpure i32関数に限定する。42binary・194,502呼出しで不一致0、独立モデル36,864条件、回復版55,572呼出し、WABT72呼出し、回復6モデルのSMT UNSATを確認した。方式既知の解析は元Fの候補を公開更新式の部分木から探し、Boolean恒等式として厳密に照合する。raw/O3の6条件で26–37ms（読取り・コンパイルを除く単回値）。公開されたHだけを読み、元Fや生成時metadataは使わない。

整数版の実行は元版の約237–266倍、O3サイズは元48–50 bytesに対し143 bytes。linear memoryは全方式0 bytes。36process×7batch、共通Wasm wrapperで測定した。3演算だけの小さい例のため、実用program全体の予測には使わない。内部rotateを含む2bit反例は8回でも安定せず、合同保存という前提が必要である。詳細は[持上げの論証と結果](word-lifting-plan.md)。

```powershell
python research/boolean-feedback/word-run.py results/bf-word-replay
python research/boolean-feedback/word-batch.py results/bf-word-replay results/bf-word-attack-replay
python research/boolean-feedback/word-audit.py results/bf-word-replay results/bf-word-attack-replay results/bf-word-audit-replay
python research/boolean-feedback/word-performance.py results/bf-word-replay results/bf-word-attack-replay results/bf-word-runtime-replay
python research/boolean-feedback/word.py input.wasm transformed.wasm
```

Python3.9標準ライブラリ、Node24.15、WABT1.0.42、Binaryen133。`shared.py`が既存hidden-filtrationのANF・Wasm評価器を使う。SMT監査のみrepo内z3-solver4.13.3.0が必要。存在しない出力先を指定する。

```powershell
python research/boolean-feedback/catalog.py results/bf-replay-catalog
python research/hidden-filtration/smoke.py results/bf-inputs
python research/boolean-feedback/run.py results/bf-inputs results/bf-replay-main
python research/boolean-feedback/audit.py results/bf-replay-main results/bf-replay-audit
python research/boolean-feedback/performance.py results/bf-replay-main results/bf-replay-runtime
python research/boolean-feedback/prototype.py input.wasm transformed.wasm
python research/boolean-feedback/attack.py transformed.wasm recovered.wasm
```

## 先行研究

Maximilien Gadouleau, Adrien Richard, *Simple dynamics on graphs*, Theoretical Computer Science628,62–77,2016, DOI[10.1016/j.tcs.2016.03.013](https://doi.org/10.1016/j.tcs.2016.03.013)。[大学リポジトリ](https://durham-repository.worktribe.com/output/1377346/simple-dynamics-on-graphs)で査読掲載書誌を確認。[著者版2015](https://webusers.i3s.unice.fr/~richard/PUBLICATIONS/JOURNALS/2015_Simple.pdf)の要旨とProposition8(2)の証明を読んだ。nilpotent写像自体は既知。今回の反例はその写像を自作残差式へ組み込む条件不足を示し、既存論文を反証するものではない。

自己安定化による初期化不要化、一般的なBoolean networkの同期/非同期更新も既知。[Dolevほか、JCSS2014](https://doi.org/10.1016/j.jcss.2014.01.001)は要旨と導入の任意初期値の定義を確認しただけで、同じ補正器分類が記載されていると推測しない。有限環残差方式との比較は[word-lifting-plan.md](word-lifting-plan.md)に記録した。正確な分類・合成・持上げに関する先行探索は未完了。
