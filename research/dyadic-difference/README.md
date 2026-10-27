# 2進刻みの差分評価：実装・設計修正・反証

2026-10-22。**主発明として不採用**。元の多項式を呼ばず差分だけを累積する実Wasm変換と、到達不能入力で差分を乱す修正版を作成した。最初の静的攻撃を修正版は拒否したが、方式既知の公開34問い合わせ攻撃で全条件が回復した。[設計と論証](algorithm.md)、[近接先行技術](prior-art.md)、[事前計画と修正理由](plan.md)。

## 結果

3/7/11次の合成多項式をraw/O3で検査。3実アプリの評価ではない。

| 区間 | 実行対象 | 正当性 | 適応的回復 |
|---|---|---|---|
| 初版 | 正30条件、unique正20 binary、負6 | 正247,830呼出し一致、負6全件で反例。別WABT240呼出し一致 | naive/deltaの12/12をbinaryだけから回復。8条件は元と異なる係数だが同じ関数 |
| 修正版 | 元/差分/guardedと回復、正36条件、unique正20 binary | 297,396呼出し、別WABT288呼出し一致 | 全18条件が各34問い合わせで回復。guardedの6条件も成功。静的回復器の6拒否は保護成功に数えない |
| 高次数の追加対照 | 1種類の再帰式を深さ5/12/20、raw/O3と回復、12条件 | BigInt独立oracleで49,260呼出し、別WABT96呼出し一致 | 6/6が34問い合わせで回復。形式次数32/4,096/1,048,576から32/30/30次の代表へ |

初版と修正版には共通binary・同じ入力例があるので、これらを独立した成功件数として合算しない。再生成時の実行も独立例に加算しない。各主条件の8,261入力は下位4,096語、境界69入力、random4,096入力。全32bitを入力できるが、全2^32入力を実行したわけではない。予期しないtrapは0。元profileにmemory・trapがないため、一般の副作用保存を実証したとはしない。

初版helperは12条件×32step×147入力＝56,448回をNodeと独立差分モデル・静的多項式に照合した。小幅1..10、次数1..12、各8係数組の960設定で全剰余196,416入力を検査。誤形式微分6条件に加えて、余分なexport・誤ったstep31・最上位bitを飛ばすdriverを拒否した。主36本と修正版36本は再生成してbyte一致。

初版の静的回復は5反復×12条件で60回測定し、deltaの総時間中央値は約79.8–132.6ms、naive比約0.808–0.955。差分生成により解析側も軽くなった。積分と証明用計算は約0.22–1.21ms。公開34問い合わせ回復の総時間は単発約67.9–91.5msで、安定した解析性能分布とはしない。問い合わせtranscriptは元/差分/guardedで同一だった。

## 性能と費用

以下は修正版と対照を同じ測定区間で比較。各3 fresh process、各7batch、合計36process/252batch。10ms未満のbatchは0。単位はns/word、3processの各batch中央値の中央値。

| 例 | 元 | 差分 | guarded | 回復 | guarded/元 | 元/guarded bytes |
|---|---:|---:|---:|---:|---:|---:|
| cubic | 1.586 | 147.092 | 160.252 | 1.394 | 101.05 | 55 / 1,470 |
| septic | 1.739 | 168.664 | 170.340 | 1.743 | 97.97 | 94 / 2,733 |
| degree11 | 2.526 | 167.580 | 159.973 | 2.623 | 63.34 | 131 / 3,984 |

warmup16,384回、15ms目標の校正、別module wrapperからimport呼出し。LCGによる全word入力更新・checksum費用を含む。Node24.15.0 / V8 13.6.233.17-node.48、Windows、Core i9-11900K、`--no-liftoff --no-wasm-lazy-compilation`。CPU affinity/周波数を固定していない。範囲は生ログに保存し、小さな時間差を優位性としない。回復式はO3入力から生成したHorner出力で、生成後のBinaryen再最適化はしていない。V8フラグは同じ。

linear memoryは全条件0。Node全体のpeak RSSは修正版測定で36,424–37,536KiB。初版deltaの変換時間は3個別生成で約77.5–80.5ms、反復性能測定ではない。初版の差分/naive実行比は約0.989/1.023/0.773で、11次では約23%削減したが、未変換からの負担は大きい。差分の効率化と難読化の有効性を混同しない。

## 意味と新規性

有限差分化、Newton補間、有限環の零多項式は先行する。ν2(34!)=32により、一変数の整数係数多項式関数mod2^32には次数33以下の代表があり、34値から回復できる。係数の非一意性は等価実装の作成を妨げない。主発明には採用せず、同じ関数classに留まる次数・noise変更を繰り返さない。

34点から任意の未知関数の多項式性を判定したとは主張しない。34点を一致させて`0xdeadbeef`だけ値を変える範囲外関数では回復候補が誤る反例を保存した。主例の同値性は、ソースを回復器へ渡さない攻撃の後に、独立した採点で零関数証明条件も確認する。

## 再現

リポジトリroot、Python3.9+標準ライブラリ、Node24.15.0、WABT1.0.42、Binaryen133。`.tools/wabt-1.0.42/bin`と`.tools/binaryen-version_133/bin`を使用。共通readerは`research/isotope-swizzle/prototype.py`と`research/connectivity-elimination/prototype.py`。出力directoryは未存在の名前を選ぶ。

```powershell
python -X utf8 research/dyadic-difference/run.py results/difference-main
python -X utf8 research/dyadic-difference/performance.py results/difference-main results/difference-perf
python -X utf8 research/dyadic-difference/audit.py results/difference-main results/difference-perf results/difference-audit
python -X utf8 research/dyadic-difference/guarded.py results/difference-guarded
python -X utf8 research/dyadic-difference/performance.py results/difference-guarded results/difference-guarded-perf
python -X utf8 research/dyadic-difference/guarded_audit.py results/difference-guarded results/difference-guarded-perf results/difference-guarded-audit
python -X utf8 research/dyadic-difference/high_degree.py results/difference-high-degree
```

個別変換は`prototype.py source.wasm output.wasm --mode delta|guarded|naive`、静的回復は`recover.py encoded.wasm recovered.wasm`、公開問い合わせ回復は`public_recover.py input.wasm recovered.wasm`。profileと攻撃のpromiseは[algorithm.md](algorithm.md)に従う。

保存済み：[初版](../../results/invention-20261022/dyadic-difference-v1/manifest.json)、[初版監査](../../results/invention-20261022/dyadic-difference-audit-v1/audit.json)、[修正版](../../results/invention-20261022/dyadic-difference-guarded-v1/manifest.json)、[修正版監査](../../results/invention-20261022/dyadic-difference-guarded-audit-v1/audit.json)、[高次数](../../results/invention-20261022/dyadic-difference-high-degree-v1/analysis.json)、[条件外の反例](../../results/invention-20261022/dyadic-difference-guarded-v1/outside-promise.json)、[比較表](../../results/invention-20261022/dyadic-difference-report-v1/comparison.md)、[集計値](../../results/invention-20261022/dyadic-difference-report-v1/facts.json)。各directoryに生データ、hash、producer snapshotを保存した。

汎用逆コンパイラ、実アプリ、全ツールの形式検証、特許性の確認は未達。今回の否定的結果は既存の有限環残差方式の構成的候補を取り消すものではなく、新しい主発明の成功にも読み替えない。
