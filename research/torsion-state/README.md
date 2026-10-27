# 非単射な持続状態表現と公開応答による回復

2026-10-22。**動作する変換・回復器と実験を保存したが、主発明には採用しない。** 呼出しをまたぐ整数状態を一対一には戻せない表現へ移した。しかし外部の挙動が低次元の線形系のままなので、公開応答だけから同等な漸化式を回復できた。既存の有限環残差フィードバック候補とは別の実験であり、その構成上の評価を撤回するものではない。

- [事前計画](plan.md)、[アルゴリズム・意味保存・回復条件](algorithm.md)、[先行研究の確認範囲](prior-art.md)
- [実測比較](../../results/invention-20261022/torsion-state-report-v1/comparison.md)、[集計JSON](../../results/invention-20261022/torsion-state-report-v1/facts.json)、[草稿追補](paper-note.md)

## 実装

sourceの1回の呼出しは `x'=Ax+Bu; y=Cx'`。全計算はmod2^32。privateなi32 globalで状態を保持し、公開APIは`step(i32)->i32`と零に戻す`reset()`。

`z=UDx`、D=diag(2^s_i)、Uは可逆行列として、zだけを保持する新しい更新を生成する。Dが非可逆なので、全xを一意に戻すdecoderは存在しない。一方、失われる状態差をAが保存しCが観測しないことが必要。生成器はこの条件と行列恒等式を確認する。到達状態上では零になる摂動Kも比較した。

`prototype.py`は実`.wasm`を読み、2–8状態のcanonical profileを確認して変換する。import/memory/table/追加export、非線形式、他の副作用・trap等は非対応。任意のWasmから線形部分を自動抽出する汎用passではない。固定幅整数globalはWasmで扱いやすいが、原理がWasmだけに特有とは主張しない。

```powershell
python research/torsion-state/prototype.py quotient input.wasm output.wasm --shifts 0,8,24
python research/torsion-state/prototype.py recover output.wasm recovered.wasm --bound 8
```

公開I/O回復器は`query.cjs`でinstantiateし、reset後に1,0,...,0の16回のstepを呼ぶ。source行列、内部global、U/D、seed、manifestは読まない。状態数上限8というpromiseを使い、合成数modulusで線形合同式を解く。偶数の逆元を仮定しない。

## 実験結果

状態2/3/4と精度配置の3設定。同じ線形系族の設定違いであり、3つの独立アプリとは数えない。plain/可逆basis/非単射quotient/零摂動perturb × raw/O3とその回復版を検査した。

|検査|結果|
|---|---|
|正48条件（byteが異なる27本）|step807,024回、reset6,816回、不一致0・予期しないtrap0|
|公開I/O回復|全24条件成功、各reset1回・step16回。回復次数2/3/4|
|別実行器|WABTで384 step一致。各wrapper内resetと公開resetも実行|
|再生成|正48本のbyte一致|
|binaryの前提確認|全24条件に対し線形・零reset・状態数・更新後状態による観測を別検査|
|solverの独立検査|mod2/4の2変数2式を全列挙、mod8/16を各512例。計5,184系で全解列挙oracleと整合|
|負の対照|誤った零摂動の3設定すべてで不一致を検出。核条件・出力条件の違反2例を拒否|

各正条件に16,813入力stepと142resetを与えた。境界値、ランダム系列、途中reset、4,096回の零入力tailを含む。型や入力の有限検査は、実装全体の数学的な同値性証明ではない。

O3実行時間の中央値（ns/step）：

|状態数|元|可逆basis|非単射quotient|零摂動perturb|回復後O3|
|---|---:|---:|---:|---:|---:|
|2|2.251|2.315|2.308|2.316|2.385|
|3|3.273|3.410|3.368|3.372|2.631|
|4|4.729|5.077|5.179|5.011|3.122|

非単射版/元版は約1.03–1.09。可逆版との差は小さく、ばらつきと重なる条件もある。回復版が常に最速とはしていない。全条件linear memoryは0。globalの論理payloadは元/変換で8/12/16byte、回復で12/20/28byteだが、これはV8の実割当量ではない。Node全体maxRSSは36,048–36,268 KiB。

性能は15条件×3 fresh process×7batch。16,384 stepのwarmup、15ms校正、共通Wasm loop内で入力を更新しchecksumを観測、resetは計時外。`--no-liftoff --no-wasm-lazy-compilation`。315batch中10ms未満0。CPU固定・周波数固定なし。変換9回の単発測定は約36–38ms、標準tool起動を含む。

回復の合同式処理は、同一の応答データに対する31反復の中央値で約0.079/0.141/0.230ms。全pipelineの単発測定は約66–93msでNode/WABT起動・コンパイルを含む。全方式の応答列が同一のため、非単射化とKの追加はこの攻撃の問い合わせ数を増やしていない。

## 保証できない範囲

16回で十分なのは、零初期、線形、時不変、状態数上限8、更新後の状態の線形観測という前提のもとだけ。`certify.py`でこれを別途検査した。回復器に行列を渡したわけではない。

実際の[反例](../../results/invention-20261022/torsion-state-audit-v1/control-checks.json)：

- `0xdeadbeef`入力だけ出力を1増やす系は、16個の実験入力では元と同じ応答を返し、その入力で回復版と相違する。
- 17状態の遅延系は最初の16応答が零で、17回目に相違する。上限を17へ直すと34応答から回復でき、別の系列4,096呼出しが一致した。

任意プログラムの同値性を標本だけで証明したとは主張しない。元の全内部状態やsource行列を復元した結果でもない。同等な短い入出力規則を得た、という保護目標上の結果である。

## 新規性と採否

Reeds–Sloane (1985)は合成数modulusでの漸化式合成を扱う。有限環上の状態表現も既存の研究分野である。本案の具体的な生成・loweringは実装したが、独立した難読化原理としての新規性を確認できず、追加の保護効果も示せなかった。全状態が一意に復号できないことを、計算規則の回復困難性へ読み替えない。この案を新発明の数に加算しない。

## 再現

Windows、Python3.9以上、Node24.15.0、`.tools/wabt-1.0.42/bin`と`.tools/binaryen-version_133/bin`。外部Python/npm package不要。共有WAT helperは`research/connectivity-elimination/prototype.py`。rootから未使用の出力名で実行する。ソースsnapshotと結果のhashを各directoryに保存し、既存出力を上書きしない。

```powershell
python research/torsion-state/run.py results/torsion-new/main
python research/torsion-state/performance.py results/torsion-new/main results/torsion-new/performance
python research/torsion-state/audit.py results/torsion-new/main results/torsion-new/performance results/torsion-new/audit
python research/torsion-state/report.py results/torsion-new/main results/torsion-new/performance results/torsion-new/audit results/torsion-new/report
```

性能測定中は他の重い実験を並行実行しない。今回の全processはexit0で終了した。
