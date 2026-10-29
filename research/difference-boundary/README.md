# 差分メモリの境界補正：実装と評価

2026-10-19。配列の隣接byteのXOR差分を保持したまま、Wasm memory.copyと境界2点の補正で状態を更新する限定変換器。重なる補正区間を共有する版も実装した。**更新の高速化は確認したが、新しい難読化の主発明としては不採用。** 元状態と元更新則を1回の累積XORと公開profileの照合で回復でき、共有規則による保護上の追加効果は確認できない。

- [事前計画](plan.md)
- [アルゴリズム・疑似コード・意味保存・攻撃](algorithm.md)
- [先行研究・特許との技術比較](prior-art.md)
- [測定結果と範囲](analysis.md)
- [日本語論文追補](paper-note.md)

## 再現

repo root、PowerShell、Python3.9、Node24.15.0/V8 13.6、WABT1.0.42、Binaryen133。追加Python package不要。`.tools/wabt-1.0.42/bin`と`.tools/binaryen-version_133/bin`を使い、親directoryはWASM_TOOLS_ROOTで変更できる。共通部品は `research/zero-extent/prototype.py` と `research/connectivity-elimination/prototype.py`。main実行時のcopy/hashを結果のsources/へ保存する。

存在しない出力先を指定する。

```powershell
python research/difference-boundary/run.py results/difference-main
python research/difference-boundary/verify.py results/difference-main results/difference-verify
python research/difference-boundary/run.py results/difference-edge --sizes 1 2 65536
python research/difference-boundary/indexed-attack.py results/difference-indexed results/difference-main results/difference-edge
python research/difference-boundary/measure.py results/difference-main results/difference-batch
```

単体の変換・回復：

```powershell
python research/difference-boundary/prototype.py input.wasm encoded.wasm --mode shared
python research/difference-boundary/prototype.py encoded.wasm recovered.wasm --recover
```

入力はcopyとdigestの限定profile。任意のWasmの汎用メモリ変換器ではない。sourceの私有memoryを外部公開しない。正当性検査用だけにmemory exportを加えた別binaryを生成し、通常binaryと並行に呼び出して全memoryを照合する。観測用binaryを実行性能の測定へ使わない。

主結果は[main v2](../../results/invention-20261019/difference-boundary-v2/summary.json)、[検証](../../results/invention-20261019/difference-boundary-verify-v1/verification.json)、[境界追加](../../results/invention-20261019/difference-boundary-edge-v1/summary.json)、[索引付き回復v3](../../results/invention-20261019/difference-boundary-indexed-v3/results.json)、[性能](../../results/invention-20261019/difference-boundary-batch-v1/summary.json)。`run.py --compare <previous>`でbyte再現を照合できる。main v1/v2の60本は一致。主・追加は120 target binary、各観測用版も実行し計256,080呼出し、不一致0。回復は未変換12を含む60条件、変換条件だけでは48条件。

索引付き回復v1は、零dataを最適化した際のdata-count sectionの差を照合器が誤って残したため停止した実装不備。修正後のv2は完走し、v3では重複した事後検証をタイマー外へ移した。これらを保護効果と数えない。probe/main v1/索引v2の再実行は追加の独立coverageに加算しない。

研究全体の新規で有効な主発明・特許候補の確立は未達。外部公開・push・出願は行っていない。
