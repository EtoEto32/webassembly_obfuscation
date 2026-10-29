# 内部変数を消した制約伝播のWasm試作

2026-10-21。別原理の具体案を実装・比較したが、**主発明への採用は見送る**。中間変数を消しても公開I/Oから同じ等価式へ回復でき、費用改善は4例中1例に限られた。既存の有限環残差方式の限定採用は維持する。

[事前計画](plan.md)、[アルゴリズム・意味保存・負の対照](algorithm.md)、[先行技術](prior-art.md)、[再開地点](checkpoint.md)を参照。元の演算DAGをCNFへ変え、内部変数をresolutionで除去し、Wasm v128上の単位伝播で出力を得る。秘密鍵や暗号的な解析不能性は仮定しない。

## 対象と実装

固定1page memory、run、arityを公開する閉じたSIMD bitwise module。固定アドレスから2–20個のv128を読み、and/or/xor/notを最大64gate計算するprofileに限定する。外部からのmemory読書きは関数呼出しの前後で許す。変換後も出力16bytes以外のmemoryを保存する。追加memoryは不要で、伝播状態はlocalに置く。

入力profileにないloop、任意の分岐、動的アドレス、call/import、共有memory、growth、浮動小数、加算carry、bitをまたぐshift/rotateは非対応。一般のC/C++バイナリ変換器ではない。専用の構文を受理するPython変換器が、WABTで実.wasmを検証・読取り・再生成する。debug/custom sectionの完全保持は保証しない。

## 正当性と回復

4例はparity8、mux9、carry12、shared16。入力Boolean変数数は8、9、12、16で、元gate数は7、28、21、57。実アプリ4種類を測定したという意味ではない。

- plain、CNF対照、内部変数消去版のraw/O3が24本。各本から公開I/Oだけで得た回復式24本を加え、計48本。
- 19,176回のvector呼出しで返値相当の出力と64KiB全memoryが一致、想定外trapは0。4例それぞれの全Boolean入力、計70,400通りを128列ずつpackし、さらに各例6定数vectorと256乱数vectorを検査した。48本の反復分を独立入力数に数えない。
- モデルでは各例256件、計1,024件の部分入力割当について、残る変数の伝播結果が失われないことを照合した。
- 24/24回復条件で等価Wasmを生成できた。各例の6条件は同じROBDD由来のbinaryへ戻り、byte一致した。元の演算DAGを復元したとはしない。
- 別実行器WABTの192 probeも一致。48本のbyte再生成を確認。非対応の有効Wasm3件を拒否した。
- 論理的に等価な節の置換でも単位伝播が止まる負の対照を実装し、raw/O3で診断trapとmemory不変を確認した。これは解析器の失敗ではない。

| 例 | 消去変数 | CNF節数→消去後 | 公開run問い合わせ | 回復BDD node |
|---|---:|---:|---:|---:|
| parity8 | 4 | 28→32 | 2 | 15 |
| mux9 | 27 | 77→103 | 4 | 133 |
| carry12 | 18 | 68→40 | 32 | 17 |
| shared16 | 40 | 200→297 | 512 | 78 |

回復は全Boolean真理値表を求めるため入力数に対して指数的で、方式とbit独立なABIを知る解析者を想定する。それでも今回の範囲では2–512回で足り、128列の並列性を攻撃側も利用できた。生成器のsource・CNF・消去順は回復器へ渡していない。今回の24条件に未対応・解析器crash・timeoutはない。別の逆コンパイラの未対応を保護効果に数えていない。

回復の問い合わせ本体は、消去版O3で約0.23/0.37/1.12/8.33ms、Node起動・表構築・コンパイル等込みは約68/73/79/91ms。ただし各1回の記録であり、分布比較や人間の解析時間ではない。問い合わせ本体にはJSでの入力packingと出力読取も含み、warmupを行っていない。下のhot実行時間と直接比較しない。

## 性能

主測定はruntime-v3。全てのraw coreへO3を1回適用し、同じ未最適化Wasm loopから呼ぶ。4例×4方式×5 fresh Node process＝80process。各processでwarmup1,024回、64回から最大1,048,576回までpilotを増やし、10msを目安にした後9batchを測定。Nodeは`--no-liftoff --no-wasm-lazy-compilation`。process内中央値を取り、さらに5processの中央値を報告する。benchmark binary16本の6,392呼出しも再照合した。

**ワークロードの制限**：loop内で最初の入力wordだけをLCGで変更し、残りの入力wordは固定乱数。入力初期化は計時外、loop・入力更新・checksum費用は計時内。全入力を毎回乱数化した結果でも、実アプリ全体の結果でもない。

単位はns/128列のrun。括弧内は5process中央値の最小–最大。

