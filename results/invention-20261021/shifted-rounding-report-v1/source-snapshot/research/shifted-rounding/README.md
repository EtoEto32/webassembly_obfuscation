# 倍率に合わせて丸め格子を移す候補の検証

2026-10-21。**実装と意味保存の有限検証は成立したが、難読化の主案としては採用しない。**
演算ごとにbinary32の値を異なる2の冪で拡大・縮小し、binary64の中で丸め格子も一緒に移す。
内部の明示的なf32への復号を省く案だったが、方式既知の解析では倍率伝播と丸めhelperの認識だけで元の演算順序を回復できた。
復元できること自体を難読化一般の失敗条件にはしない。本案では復元本体が小さく、倍率変更の独立した保護利得を示せず、通常入力の実行費用が増えていることを合わせて判断する。

[事前計画と追加仮説の時点](plan.md)、[アルゴリズム・意味保存の条件](algorithm.md)、
[先行研究との対応](prior-art.md)、[保存値からの比較表](../../results/invention-20261021/shifted-rounding-report-v1/comparison.md)。
既存の[有限環残差フィードバックの構成的提案](../repository-assessment-20261021.md)の限定採用を取り消す判断ではない。

## 実装範囲と保護目標

`prototype.py input.wasm output.wasm` が実バイナリを読み、WABTで検証・読取・再生成する。
対象は1–16個のf32引数、f32局所変数、add/sub/mulだけからなる最大512 nodeの純粋DAGと、
元からcanonical NaNを返すi32 bit API `run` を持つ閉じたmodule。メモリ・import・global・loop・div・min/max・途中のbit観測・任意のアプリは対象外。
符号付き零を保持し、演算の再結合やFMA化は行わない。NaN payloadの保存契約を後から弱める変換ではない。

解析者は全バイナリ・入出力・生成方式を知る。倍率は公開定数であり秘密鍵ではない。
保護タスクは元のf32演算の依存関係と順序の回復。暗号としての秘匿を目標にしない。

| モード | 処理 | 比較目的 |
|---|---|---|
| plain | 元のnative f32 | 未変換対照 |
| eager | 各演算で倍率を戻しf32演算後に再符号化 | 同じ倍率の素朴な対照 |
| grid0 | 全倍率0でsoftware丸め | 高精度エミュレーションのアブレーション |
| shifted | nodeごとの倍率と丸め格子を移動 | 今回の仮説 |

## 保存実験の結果

multiply-add、horner6、butterfly4、cancellationの**4個の合成kernel**を使った。
32条件は4 kernel × 4モード × raw/O3であり、32個の独立した実アプリではない。

- 主実験: 各条件6,400入力、計204,800呼出しが独立した整数演算のf32 oracleと一致。
  境界16値の三重積4,096件、乱数2,048件、相殺関連256件。全バイナリがWABT validationを通過。
- 量子化器: 7倍率、境界・乱数・特殊値をraw/O3で計16,380件照合。不一致0。
  この単体対照はJavaScriptのMath.froundを使うため、主実験の整数oracleと区別する。
- 適応解析: grid0/shiftedの16条件中16条件から元と同じ順序の演算DAGを回復。shifted単体は8/8。
  復元した16本も102,400呼出しで一致。復元器へ元DAG・seed・target manifestは渡さない。
- 追加監査: 48 binaryのbyte再生成一致、WABT interpreterで384呼出し一致、妥当なWasmである5件の不適合入力を拒否。
  途中の丸めを消した負例では、正解+0が`0xa8800000`になり不一致を検出。
- 復元時間: 16条件の各11回の中央値は本体0.223–0.340ms、WABT読取16.027–16.823ms。
  公開helper profileの事前準備と人間による方式理解は計時外。汎用逆コンパイラの性能ではない。

初期の復元v1/v2は各12成功・4未対応だった。grid0のO3で引数が定数化され、localの置き方も変わったためで、
定数化profileとlocal代入の正規化を加えたv3で全件回復した。初期の未対応を保護成功に数えない。
各runで繰り返した量子化器probeを独立した新しい検体として合算しない。

