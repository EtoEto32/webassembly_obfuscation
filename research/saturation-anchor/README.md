# privateな飽和カウンタの符号化費用

2026-10-21。[zero-anchor](../zero-anchor/README.md)の適用範囲を調べる改良試作。**限定したカウンタ処理で時間・サイズの改善を観測したが、独立した発明と特許取得可能性は未確立**。追加の解析耐性は確認できず、方式既知の16問い合わせで全48条件の符号化を回復した。

## 課題と変換

小表による符号化計算では、復号した4bit値x,yを加算し、15で飽和してから出力置換Eを適用する。本試作はE(15)=0に制約する。

```text
通常: E[min(x+y, 15)]
試作: strict_swizzle(E, x+y)
```

0≤x+y≤15では同じ表参照、16≤x+y≤30ではstrict swizzleの零がE(15)に一致する。一般mod16加算と違い、範囲外の全入力が一つの論理結果15へ合流する。この局所恒等式は容易に導け、これだけを新しい数学原理としない。

```text
transform(module, seed):
  validate(module)
  recognize_exact_private_bank_profile(module) or reject
  E = seeded_permutation(0..15), constrained so E[15] = 0
  D = inverse(E)
  replace private packed state with E-coded nibbles
  replace merge with strict_swizzle(E, D(a)+D(b)) per nibble
  replace decay with lookup(code -> E[floor(D(code)/2)])
  update init/reset/get/set/checksum consistently
  establish encoded zero using start; validate(output)
```

relaxed swizzleにそのまま変更してはいけない。16..30で下位添字を参照する許容動作は違う値を返す。実Nodeでその誤変更を試し、各256値対の120対で不一致を確認した。変換器は範囲内の表引きだけrelaxedを使う。

## 対象と意味保存

N=32..65536、32の倍数のカウンタを二列持つ固定profileの実.wasmを入力する。実測Nは256と4096。2counter/byteで全データN bytes、固定64KiB memory。7関数はmerge、decay、reset、init、get、set、checksum。汎用C/C++由来Wasmを変換するpassではなく、入力が対応する関数構造と一致する場合だけ処理する。

private memoryの物理表現は変わる。観測する意味は公開関数の返値、trap、復号した状態。各nibbleの不変条件code=E(value)に基づき、mergeの上記式、decayの合成表、get/setの逆置換、初期化を照合する。setは他方nibbleを保存する。境界外index/bankは書込み前にtrap。zero-initの物理memoryをそのまま使わず、startで論理0をE(0)へ書く。

export/import/shared/growを伴うmemory、外部からのraw byte観測、任意の別関数、他の更新則は非対応。診断ではmemory exportのみ追加したcloneで全byteも検査する。64KiBのうち使用領域の符号化と未使用領域の零を比較し、未変換版と物理byteが同一とは主張しない。意味保存の局所的説明と有限テストであり、変換器・engine全体の形式証明ではない。

## 比較と結果

plain、補数E(x)=15−x、自由置換+min、制約E(15)=0+min、制約+strict零出力、制約+native飽和加算列、自由置換+16行融合表を比較。補数は著しく構造的で、自由置換と同じ保護とは仮定しない。native列はmin(x+y,15)=sat_add_u(x+240,y)−240。表版は一般的な融合表を自作し、他論文の特定実装の再現とはしない。

2サイズ、2seed（plain/補数はseed0）、raw/O3の主48本すべてWABT validationと実行検査通過。各条件で全256値対、乱数128操作、境界値、start状態、全メモリ副作用を検査した。**60,228,864 Wasm呼出し（診断cloneと想定trapを含む）、6,864状態検査、449,839,104 byte照合、1,152想定trapで不一致・想定外trapは0**。呼出し数は独立入力条件数ではない。seedと小profileの範囲を超える証明ではない。

独立scalar modelでも128置換×256対=32,768組を照合。4本を全strict化した対照で不一致0。4本の意図的な全relaxed化で120/256ずつ不一致。非対応入力3件と誤ったanchor1件を拒否した。

適応解析はknown layoutと任意の計装を認める。public setterで0..15を一度ずつ書き、private memoryを計装観測して置換を学ぶ。生成seed・encoding metadataは与えない。48/48条件で逆表を回復し、merge+decay後の両配列を復号した。未対応、crash、timeoutは0。これは一つの共通nibble符号化の回復課題であり、NotDecや一般データ構造回復の評価ではない。追加の型・接続・アルゴリズム保護は示さない。

