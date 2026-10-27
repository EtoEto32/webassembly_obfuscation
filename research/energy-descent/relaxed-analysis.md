# 全体の収束で保証する改良と、最小化消去による反証

2026-10-22。**改良は正しく動くが、独立した主発明には採用しない。** 元ゲートと逆向きの局所更新を許しても全初期値から正答する例を構成した。しかし既知の変数消去へ対応する適応的解析で、raw/O3の全28条件を通常のDAGへ回復できた。同じenergy方式の修正を独立した発明数へ加算しない。

[事前計画](relaxed-plan.md)、[生成・回復CLI](relaxed.py)、[主実験](relaxed-run.py)、[監査](relaxed-audit.py)、[性能測定](relaxed-performance.py)、[集計](relaxed-report.py)。[実測比較](../../results/invention-20261022/energy-relaxed-report-v1/comparison.md)と[集計JSON](../../results/invention-20261022/energy-relaxed-report-v1/facts.json)を保存した。

## 課題・改良・正当性

旧案は各座標の最適更新が必ず元ゲートと同じになる重みを用いたため、その局所規則が露出した。今回は元の限定Boolean DAGから、正整数重みをCEGISで合成する。対象・i64範囲・追加private memory・非対応機能は[旧設計](algorithm.md)と同じ。Wasm固有の新原理とは主張しない。

```
E(x,z) = sum_i w_i * (z_i XOR f_i(x,z_<i)),  1 <= w_i <= 65536
counterexample(w):
    find x,z such that E(x,z)>0
    and E(x,z XOR 2^j)>=E(x,z) for every internal j

start with positive bounded integer weights
repeat (maximum 128 rounds):
    minimize sum(weights) subject to accumulated counterexamples
    if counterexample is UNSAT: accept weights
    if unknown/timeout: report incomplete; do not emit a correct transform
    otherwise add OR_j(sum_i w_i * delta_error_i(j) < 0)
emit the aggregate polynomial after coordinate permutation/complements

run(x):
    initialize internal bits; hold input bits fixed
    repeat a complete coordinate sweep:
        accept each single-bit flip only if E strictly decreases
    until a complete sweep changes nothing
    return the designated output bit
```

正の重みとDAGにより、E=0の内部状態は元の計算結果ただ一つ。反例が存在しなければ、E>0で変化のないsweepは起こらない。Eは非負整数で初期値はW=sum(w)以下、各採用反転は少なくとも1減らすので、採用反転は高々W、停止確認を含むsweepは高々W+1。優越条件によるn回上界を改良版へ流用しない。SMTはBoolean数学モデルの検査であり、Wasm実装全体の形式検証ではない。

最初の6例（旧3回路と入力を3bitへ共有した3回路）は、合成しても旧優越重みと一致した。この結果を見て、事後に7例目ordered-guardsを追加した。成功例だけを事前選定したコーパスとは扱わない。

```
z0 = x0 XOR x1
z1 = x2 AND x3
z2 = x2 OR  x3
z3 = z0 AND z1
z4 = z0 OR  z2
z5 = z3 XOR z4
```

正しいz1,z2はz1<=z2を満たすが、任意の内部状態にはこの関係がない。優越重み[5,3,3,2,2,1]に対し、合成は[3,3,3,2,2,1]を得た。全Boolean入力・内部状態で誤った局所最小はない。x=1、元座標の内部bit集合z=3では、違反は[0,1,0,1,1,0]、E=7。正しいz0を誤った値へ反転してもE=6へ下がる。他の座標の修復を経れば最終的に正答へ至る。これは「全体の正答保証には各更新が元ゲートと一致する必要がある」という一般化への反例である。

## 攻撃：局所更新ではなく、変数を消してから戻す

多重線形多項式をE=A+z_j Dと書く。公開係数からDを抜き出し、q=[D<0]を計算すると、E'=A+qD=min(E|z_j=0,E|z_j=1)。qを真理値表から多重線形多項式へ戻して代入し、その変数を消す。最後にE'=0を要求する。記録したqを消去の逆順で評価すれば、全体の最小状態を再構成できる。

