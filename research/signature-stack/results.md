# Pの実測結果（2026-10-26）

## 正当性の試験

| データ | 対象数 | 判定・制限 |
|---|---:|---|
| correctness-v3 | 362 binary | 標準側119 valid。自作3方式は117 valid / 243 invalid / 2 unsupported。対応360例はwasmparser 0.227.1・0.262.0、Node/V8、WABTと一致。seed固定生成・手書き境界例であり全入力の証明ではない |
| spec-check-v2 | 公式13 WASTから522 binary | 対応481例はすべて期待invalidと一致。41例unsupported、うち正常module15例。**正常系の公式moduleを受理した実績は0**。unsupportedを成功に数えない |
| corpus-v1 | 公開保存データ220 binary | kernelは16 valid / 1 invalid / 188 unsupported / 15 resource_limit。16 validは8〜160 byteの小moduleで、10本は関数本体がない。大規模アプリへの適用実証ではない |

手書き境界にはunreachable直後の型、Bottomのselect、implicit else、loopのparameter label、br_ifの型精密化、異なる型だが同じarityのbr_table、部分Bottom suffix、local/call index異常を含む。

各例で参照validatorとの照合を行ったが、すべての検証器が同じ仕様解釈を共有する可能性は残る。メモリやruntime副作用の同値変換テストではない。今回の処理は入力binaryを変更しない。

## 性能

`performance-v2`は40条件×4方式×3process = **480 process**。幅1/8/64/512、反復64/1024、block/call/if/br_if/異なる型列の交互callの5系列。混合i32/i64/f32/f64。warmup・batch条件はREADME参照。

以下は幅512・反復1024で、3process内の各11sample中央値をさらに中央値にしたend-to-end値（µs）。alternatingは1反復が2callなので、行間を同じ命令数として比較しない。

| 系列 | bytes | wasmparser 0.262 | flat | cached-flat | segment | segment / cached |
|---|---:|---:|---:|---:|---:|---:|
| block | 6,966 | 1,796.95 | 151.43 | 100.25 | 113.88 | 1.136 |
| call | 7,362 | 783.38 | 122.86 | 95.72 | 93.92 | 0.981 |
| if | 10,038 | 2,774.25 | 266.73 | 150.07 | 202.29 | 1.348 |
| br_if | 11,062 | 2,842.33 | 188.62 | 210.11 | 192.58 | 0.917 |
| alternating | 13,653 | 1,563.27 | 198.75 | 177.26 | 155.39 | 0.877 |

最新stockに比べた大きな差を、segmentだけの効果としては扱わない。u8配列とslice比較のflatにも大きな効果がある。cached-flatはblock/ifでsegmentを上回り、callでもほぼ同程度。alternatingではsegmentが約12.3%短いが、人工系列の限定的な結果である。

ばらつきも残る。例えばifのprocess中央値はflat 179.16〜273.85 µs、cached 123.49〜178.18 µs、segment 177.91〜204.03 µs。callではcached 94.24〜103.52 µsに対しsegment 86.86〜108.84 µsであり、約1.9%の差を確実な優位と主張しない。alternatingではcached 176.16〜180.22 µs、segment 153.74〜163.75 µsだった。統計的信頼区間・CPU固定・別機種検証は未実施。

幅1の反復1024では、segmentのstock比は1.25〜2.08倍。全般的な改善ではなく小arityでは退行する。predecode、pool構築、一般的なcontrol処理の費用も含む。

全processのpeak working setを保存したが、検証stackだけのmemoryではない。幅512 blockではsegment 5.49〜5.51 MB（decimal）、cached 5.27〜5.37 MB。segmentの最大stack capacityは12,288 byte、logical stack512である。singletonを最初に512個積むため、区間表現でもmemory削減になっていない。poolには共有vecとHashMapキーがあり、pool_cellsだけでは総確保量を表さない。

Wasm自体を変換しないため、実行時性能とbinary sizeの改善は測定対象外。入力sizeを上表に示し、解析準備時間・検証kernel時間・全体時間は生ログに分離している。

## 最悪ケースの反証

`fragmented-v1`は3幅×4方式×3process = **36 process**。`makeA; makeB; sink(A+B)`を1024回並べた。segmentのidentity shortcutは全条件で0だった。

| W | 比較対象セル合計 | segment / flat | segment / cached |
|---:|---:|---:|---:|
| 8 | 8,200 | 1.030 | 1.040 |
| 64 | 65,600 | 1.184 | 1.089 |
| 512 | 524,800 | 0.921 | 0.890 |

合計はW×(1024+1)。+1は生成helperのresult検証に対応する。幅512の時間差が正でも、**幅依存の検査量を一般に解消する保証は成立しない**。CPUのvector化された比較とcounterを混同しない。

## 実際のbinaryでの機会調査

NodeWasmStudy commit `53118203addbc9d421deb83289c282dfe7f27173`から既に保存してあった220本を使用。今回のために都合のよいsubsetを追加採取していないが、全Wasm市場の無作為標本でもない。

wasmparser 0.262 / WASM2設定で217本を受理し、199,281関数、50,709,111命令、4,892,619箇所のdirect call/block/loop/ifのsignatureを数えた。2本は複数memory・threadsというfeature設定外、1本は空fileなので集計外。

- 型幅0または1：72.448%。
- 幅8超：0.0581%。93 moduleには少なくとも1箇所ある。
- 幅64超：0箇所。最大34。
- parameterを持つblock、または多値resultのblock：0箇所。

これは**静的なsignature使用箇所の分布**であり、実行頻度ではない。direct call以外の命令費用も含まない。現代のGC言語やComponent Model adapterの十分な標本を調べたとは言えない。したがって自然なworkloadでの大きな高速化は未実証である。一方、untrusted入力の最悪時保護を主題にするなら自然頻度だけで却下せず、fragmented反例と幅上限を含む保証を解決する必要がある。

## 保存した失敗・未完了

初回公開source取得はDNS制約で失敗し、通常の承認審査を通した公開downloadで成功した。公式specの`wasm-2.0`名はAPI422となったため、確認済み2026-10-23 commitに固定した。WABTの初回変換はGC構文feature不足で失敗し、`--enable-all`で13本を変換できた。これらを新方式の解析失敗や安全性の効果には数えない。

現時点では、full Wasm対応、正常な公式suite全体の適用、stack表現と標準規則の機械証明、実compiler workloadでの利得、他CPUでの再現は未完了。
