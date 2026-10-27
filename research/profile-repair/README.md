# I: 共通profileを保つ部分決定化

WasmのRelaxed SIMDで、同じ環境選択に依存する演算を一部だけ厳密化すると、元は同じだった判断結果が変わる場合がある。実Wasmでその反例を確認し、相関を保持して必要な変更箇所を選ぶ限定CLIを実装した。**新規性・特許性は未確立**。

25設計例では99site中14を変更し、独立siteモデルは92を変更した。追加80生成例では197対220で、差は意図的に相関を作った系列だけに現れた。第三者NoWaSetの219非空binaryには対象命令がなく、XNNPACK由来の縮小例は既存設計のままで正しかった。**主特許候補への昇格は保留**する。

命令変更に代えて事前のテーブル表現を補償する見直しも[実装・実験](compensation.md)した。通常profileの表は既存XNNPACKと一致し、全strict比の速度差を新しい発明効果とはできない。原理の異なるF-O/H/Iの[比較](../masters-security-20261024/continuation-three-20261024.md)も更新する。

[事前計画](plan.md)、[構成・疑似コード・脅威モデル](algorithm.md)、[先行技術・請求項案](novelty-analysis.md)、[実験と限界](results.md)、[日本語草稿](paper-draft.md)。

## 再現

Python3.9、Node24.15.0、`.tools/wabt-1.0.42/bin`、`.tools/binaryen-version_133/bin`、Z3 4.13.3（`.tools/encoding-synthesis-python`）、Wasmtime50.0.1（`.tools/import-alias-quotient-python`）。既存のローカル依存を使用する。新規出力先を指定し、性能測定は他のCPU処理と同時実行しない。

```powershell
python -m pip install --target .tools/encoding-synthesis-python z3-solver==4.13.3.0
python -m pip install --target .tools/import-alias-quotient-python wasmtime==50.0.1
python research/profile-repair/probe.py results/profile-repair/repro
python research/profile-repair/boundary.py results/profile-repair/repro results/profile-repair/repro-boundary
python research/profile-repair/optimize-audit.py results/profile-repair/repro results/profile-repair/repro-optimize
python research/profile-repair/symbolic-audit.py results/profile-repair/repro results/profile-repair/repro-optimize results/profile-repair/repro-symbolic
python research/profile-repair/cross-engine.py results/profile-repair/repro results/profile-repair/repro-cross
python research/profile-repair/bench.py results/profile-repair/repro results/profile-repair/repro-optimize results/profile-repair/repro-performance
python research/profile-repair/internal-bench.py results/profile-repair/repro-performance results/profile-repair/repro-internal-performance
python research/profile-repair/prototype.py INPUT.wasm OUTPUT.wasm
python research/profile-repair/probe.py results/profile-repair/repro-generated --suite generated
python research/profile-repair/optimize-audit.py results/profile-repair/repro-generated results/profile-repair/repro-generated-optimize
python research/profile-repair/symbolic-audit.py results/profile-repair/repro-generated results/profile-repair/repro-generated-optimize results/profile-repair/repro-generated-symbolic
python research/profile-repair/generated-summary.py results/profile-repair/repro-generated results/profile-repair/repro-generated-summary
python research/profile-repair/xnnpack-fetch.py .tools/xnnpack-c754a15
python research/profile-repair/xnnpack-audit.py .tools/xnnpack-c754a15 results/profile-repair/repro-xnnpack
python research/profile-repair/compensate.py results/profile-repair/repro-compensation
python research/profile-repair/compensation-audit.py results/profile-repair/repro-compensation results/profile-repair/repro-compensation-audit
python research/profile-repair/compensation-cross.py results/profile-repair/repro-compensation results/profile-repair/repro-compensation-cross
python research/profile-repair/compensation-bench.py results/profile-repair/repro-compensation results/profile-repair/repro-compensation-performance
```

変換CLIは2個のi32引数から1個のi32を返す純粋runに限定。対応するsplat/swizzle/extract形以外、memory/import/loop/float等を拒否する。全入力について主張するのはこの有限式モデルに対する検査結果であり、任意Wasmの形式同値性証明ではない。出力は全strictの基準観測へ揃えるもので、元の全環境の値をそのまま保存する変換ではない。
