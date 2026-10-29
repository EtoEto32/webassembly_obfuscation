# 出力履歴による内部状態の消去：実装と反証

2026-10-19。元の内部状態yを消すWasm変換を作ったが、**有効で新規な主発明としては採用しない**。偶数係数のためyが一意に戻らなくても、w=b*yだけを持つ短い等価実装へ戻せる。解除不能性を要求したためではなく、今回の変換に追加の保護優位性と独立した新規性を確認できなかったためである。

主32本・66,080呼出し（trap9,216）で値・trap・公開memoryの不一致0。WABT224呼出しも一致。異なる元プログラムが同一historyバイナリになる3組を実際に生成し、b=0の端点を含む追加9本・18,585呼出しも一致した。8/8のhistory条件を、元yの復元なしにquotientのバイナリへ回復した。24条件のsource/history/quotientを同じ検査器で処理した比較も保存。

[アルゴリズムと条件](algorithm.md)、[先行研究・読了範囲](prior-art.md)、[実測](analysis.md)、[日本語草稿](paper-note.md)、[多項式拡張の限界とrotate反例](extension.md)を参照。全入力について実装が機械証明されたとは主張しない。研究全体・特許性の確立は未達。

## 再現とCLI

Python3.9以上、Node24.15.0、WABT1.0.42、Binaryen133を使用。Windowsの`.exe`配置を前提とし、既存の`.tools/wabt-1.0.42/bin`と`.tools/binaryen-version_133/bin`を利用する。別配置は`WASM_TOOLS_ROOT`で指定できる。実験にネットワーク・課金・外部公開は不要。

```powershell
python research/output-recurrence/run.py results/recurrence-reproduction
python research/output-recurrence/verify.py results/recurrence-reproduction results/recurrence-verification
python research/output-recurrence/compare.py results/recurrence-reproduction results/recurrence-analysis
python research/output-recurrence/extension.py results/recurrence-extension
```

出力先は新しいディレクトリにする。`run.py NEW --compare OLD`でバイト再現を照合できる。性能測定中は他の重い処理を並行実行しない。

```powershell
python research/output-recurrence/prototype.py transform source.wasm history.wasm
python research/output-recurrence/prototype.py recover history.wasm recovered.wasm
```

CLIは任意Wasm変換器ではない。実際に係数をprivate memoryから読み出す、指定profileのscan moduleを受理し、全moduleを再構築して照合する。原状態を返す・memory副作用を加える・private memoryを公開する等の変更は拒否する。生データは[主v2](../../results/invention-20261019/output-recurrence-v2/summary.json)、[正当性](../../results/invention-20261019/output-recurrence-v2/correctness.json)、[比較](../../results/invention-20261019/output-recurrence-compare-v1/comparison.json)、[負の対照](../../results/invention-20261019/output-recurrence-verify-v1/controls.json)にある。

v1とv2は主実装が同じで、v2は別出力先への再実行。verify/compareはv1のバイナリを使用し、v1/v2の32本のbyte一致で対応を監査する。元の未関連ファイル、外部公開、push、出願を変更しない。
