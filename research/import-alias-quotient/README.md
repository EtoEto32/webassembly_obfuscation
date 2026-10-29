# import同一性を使うWasmの比較検査（G）

2026-10-24。複数memory importが同じhost objectを指す場合を、memory indexを統合した別moduleと照合する検査器。**主発明として不採用**。既存`wasm-merge`と再公開wrapperで全198条件を代替でき、統合操作自体の新規性を否定する証拠が得られた。検査資産として保存する。

[構成・請求項たたき台](algorithm.md)、[先行技術と採否](novelty-analysis.md)、[実測](results.md)、[事前計画](plan.md)、[既知WABT問題](reader-note.md)。

## 再現

リポジトリルートから、まだ存在しない出力先を指定する。Python 3.9、Node 24.15.0、WABT **1.0.42**、Binaryen 133を使用する。WABTのmemory.init出力順の既知問題を限定補正するため、他のWABT版は再監査まで拒否する。WABT/Binaryen探索は`research/connectivity-elimination/prototype.py`を利用する。

```powershell
python research/import-alias-quotient/probe.py results/import-alias-quotient/repro
python -m pip install --target .tools/import-alias-quotient-python wasmtime==50.0.1
python research/import-alias-quotient/cross-engine.py results/import-alias-quotient/repro results/import-alias-quotient/repro-cross
python research/import-alias-quotient/merge-baseline.py results/import-alias-quotient/repro results/import-alias-quotient/repro-cross results/import-alias-quotient/repro-merge
```

全memoryは非shared memory32、最小1/最大3page、import数2～4。memory.init/data.drop、copy重複、grow、trap前の書込み、active data初期化順を扱う。任意Wasmの同値証明器ではなく、関数import・threads・memory64・異なるlimits等は対象外。検査範囲と実装の受理範囲は同じではない。start関数は変換器が保持するが、この実験では生成していない。

ソースsnapshot、入力と生成binary、全呼出しの参照観測、実行ログ、ハッシュは各結果directory内に保存する。失敗したv1/v2も残す。公開・push・上流への報告は行っていない。
