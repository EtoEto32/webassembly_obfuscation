# 逆向き受理情報の混合：実装と反証

2026-10-22。実Wasm変換・差分検査・適応的回復・性能比較を完了。**主発明には不採用**。符号化を解かずに、小さな観測関数の閉包から元DFAを得られる。[アルゴリズムと論証](algorithm.md)、[近接する既存研究](prior-art.md)、[事前計画](plan.md)。

## 実測結果

3つの小さなDFA（4/6/7状態）、未変換・逆向きvectorのみ・非線形混合2seedをraw/O3で比較。主48 artifact条件のうち正42条件、unique正binaryは24本。正条件182,532呼出し（期待trap840）に不一致0。各条件の入力は全長0..10の2,047語、境界231例、random2,048例、範囲外20例。意図的に読取順を誤った6条件は全て反例を検出した。テスト回数は全入力の同値性証明ではない。

逆向きvectorと混合版の18/18条件をbinaryだけから元binaryへ回復。回復器への元ソース・seed・encoding・実行oracleの提供は0。監査では同じ18条件のhelperについて、全小状態と上位bit全0/全1をNodeで7,488呼出し照合し、静的評価器・独立の生成モデルと一致。別WABT interpreterの336呼出し（42trap）、9拒否対照、48本のbyte再生成も一致した。再生成時の主テスト再実行は独立した追加プログラム数に加えない。

O3、混合seed221011、32記号を1回処理する時間。中央値は3 fresh processの各7batch中央値から算出。

| 例 | plain ns | vectorのみ ns | 混合 ns | 混合/plain | plain/混合 bytes |
|---|---:|---:|---:|---:|---:|
| suffix001 | 184.04 | 189.50 | 214.47 | 1.165 | 176 / 284 |
| contains01101 | 186.88 | 205.11 | 742.77 | 3.975 | 201 / 1,445 |
| mod7 | 197.93 | 229.94 | 2,234.34 | 11.288 | 225 / 3,608 |

27 fresh process、189batch、10ms未満のbatchは0。warmup1,024回、15ms目標の反復回数校正、別moduleのimport wrapper。LCG入力生成・checksum・呼出し費用も含む。Node 24.15.0 / V8 13.6.233.17-node.48、Core i9-11900K、Windows。`--no-liftoff --no-wasm-lazy-compilation`。CPU固定・周波数固定は行わない。分散とRSSは生JSONに保存。linear memoryは全条件0で、RSSはNode全体の値。mixedの変換時間は6個別生成で約76.0–89.8ms、安定した性能比較用の反復測定ではない。

解析はvectorのみ/混合seed221011のraw/O3を各5回、順序無作為化して60回測定。混合の読取・driver検査・出力込み中央値は約79–195ms、vectorのみ比約1.008–2.377。O3は約115/134/187msで比約1.013/1.180/1.620。truth table構築の費用増はあるが、観測閉包自体は約0.017–0.111msに留まる。これを人間の解析時間の測定とは扱わない。

## 再現

リポジトリルートで実行。Python 3.9+、Node 24.15.0、`.tools/wabt-1.0.42/bin`、`.tools/binaryen-version_133/bin`を使用。標準Pythonライブラリのみ。ツール共通部分は既存の`research/isotope-swizzle/prototype.py`と`research/connectivity-elimination/prototype.py`に依存する。

```powershell
python -X utf8 research/reverse-observer/run.py results/reverse-observer-reproduction
python -X utf8 research/reverse-observer/performance.py results/reverse-observer-reproduction results/reverse-observer-performance-reproduction
python -X utf8 research/reverse-observer/audit.py results/reverse-observer-reproduction results/reverse-observer-performance-reproduction results/reverse-observer-audit-reproduction
```

出力先は未存在のdirectoryを指定する。個別変換は`prototype.py input.wasm output.wasm --mode mixed --seed 221011`、回復は`recover.py encoded.wasm recovered.wasm`。入力profileは[algorithm.md](algorithm.md)に限定される。

保存済み結果：[主実験](../../results/invention-20261022/reverse-observer-v1/manifest.json)、[差分検査](../../results/invention-20261022/reverse-observer-v1/checks.json)、[性能](../../results/invention-20261022/reverse-observer-performance-v1/runtime.json)、[監査](../../results/invention-20261022/reverse-observer-audit-v1/audit.json)。主99・性能59・監査409ファイルのhashとproducer snapshotを保存。外部公開・pushは行っていない。

この小さな反証から、すべての大規模状態符号化が容易だとは結論しない。新規性の確認、一般アプリの評価、方式を知らない汎用逆コンパイラの評価、全入力のツール検証は未達。既存の有限環方式の構成上の候補とは別の結果として保持する。