元DAGのsinkは自身の違反項にしか現れないため、sinkの最小化はその項を消す。従って元の逆依存順が分かれば、小さい規則を保つ消去順は存在する。これは、その順を任意の公開多項式から常に安く発見できるという証明ではない。実装は元グラフを渡さず、消去後項数が最小の候補を選ぶ貪欲法。列挙support最大20、残す規則最大5入力の上限があり、越える例は未対応とする。一般的な多項式時間解除とは主張しない。

旧解析の2条件の直接の停止理由は「回復規則が5入力lookup上限を越える」。別途その上限を外して依存を調べると、6入力を読む座標5と座標6/8の間に循環があった（物理座標）。この未対応や循環を耐性の成功に数えない。適応的な消去は、合成版でも28項→23→18→13→10→3→0と進み、通常の一回評価へ戻せた。元source、seed、ゲート別の重みを回復器へ渡していない。

表を含む任意のbinaryを信用しないため、公開係数から既知実行器を再生成してraw/O3 byte一致を確認する。別評価器は拒否する。この認識は生成族に限定され、汎用逆コンパイラの性能ではない。

## 実測と正当性検査

- 7合成回路、70条件、byte異なる37本。通常180,420呼出し、全初期値probeで別に2,922,496呼出しが一致。コーパス間の重複は除外しておらず、全般的な実アプリ評価ではない。
- 最小化消去28/28条件成功。旧解析は26成功・2未対応。主条件でクラッシュ・timeout・unknownは0。
- 7個の誤局所最小不存在式をfresh Z3 solverで再確認。等重み7例は誤った局所最小の具体例を検出し、Pythonで隣接energyを再計算した。
- 回復の248消去段について、選んだ規則が両方の値以下のenergyを与えることを別のSMT式で確認。28回復出力のsourceとのBoolean同値式もunsat。これらは抽象モデルの検査。
- 70主binaryの再生成byte一致、別実行器WABTで280呼出し一致。改変した評価器の拒否、回復出力極性を壊す負例の同値検査失敗を確認。
- binary読取・実行器照合・compile込みの回復単発総時間は約62.9–94.1ms。回復本体11反復中央値は全例約0.91–15.79ms。ordered-guardsでは約0.91–1.02msで、優越版に対する有意な増加は示していない。解析器を開発する人間の時間は未測定。

ordered-guardsのO3実行は、元版1.379ns/call、優越版242.336、合成版237.806、合成版からの回復2.976。合成版/元版約172.46、合成版/回復版約79.91。優越版も合成版も同じ動的停止規則であり、旧固定n回版との比較ではない。合成版の約1.9%の差はprocess範囲が重なり、安定した性能改善とは解釈しない。

15 fresh Node process×7batch=105batch、warmup16,384、calibration20ms目標、全batch10ms以上、固定seedでprocess順shuffle。CPU affinity/周波数固定なし。Node24.15.0/V8 13.6、`--no-liftoff --no-wasm-lazy-compilation`、Intel i9-11900K、Windows x64。別oracleで性能用5本の10,430通常呼出しと80wrapper checksumも検査した。同じ小入力領域の再確認であり、独立ベンチマークとは数えない。

最適化後サイズは元84B、優越/合成567B、回復131B。private memoryは保護版65,536B、元/回復0B。全Node processのmaxRSSは37,692–38,404KiB。生成は優越約40.1–41.5ms、合成約129–667ms（各単発、WABT込み）。少数例から一般的な変換費用を推定しない。

## 先行研究と読んだ範囲

