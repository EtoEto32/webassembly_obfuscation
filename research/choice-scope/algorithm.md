# 実行結果の関係を保つ限定oracle

入力は検証済みの実.wasm、具体的なi32引数列、実行結果のi32列。単一run・直線式・純粋な数値命令を対象に、出力列がモデルの許容関係に属するかを検査する。数値一致ではなく存在量化による所属検査であり、既存の記号実行・SMTを用いる。

1. WABTで検証・folded WATへ復号し、未対応命令と宣言を拒否する。
2. concrete引数をbitvectorにする。localへの代入は式を保存し、local.getは同じ式を再利用する。
3. relaxed swizzleにはrun内共通のBooleanを置く。
4. f32.addの結果には評価ごとに新しいbitvectorを置く。NaNなら入力NaNのcanonical性に応じた許容payload/signを制約する。非NaNならZ3のRNE演算とbit列を一致させる。reinterpret・abs・neg・copyはbit列をそのまま操作し、新たなNaN選択を作らない。
5. lane選択には明示したモデルの共通parameterを置く。defaultは[model-revision.md](model-revision.md)のbyte-compatible解釈であり、一般仕様への完全適合を保証しない。
6. 全出力を同時に実観測へ等置し、許容する選択変数が存在するかを問う。

```
(F, constraints, profiles) = evaluate_symbolically(binary, concrete_inputs)
answer = SMT(constraints AND all(F[i] == observed[i]))
SAT     -> このモデルで説明可能
UNSAT   -> このモデルでは説明不能。仕様・モデルの不備も調べる
unknown -> 未解決（timeoutなどの理由を保存）
```

点ごとの対照は各出力の等式を別queryで解くため、観測間の関係を失う。independent-site対照は命令間の共通profileを外すが、生成済みlocal値の共有は残す。強い対照のenumeratedは共通profileを有限列挙し、各組で同じNaN制約と全出力を解く。完全なsolverを仮定すればjointと同じ許容集合になる。これは別の新合成理論ではない。

O3後の実行結果も、元binaryから作った関係へ照合する。許容結果の一部だけを返す最適化は拒否しない。例えば二回の独立したNaN生成を一回に共通化しても、元の許容集合の部分集合に入るなら、この所属検査では問題としない。全入力・全実行の意味精緻化証明ではなく、観測した入力・出力だけの検査である。

## 範囲と信頼基盤

256KiB以下、最大64 i32結果、512 locals、4,096式。i32/f32/v128 locals、整数論理・一部演算、f32.add/reinterpret/abs/neg、vector定数/splat/extract、swizzle、8/32/64幅lane選択を扱う。memory、import、global、loop、一般call、trapを起こす命令、i16 relaxed lane選択、他のrelaxed命令は未対応。WABT、簡易folded-WAT parser、Python、Z3を信頼する。検証済みとは数学的証明済みを意味しない。異なるrunやprocess間の共通profileを検査しない。

制約式のサイズやsolver時間に有利な漸近的上界は示していない。有限profileの列挙を避けるだけで常に高速になるとの主張もない。f32式の連鎖、branch/path、memory等へ広げた場合の実用性能は未評価。
