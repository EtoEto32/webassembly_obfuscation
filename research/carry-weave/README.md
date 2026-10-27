# マスク分割とcarry-saveのWasm試作

加算項をbit maskで分割し、相方を異なるSIMD lane・圧縮段へ配置する候補を実装した。主90条件と追加40条件は正当性検査を通過し、全条件で元の加算項を回復できた。解析本体の費用増加はあるが、既存のCSA・MBAとの差と実用的な保護上の優位性は未確立。主特許候補には採用しない。

- [事前計画](plan.md)
- [対象範囲、アルゴリズム、意味保存、回復](algorithm.md)
- [先行論文・公報との比較](prior-art.md)
- [実測とアブレーション](analysis.md)
- [日本語草稿への追補](paper-note.md)
- [主結果](../../results/invention-20261019/carry-weave-v2/summary.json)
- [端数・境界条件](../../results/invention-20261019/carry-weave-controls-v2/summary.json)
- [再現監査](../../results/invention-20261019/carry-weave-audit-v1/summary.json)

## 環境・実行

Python3.9.0、Node24.15.0/V8 13.6、Windows10.0.26100、Intel Core i9-11900Kで実行した。外部Pythonパッケージは不要。WABT1.0.42を`.tools/wabt-1.0.42/bin`、Binaryen133を`.tools/binaryen-version_133/bin`へ置く。共有readerに`research/isotope-swizzle/prototype.py`と`research/connectivity-elimination/prototype.py`を使用する。リポジトリrootから実行し、outputは未存在のディレクトリを指定する。

```powershell
python research/carry-weave/run.py results/carry-local
python research/carry-weave/controls.py results/carry-local-controls
python research/carry-weave/model.py results/carry-local-model
python research/carry-weave/verify.py results/carry-local results/carry-local-verify
python research/carry-weave/performance.py results/carry-local results/carry-local-performance
python research/carry-weave/report.py results/carry-local results/carry-local-performance results/carry-local-report
python research/carry-weave/run.py results/carry-local-replay
python research/carry-weave/audit.py results/carry-local results/carry-local-replay results/carry-local-performance results/carry-local-verify results/carry-local-model results/carry-local-controls results/carry-local-audit
```

性能測定中は他の重い処理を実行しない。実行・解析の時間はhash再現の対象ではない。監査は180本の主対象・回復バイナリの再生成一致、正当性記録、別実行器の入力hash、追加条件、checksum、ソースsnapshotを検査する。`run.py --small`は小規模probeで、90条件を前提とする監査には使用しない。

```powershell
python research/carry-weave/prototype.py transform results/carry-local/n32-k1-source.wasm results/carry-custom.wasm --mode splitcsa --seed 37
python research/carry-weave/prototype.py recover results/carry-custom.wasm results/carry-recovered.wasm
```

主系列は`carry-weave-v2`、`performance-v2`、`verify-v2`、`controls-v2`、`model-v1`。初期reader不備とzero-padding対応前の結果も削除せず保存した。詳細は[分析](analysis.md)に記載する。研究全体の新規で有効な発明の確立は未達であり、外部公開・push・出願は行っていない。