性能の主要測定は24 O3 binaries×2 workload×5 fresh process=240 process。warmup20,000回、9batch×50,000回。Wasm内部で全配列mergeまたはmerge+decayを反復し、初期化とchecksumは計時外。固定Bの反復では両workloadとも固定状態に収束する。状態が変わり続ける実アプリの評価ではない。

- 同じ符号化のminあり版比、中央値で約2.0–13.5%の時間減。8比較のうち5比較はprocess中央値の範囲が重ならず、3比較は重なる。信頼区間や一般的な性能保証ではない。
- mergeだけは約6.1–13.5%減、merge+decayは約2.0–7.6%減。変えていないdecayが加わると利益は薄まる。
- native飽和列比約8.0–18.5%減。ただし未符号化の約1.92–2.23倍の実行時間は残る。補数も本方式より速い。
- O3 binaryは873/874→831/832 bytes、42bytes減。linear memoryは全条件64KiB、使用データ256/4096bytes、追加領域なし。
- 変換時間約37.7–43.5ms（構文読取・コンパイル・validation込み、各変換1回、反復統計ではない）。RSSはNode全体で取得し、提案だけのmemory費用とは扱わない。

初回240 processは測定区間が短く、warmup不足を疑う推移を観測した。捨てずに[手順修正](measurement-amendment.md)と元ソース・raw値を保存している。主要測定の全表は[comparison.md](../../results/invention-20261021/saturation-anchor-report-v1/comparison.md)。

## 生成機械語と効果の限界

V8 TurboFanに限定して4096/seed7のmergeの出力コードも採取した。min版のvpminubに対応してzero版にはvpaddusbがあり、strict命令の補正費用は消えていない。定数の構築に使う命令列も違い、診断上の当該関数のinstruction bytesは1676→1612。native版は1408bytesでも遅く、命令数やサイズだけで実行費用を説明できない。

この診断は`--no-liftoff`による別コンパイルで、通常の速度測定processの機械語を捕捉したものではない。全体dumpからindex0の区間を明示抽出した。効果はこのengineの命令選択・定数生成にも依存すると考えられ、全CPUで同じ時間減があるとは主張しない。

## 先行性と判断

[文献と読取範囲](prior-art.md)。Hamburg(CHES2009)には特殊値とpermute零出力・飽和演算・表設計を合わせる先行例がある。零を使う発想や小表符号化は発明の核にできない。今回確認したのは限定された変換規則と、その一環境の費用改善。一般の符号化生成との差、実用範囲、保護費用の妥当性が不足し、特許の主核は保留する。

## 再現

Python3.9.0、Node24.15.0/V8 13.6.233.17-node.48、WABT1.0.42、Binaryen133。Windows10.0.26100、Core i9-11900K、16 logical CPU。`.tools`に配置済みのツールを既存helperから使う。以下はrootから、新しい出力名を指定する。研究用helperはisotope-swizzleとconnectivity-eliminationにも依存する。

```powershell
python research/saturation-anchor/run.py results/saturation-new
python research/saturation-anchor/controls.py results/saturation-new results/saturation-controls-new
python research/saturation-anchor/benchmark.py results/saturation-new results/saturation-runtime-new
python research/saturation-anchor/inspect-code.py results/saturation-new results/saturation-machine-new
python research/saturation-anchor/prototype.py results/saturation-new/n256-source.wasm results/saturation-one.wasm --mode anchor-zero --seed 7
```

`run.py`はsource生成→実.wasm変換→O3→診断clone→scalar照合・適応解析を実行する。48本のbyte再生成照合とソースhash、環境・計測条件はreport-v1に保存。`report.py`はsource/runtime/pilot/controls/outputの5引数で初回と主要測定をまとめる。raw値はsaturation-anchor-v3、controls-v1、runtime-v1/v2、machine-v1に保存。

初回v1はWAT表現の並び・unreachableの正規化不足、v2は式parserのmodule-only制約の扱いで停止した。いずれも実験前の実装不備。v3で修正して正当性検査を完走した。これらを解析失敗・難読化耐性に数えていない。