## 性能と効果の範囲

通常値・符号付き零で72 fresh Node process、追加のunderflow入力で36 processを測定。
3 kernel × 4モード × 3入力分布、各3 process。Wasm内の反復loopを用い、JSとの境界通過を呼出しごとに含めない。
各processは1,024呼出しwarmup、最大2^20呼出しまで10msを目標に校正、9 batch。
高速条件は上限で目標未満となる。引数生成・checksumを含む時間であり、演算命令だけの時間ではない。

| 入力 | kernel | plain ns | shifted ns | grid0 ns |
|---|---|---:|---:|---:|
| 通常値 | multiply-add | 2.257 | 9.138 | 7.000 |
| 通常値 | horner6 | 3.329 | 51.525 | 41.418 |
| 通常値 | butterfly4 | 3.506 | 50.544 | 41.146 |
| underflow | multiply-add | 25.428 | 12.182 | 10.645 |
| underflow | horner6 | 150.439 | 94.928 | 85.288 |
| underflow | butterfly4 | 168.973 | 77.662 | 65.722 |

underflow入力ではshiftedがplainより約37–54%短いが、倍率0の対照はさらに速い。
binary32の非正規化数をbinary64内で扱うことと整合する結果であり、hardware counterによる原因確認はしていない。
倍率変更による保護効果や未知の数値計算法の実証とはしない。CPFloatそのものは未実行。
O3サイズはplainの65/99/128 bytesに対しshiftedの419/646/777 bytes。
変換時間は読取・生成・compile/validate込み35.758–42.084ms（各条件1回、O3処理を除く）。
linear memoryは未使用。108 processの最大RSSは37,876–38,488KiBで、追加のf64 local・JIT・stackの費用がないという意味ではない。

測定環境はWindows 10.0.26100、Intel64 Family 6 Model 167、Python3.9.0、Node24.15.0/V8 13.6、
WABT1.0.42、Binaryen133。Node flagsは`--no-liftoff --no-wasm-lazy-compilation`。
CPU affinity/周波数固定なし。性能の反復値・batch数・RSSは生JSONに保存。複数engineの性能評価ではない。

## 再現

リポジトリrootで実行する。Python標準ライブラリのみを使用し、NodeをPATHへ、
WABTを`.tools/wabt-1.0.42/bin`、Binaryenを`.tools/binaryen-version_133/bin`へ配置する。
共有readerとoracleは同じリポジトリ内のzero-sign-transport、isotope-swizzle、connectivity-eliminationに依存する。
出力先は毎回新規directoryとし、保存実験へ上書きしない。

```powershell
python research/shifted-rounding/run.py results/replay-shifted-main
python research/shifted-rounding/analyze.py results/replay-shifted-main results/replay-shifted-recovery
python research/shifted-rounding/performance.py results/replay-shifted-main results/replay-shifted-runtime
python research/shifted-rounding/performance.py results/replay-shifted-main results/replay-shifted-underflow --underflow
python research/shifted-rounding/audit.py results/replay-shifted-main results/replay-shifted-recovery results/replay-shifted-audit
```

単体変換・方式既知の復元:

```powershell
python research/shifted-rounding/prototype.py results/replay-shifted-main/horner6-source.wasm results/replay-shifted-target.wasm --mode shifted --seed 37
python research/shifted-rounding/recover.py results/replay-shifted-target.wasm results/replay-shifted-restored.wasm --profiles results/replay-shifted-recovery/profiles/profiles.json
```

保存結果の集計のみを再実行:

```powershell
python research/shifted-rounding/report.py results/replay-shifted-report
```

`results/invention-20261021/shifted-rounding-report-v1`には集計、実験入力のhash一覧、
共有依存を含むsource snapshotを保存する。`main-v1/sources`は初回の履歴として保持し、最終復元器に置き換えない。
全入力の形式的同値証明、一般Wasmへの適用、第三者による独立再現、既存難読化製品との同費用比較は未完了。