1. Rina Dechter, *Bucket elimination: A unifying framework for reasoning*, **Artificial Intelligence 113(1–2):41–85, 1999**, DOI [10.1016/S0004-3702(99)00059-4](https://doi.org/10.1016/S0004-3702(99)00059-4)。査読論文。[著者側PDF](https://ics.uci.edu/~csp/r48b.pdf)の冒頭と§8、Figure25のelim-opt、Theorem11（PDFページ34–36）を読んだ。変数を最小化して消去し、後から最小値を与える割当を構成する原理が明示される。今回の合計多項式・Boolean規則抽出はその原理への実装上の対応であり、新しい一般解析原理ではない。全51ページや全評価を読了したという記録ではない。
2. Simon Odense, Artur d’Avila Garcez, *A semantic framework for neurosymbolic computation*, **Artificial Intelligence 340:104273, 2025**（online2024-12-31）, DOI [10.1016/j.artint.2024.104273](https://doi.org/10.1016/j.artint.2024.104273)。[大学書誌](https://openaccess.city.ac.uk/id/eprint/34394/)に査読ありと明記。[本文](https://openaccess.city.ac.uk/id/eprint/34394/1/1-s2.0-S0004370224002091-main.pdf)の冒頭とHopfield/penalty logic節、局所最小と意味対応の段落（PDFページ21–22）を確認。誤った局所最小を除く必要性は既知であり、今回の正当性条件自体を新発明としない。このCEGIS重み合成が同論文にあるとは確認していない。後続の部分取得は一度失敗し、未読部分は補完していない。

Pinkasの既存構成は[先行資料](prior-art.md)を参照。今回の特定合成器と全く同じ先行手順を確認したとは主張しないが、既知のenergy埋込み、制約合成、min-sum消去からの独立した貢献と良好な保護費用比は示せなかった。

## 判断

優越条件を緩めるだけで十分という仮説を棄却する。今回の収穫は、局所規則が循環しても、**公開energyの最小化問題を順に縮める解析が残る**と実装・実験で確認したこと。単項式を増す、極性や重みを変える、同じ因子を別評価器へ移すだけの次案は採らない。新規で有効な主方式の確立は未達であり、主目標は継続する。

## 再現

Python3.9、Node24.15.0、WABT1.0.42、Binaryen133、Z3 4.13.3。追加依存は`.tools/encoding-synthesis-python`のz3-solverで、`relaxed.py`がそこからimportする。Wasm toolsの配置は旧READMEと同じ。新しい出力directoryを指定する。

Z3がない環境では `python -m pip install --target .tools/encoding-synthesis-python z3-solver==4.13.3.0` で同じ版を配置する。今回の実行では既存の同版を使用した。最終のsource一致・596個の保存ファイルhash・構文・集計検査は[検証記録](../../results/invention-20261022/energy-relaxed-verification-v1.json)にある。

```powershell
# 現runnerは7例。初期6例の保存済みv1と合計回数を二重計上しない。
python -X utf8 research/energy-descent/relaxed-run.py results/energy-relaxed-new/main
python -X utf8 research/energy-descent/relaxed-audit.py results/energy-relaxed-new/audit results/energy-relaxed-new/main
# 性能再現を元測定と同じ1例に絞る場合
python -X utf8 research/energy-descent/relaxed-run.py results/energy-relaxed-new/coupled --only ordered-guards
python -X utf8 research/energy-descent/relaxed-performance.py results/energy-relaxed-new/coupled results/energy-relaxed-new/performance

python -X utf8 research/energy-descent/relaxed.py transform input.wasm protected.wasm
python -X utf8 research/energy-descent/relaxed.py recover protected.wasm recovered.wasm
```

保存済み主v1は初期6例、coupled-v1は追加1例。各directoryはsource snapshotとhashを保存。反例モデルの選択やround数はZ3 contextにより変わり得る。byte再生成は保存係数から検証し、CEGIS探索履歴のbyte一致を主張しない。`enumerated_candidate_rows`は上限内で採用候補となった規則の列挙行だけを合計する補助値で、全解析の作業量には使用しない。費用は壁時計の実測を用いた。
