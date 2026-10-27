# 部分文字列をまたぐ文法状態変換

**判断：主難読化候補として不採用。** 実Wasmの変換と動作確認には成功したが、方式を知る解析者が三次の係数から二項文法へ戻せる。単なる線形混合との実装上の差はあり、新規性・保護効果・特許性の確立とは区別する。

- [実験前計画](plan.md)
- [生成手順・意味保存・解除条件](algorithm.md)
- [先行研究・公報との関係](prior-art.md)
- [確定した実測レポート](../../results/invention-20261023/substring-shear-report-v1/report.md)

Windows、Python3.9、Node24、WABT1.0.42、Binaryen133。`prototype.py`が参照する共通ヘルパは `../mutation-quotient/prototype.py`、`../isotope-swizzle/prototype.py`、`../connectivity-elimination/prototype.py`。外部Pythonパッケージ不要。ツールはリポジトリの`.tools`、または`WASM_TOOLS_ROOT`配下の同名ディレクトリを使う。ネット接続不要。結果ディレクトリは毎回新しい名前を指定する。

```powershell
python research/substring-shear/run.py results/invention-20261023/substring-shear-reproduction-main
python research/substring-shear/model.py results/invention-20261023/substring-shear-reproduction-model
python research/substring-shear/audit.py results/invention-20261023/substring-shear-reproduction-main results/invention-20261023/substring-shear-reproduction-audit
python research/substring-shear/performance.py results/invention-20261023/substring-shear-reproduction-main results/invention-20261023/substring-shear-reproduction-runtime
python research/substring-shear/quartic.py results/invention-20261023/substring-shear-reproduction-quartic
python research/substring-shear/report.py results/invention-20261023/substring-shear-reproduction-main results/invention-20261023/substring-shear-reproduction-model results/invention-20261023/substring-shear-reproduction-audit results/invention-20261023/substring-shear-reproduction-runtime results/invention-20261023/substring-shear-reproduction-quartic results/invention-20261023/substring-shear-reproduction-report
```

単独変換の例：

```powershell
python research/substring-shear/prototype.py transform results/invention-20261023/substring-shear-main-v3/dyck-plain-raw.wasm tmp/substring-demo.wasm --a 1 --b 2 --c 0 --alpha 257
python research/substring-shear/prototype.py recover tmp/substring-demo.wasm tmp/substring-recovered.wasm --weighted
```

元文法や生成seedはrecoverの入力ではない。`--weighted`は0/1の元規則を仮定しない係数合同式による攻撃。`--linear`は比較用の通常線形shearと専用回復である。両方の同時指定によるweighted linear回復は非対応。

主結果はmain-v3、model-v2。main-v1はbulk memory flag不足で中断。main-v2は最初の回復器による正当な実測だが、非単元係数の合同類を列挙する上限があったため、最小剰余一つで十分とする論証に従い回復器を修正しv3を実行した。model-v1はterminal記号の生成にPython演算子優先順位の誤りがあり中断した。失敗runを回復件数や保護効果へ加算しない。