| 例 | 未変換 | CNF対照 | 内部変数消去 | 回復式 |
|---|---:|---:|---:|---:|
| parity8 | 6.14 (6.11–6.40) | 86.69 (85.78–93.42) | 100.13 (97.67–102.62) | 10.39 (10.01–10.75) |
| mux9 | 7.51 (7.41–7.72) | 147.30 (146.57–154.24) | 222.24 (203.40–228.08) | 30.54 (29.59–32.54) |
| carry12 | 7.49 (7.47–7.96) | 199.58 (197.88–212.52) | 149.66 (144.43–156.47) | 10.13 (9.66–10.56) |
| shared16 | 16.64 (15.93–17.64) | 2571.39 (2500.34–2689.43) | 3959.18 (3939.09–4081.18) | 21.83 (21.60–22.65) |

消去版はCNF対照比でcarry12だけ約25%時間減、他3例は約16–54%増。未変換比では約16–238倍の時間を要する。全例で回復式は消去版より大幅に速い。元の演算境界を消したことから、保護上の優位は導けない。

| 例 | 未変換O3 bytes | CNF対照O3 bytes | 消去O3 bytes | 回復O3 bytes |
|---|---:|---:|---:|---:|
| parity8 | 137 | 1060 | 2358 | 313 |
| mux9 | 222 | 1555 | 11307 | 1444 |
| carry12 | 237 | 1724 | 3272 | 463 |
| shared16 | 465 | 5525 | 18774 | 935 |

線形memoryは全条件65,536bytes。process peak RSSは生ログに保存し、約39–41MiBだがNode/JIT全体の値である。元moduleにmemoryを追加していないことと、local/JIT領域の費用が0であることは同義ではない。変換時間は消去版で約81/117/96/592ms、各1回のtool起動・profile検証・生成込み。変換時間の反復分布は未測定。

初回の主実験v1は最適化器のSIMD指定不足で中断した。runtime-v1は補助parserの呼出し方の誤りで計時前に停止した。runtime-v2は80process完了したが回復版だけ追加O3がないため、主比較をv3に揃えた。全履歴を残し、これらを解析耐性へ計上しない。

## 失敗原因と主張の範囲

一つの長さkの節からk個の伝播規則を作る現在の実装では、各規則に最大k−2個のANDが要る。変数数・節数が減っても、節幅とliteral数の増加で静的な演算数は増え得る。実際の速度は伝播pass数とJITにも依存し、この静的説明だけで時間差の全てを説明したとはしない。

費用削減の余地はあるが、prefix/suffixのAND共有や別の消去順だけでは、公開関数のbit独立性と小さいBoolean入力数は変わらない。したがって、閾値を調整して主発明へ格上げする方針は取らない。通常最適化後にも計算が複雑なまま残ることと、等価な小さい計算を入出力から作れないことを区別する。

既知のSAT前処理・bitslicing・論理言語への変換との差が弱く、実用的な保護効果も支持されないため主発明には不採用。意味保存するWasm生成器、伝播能力を失う反例、並列I/O回復の実装は研究資産として残す。世界初・特許取得・一般的な解析不能性は主張しない。

## 再現と証拠

Windows 10.0.26100、Python3.9.0、Node24.15.0/V8 13.6.233.17、WABT1.0.42、Binaryen133。リポジトリの`.tools`を使い、追加Pythonパッケージは不要。共通readerは`research/isotope-swizzle/prototype.py`と`research/connectivity-elimination/prototype.py`。rootから未存在の出力先へ実行する。

```powershell
python research/propagation-projection/run.py results/invention-20261021/propagation-projection-reproduction
python research/propagation-projection/performance.py results/invention-20261021/propagation-projection-reproduction results/invention-20261021/propagation-projection-reproduction-runtime
python research/propagation-projection/audit.py results/invention-20261021/propagation-projection-reproduction results/invention-20261021/propagation-projection-reproduction-runtime results/invention-20261021/propagation-projection-reproduction-audit
```

- [主実験](../../results/invention-20261021/propagation-projection-v2/manifest.json)：48本、[正当性](../../results/invention-20261021/propagation-projection-v2/checks.json)、[回復](../../results/invention-20261021/propagation-projection-v2/recovery.json)、[モデルと消去順](../../results/invention-20261021/propagation-projection-v2/model.json)。
- [主性能集計](../../results/invention-20261021/propagation-projection-runtime-v3/summary.json)、[protocol](../../results/invention-20261021/propagation-projection-runtime-v3/protocol.json)、[80processの生値](../../results/invention-20261021/propagation-projection-runtime-v3/runtime.json)。性能manifestの`sha256`は元raw、`bytes`は最適化coreから継承した項目。実測用fileには`bench_sha256`/`bench_bytes`、coreには`core_sha256`/`core_file`を使う。
- [再生成・別実行器・負例の監査](../../results/invention-20261021/propagation-projection-audit-v1/audit.json)：48本のbyte一致、192 probe、同値だが伝播しない2負例、3拒否、source/tool/evidence hash。

CLIは`prototype.py transform SOURCE OUTPUT --mode project`または`--mode cnf`、回復は`prototype.py recover SOURCE OUTPUT`。回復器が利用するのはpublic ABIとbit独立性であり、任意のWasmへ使って同値を保証するコマンドではない。
