# 観測文脈を保持するWasm式再合成：実装・再現方法

2026-10-18。設計は[algorithm.md](../algorithm.md)、計画と結果は[experiments.md](../experiments.md)。実Wasm変換、主実験、独立式検証、別エンジン検査、アブレーションまで実施した。**保護対象60条件は全て0–2演算で復元できたため、新しい有効な保護方式としては不採用。** 実装と負の結果を再現する研究用パッケージである。

## 一括再現

Windows x64、Python3.9以降、Node24.15.0、WABT1.0.42、Binaryen133を使用。Python依存はSymPy1.13.3、mpmath1.3.0、z3-solver4.13.3.0。生成器自体はPython標準ライブラリのみで動く。リポジトリrootで実行する。

1. [WABT1.0.42](https://github.com/WebAssembly/wabt/releases/tag/1.0.42)のWindowsバイナリを`.tools/wabt-1.0.42/bin/`、[Binaryen133](https://github.com/WebAssembly/binaryen/releases/tag/version_133)を`.tools/binaryen-version_133/bin/`へ配置する。CLIは`.exe`を前提にする。別配置では親ディレクトリを`WASM_TOOLS_ROOT`で指定する。
2. Python依存を環境へ導入する。既存環境では`.tools/nonbijective-residual-cas`と`.tools/encoding-synthesis-python`を利用した。これらがない環境では以下のrequirementsを導入すれば通常のsite-packagesから読める。
3. 一括スクリプトへ**未作成の出力先**を渡す。既存結果は上書きしない。

```powershell
python -m venv .venv-research
./.venv-research/Scripts/python.exe -m pip install -r research/observation-synthesis/requirements.txt
./research/observation-synthesis/reproduce.ps1 -OutputDirectory results/research-reproduction-new -PythonCommand './.venv-research/Scripts/python.exe' -NodeCommand 'C:/Program Files/nodejs/node.exe'
```

既に依存がある現環境で検証したコマンドは次のとおり。新しい名前を使う。

```powershell
./research/observation-synthesis/reproduce.ps1 -OutputDirectory results/research-another-run -NodeCommand 'C:/Program Files/nodejs/node.exe'
```

手順全体は`results/invention-20261018/observation-reproduction-v1/`へ再実行して完走した。主表は初回の`observation-suite-v2/`を使用し、再現runを独立プログラム数や入力数へ足していない。性能値はhost負荷で変動するため、完全一致を期待する対象はバイナリ・意味・復元結果である。

## 主実験の結果とファイル

5カーネル×5方式×3設定=75条件。54,600入力条件に対し通常run、probe run、checkedを実行し、計163,800呼出しで不一致0。checkedの26,250件はmemory trap。別のwasm-interpは2,400件で一致。75出力式と60復元式を独立した係数計算で検査。対象なし15件を成功率の分母へ入れない。

出力には`plan.json`、`manifest.json`、`runtime.json`、`attacks.json`、`symbolic.json`、`memory.json`、`ablation.json`、`summary.json`、`comparison.csv`、`comparison.md`ができる。カーネル別ディレクトリにはWasm/WAT、probe、140入力の全観測値、変換証明書を保存する。`cross-engine/`、`transform-resources-sequential/`には別エンジンと変換資源の生値。`inventory.json`は集計時点の保存ファイルのSHA-256である。

`sources/`は生成開始時、`analysis-sources/`は追加分析終了時のソース。依存バイナリ自体は複製せず、版を記録した。`reproduce.ps1`とrequirementsはこのディレクトリにある。主実験の全詳細は[実測表](../../results/invention-20261018/observation-suite-v2/comparison.md)と[論文草稿](../../paper-draft.md)を参照。

## 個別コマンド

```powershell
python research/observation-synthesis/transform.py input.wasm output.wasm --mode frontier
python research/observation-synthesis/suite.py results/new-suite
node --no-liftoff --no-wasm-tier-up --no-wasm-lazy-compilation --trace-wasm-compilation-times research/observation-synthesis/suite_runtime.cjs results/new-suite run > results/new-suite/runtime.log
node research/observation-synthesis/suite_runtime.cjs results/new-suite attack
node research/observation-synthesis/suite_runtime.cjs results/new-suite memory
python research/observation-synthesis/verify_suite.py results/new-suite
python research/observation-synthesis/supplement.py results/new-suite cross
python research/observation-synthesis/supplement.py results/new-suite resources --label transform-resources-sequential
python research/observation-synthesis/ablation.py results/new-suite
python research/observation-synthesis/summarize_suite.py results/new-suite
```

PowerShellの版によって`>`がUTF-16になるため、一括スクリプトはログをUTF-8へ正規化する。個別実行の場合も集計前にUTF-8にする。一括再現が推奨経路である。独立した性能測定どうしを並列実行しない。

## 実装済み

- `core.py`：mod2^32の疎多項式、同値な式の生成、観測集合による非支配候補の保持、0/1/2演算による復元照合。
- `transform.py`：検証済み.wasmをWABTで読み、pure i32 add/sub/mulの領域を再合成して.wasmへ戻す。出力・コストのみ、seed固定のランダム、観測profileの3選択方式。
- `check_core.py`：形式多項式の一致、候補の支配関係、i32境界・乱数実行による部品検査。
- `check_binary.py`：storeと後続の範囲外loadを含む実バイナリの変換・差分試験。

実装はPython標準ライブラリ、実行検証はNode、変換はWABT1.0.42。既存`.tools`を使い、別配置は`WASM_TOOLS_ROOT`。現在の環境でPython3.9でも実行できた。出力先は新しいディレクトリを使う。

```
python research/observation-synthesis/check_core.py results/invention-20261018/observation-core-recheck
python research/observation-synthesis/check_binary.py results/invention-20261018/observation-binary-recheck
python research/observation-synthesis/transform.py input.wasm output.wasm --mode frontier
```

CLIは対象領域を最大32箇所、各96候補、書き換え深さ3、元演算数の2倍までに制限する。上限到達を記録する。式の項数上限は512。上限や未対応を防御成功とはしない。WABT生成のfolded WATを読む簡易パーサであり、custom/debug sectionの完全保存は保証しない。

## 初期部品試験の履歴

部品試験は1式 `((x*y)+(z*x))*((y*z)+1)`。候補生成前に内部値T=x*y+z*xを固定した。96候補から12個の非支配候補が残り、全96候補に、それを支配する保持候補が存在した。各728入力、計69,888照合で不一致0。96の上限に到達しており探索完了とはしない。

12候補中6個でTを直接観測でき、2個は1演算、4個は2演算で復元できた。1演算で見つからない4件を耐性の成功とはしない。T=x*(y+z)という因数分解からも、公開入力だけで2演算で再計算できる。これは明確な上界で、困難性の主張を制約する。

初回v1は0/1演算まで。v2は2演算照合を追加し、旧結果と使用ソースを保持した。試験入力の重複は独立標本数に加算しない。復元器は目標式の正規化多項式を一致判定のoracleとして使う。未知プログラムから目標自体を発見する解析ではない。コード上の式を生成規則へ渡しているわけではないが、意味一致oracleを持つ強い限定モデルと明記する。

バイナリ試験は、上記計算の前にstore、後に入力依存loadを含む1プログラム。4条件×1,096入力、計4,384実行で返り値・同一エンジンのtrapメッセージ・全64KiBメモリのbyte列が一致。各条件539入力はtrap。条件間の3,288比較のほか、基準自身の1,096再実行もこの4,384に含む。したがって4,384個の独立した入力ではない。

|選択方式|対象領域の演算数|Tの復元追加演算数（限定モデル）|
|---|---:|---:|
|元|6|0|
|出力・コストのみ|5|1|
|固定seedランダム|9|1|
|観測profile|9|2|

この表は同じ候補pool内での初期選択比較。1演算対2演算の差に対し領域コストが増えており、実用的優位性は支持していない。その後、基本MBA、O2/O3、複数カーネル、実時間・peak memoryへ評価を広げた結果が冒頭の主実験である。

## 正しさと限界

変換前後の出力多項式がmod2^32で一致した候補だけを採用する。leafはlocal.get/定数、演算はadd/sub/mulで全域的。load/store/call・除算・浮動小数点を領域へ取り込まないため、これらの評価回数や順序を変えない。今回の試験はその境界の副作用も検査したが、任意Wasm全体の形式証明ではない。

主実験でも観測profileの変化や探索候補数を保護成功には数えなかった。一般の等式探索・Pareto選択・攻撃を考慮した合成は既存で、具体的な選択規則にも有効性を確認できていない。real-world corpus、NotDec/StackSight、SaMBA/LOKI本体、JITネイティブ観測への効果は未実証である。
