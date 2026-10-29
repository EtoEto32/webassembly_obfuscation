# コピー互換の非線形残差表現：SHA-256への適用と解除

2026-10-21。全64roundのSHA-256圧縮を対象に、状態read/writeを公開しない実Wasm
変換を実装した。固定memory.copyを復号なしで残す構成は動いたが、raw/O3とも
バイナリだけの記号実行で同じ計算へ回復できた。独立した新規性・保護優位は未確立で
主案には不採用。有限環残差方式の過去の限定採用は取り消さない。

- [事前計画](plan.md)・[アルゴリズム、意味保存、対象範囲](algorithm.md)
- [先行技術と未読範囲](prior-art.md)・[攻撃モデル、実測、判断](analysis.md)
- [主正当性](../../results/invention-20261021/copy-fiber-main-v1/checks.json)
- [解除ログ](../../results/invention-20261021/copy-fiber-recovery-v1/recovery.json)
- [実行費用](../../results/invention-20261021/copy-fiber-runtime-v1/summary.json)
- [再現・負例・別engineの監査](../../results/invention-20261021/copy-fiber-audit-v3/audit.json)
- [集計と最終ファイルの照合](../../results/invention-20261021/copy-fiber-report-v1/report.json)

Python3.9+、Node24.15.0、`.tools/wabt-1.0.42/bin`、`.tools/binaryen-version_133/bin`。
追加Python/Node packageなし。共通WAT処理は`research/isotope-swizzle/prototype.py`と
`research/connectivity-elimination/prototype.py`を使用する。SHA定数の元資産は
[sha.jsライセンス](../../experiments/sha256-research-baseline/vendor/LICENSE)に従う。
ベンチマークのpaddingとblock連鎖はJSであり、Wasm単独の全SHA実装とは呼ばない。

リポジトリrootから、各出力先を未存在の名前にして実行する。

```powershell
python research/copy-fiber/run.py results/copy-fiber-new/main
python research/copy-fiber/attack.py results/copy-fiber-new/main results/copy-fiber-new/recovery
python research/copy-fiber/performance.py results/copy-fiber-new/main results/copy-fiber-new/recovery results/copy-fiber-new/runtime
python research/copy-fiber/audit.py results/copy-fiber-new/main results/copy-fiber-new/recovery results/copy-fiber-new/audit
python research/copy-fiber/report.py results/copy-fiber-new/main results/copy-fiber-new/recovery results/copy-fiber-new/runtime results/copy-fiber-new/audit results/copy-fiber-new/report
```

実バイナリへの単独変換と解除：

```powershell
python research/copy-fiber/prototype.py source results/cf-source.wasm
python research/copy-fiber/prototype.py transform results/cf-source.wasm results/cf-native.wasm --layers 1
python research/copy-fiber/recover.py results/cf-native.wasm results/cf-recovered.wasm
```

測定は他の重い処理と同時実行しない。全体の目標は継続中。今回は新しい特許候補が
成功した報告ではなく、非線形化・公開APIの削除でも残る失敗条件を具体化した結果。
