# Q: Wasmの選択範囲を区別する実行結果oracle

2026-10-26。**動作する限定prototypeと比較実験。新しい主アルゴリズムの確立は未達。** 元の命令を正規化せず、実行結果の組を数値意味モデルと照合する。一般の記号実行・SMTを使い、Iの共通profileモデルも継承するため、完全に別原理の発明とは数えない。

- [事前計画](plan.md)、[アルゴリズムと範囲](algorithm.md)
- [先行研究との比較](prior-art.md)、[実測と厳格判定](results.md)
- [120件の診断とモデル修正](model-revision.md)、[研究ノート](research-note.md)
- 実測JSON・binary・source snapshotはリポジトリの`results/choice-scope/`。

## 実行環境

既存リポジトリのPython3.9、Node24.15、WABT1.0.42、Binaryen133を使用。Z3を`.tools/encoding-synthesis-python`、Wasmtime Python50.0.1を`.tools/import-alias-quotient-python`から読む。SpiderMonkey150.0.1は`.tools/spidermonkey-150.0.1/js.exe`。WABT/Binaryenの配置は`research/connectivity-elimination/prototype.py`のWABT/BINARYEN定数を参照する。WAT parserとtool wrapperを同ファイルから再利用するため、このフォルダだけのcopyでは動かない。

新しい環境では同じversionの公式配布を`.tools`へ配置する。Python packageは`z3-solver==4.13.3.0`と`wasmtime==50.0.1`。ここに特定engineのsystemインストールを要求する操作は含めない。公開sourceの追加取得は検証器の通常実行に不要。

```powershell
# リポジトリのルートから。出力先は既存dirと重ならない名前にする。
python research/choice-scope/experiment.py results/choice-scope/reproduce-screen
python research/choice-scope/independent.py results/choice-scope/reproduce-screen results/choice-scope/reproduce-independent
python research/choice-scope/benchmark.py results/choice-scope/reproduce-screen results/choice-scope/reproduce-performance
python research/choice-scope/minimal.py results/choice-scope/reproduce-minimal

# 保存済み成果物を監査する。既存audit-v1を上書きしない。
python research/choice-scope/audit.py results/choice-scope/reproduce-audit

# 元binaryの出力tupleを一つ照合する。SATはこのモデルで説明可能の意味。
python research/choice-scope/oracle.py results/choice-scope/screen-v2/nan-share.wasm '[1,0]' '[2143289345,2143289345]'
```

CLIの`--mode`はjoint/pointwise/independent-site/enumerated。`--lane-policy core-two`は古い二択解釈の診断用で、既知のbyte単位動作を拒否する。defaultはbyte-compatibleだが、規範仕様の完全なモデルであるとは主張しない。未対応はstatus=unsupported・exit2、SMTのSAT/UNSAT/unknownはJSONのstatusで読む（UNSATだけでengine bugと確定しない）。

ログを上書きしない。screen-v1/independent-v1/performance-v1は探索過程、screen-v2/independent-v2/performance-v2が修正後の主記録。minimal-v1はモデル不一致を説明する診断例で、脆弱性PoCではない。
