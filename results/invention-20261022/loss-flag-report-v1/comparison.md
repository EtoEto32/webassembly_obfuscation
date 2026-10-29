# 現memoryを使う修復の実測

性能は別moduleからのimport呼出し、正常出口、seed 221001、O3。各3 fresh process×7 batch。中央値はprocess中央値の中央値。

| profile | plain ns | eager ns | basis ns | current ns | current/basis | current/plain | basis/current bytes | 入口保存値 basis→current |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| swap16 | 2.351 | 8.304 | 4.812 | 4.948 | 1.028 | 2.104 | 815/948 | 3→0 |
| cascade32 | 4.022 | 55.543 | 15.327 | 11.297 | 0.737 | 2.809 | 2639/2788 | 21→0 |
| overlap24 | 11.845 | 59.073 | 27.021 | 19.517 | 0.722 | 1.648 | 3271/3498 | 20→0 |

保存値は8bit情報を持つi32 localの個数であり、実際のstack/register割当byte数ではない。currentにも出口の一時値がある。全modeの線形memoryは64KiB。

| profile | form | basis回復 ms | current回復 ms | total比 | 解析本体比 |
|---|---|---:|---:|---:|---:|
| swap16 | raw | 41.861 | 42.722 | 1.021 | 0.951 |
| swap16 | O3 | 42.710 | 42.178 | 0.988 | 0.980 |
| cascade32 | raw | 53.484 | 51.119 | 0.956 | 0.693 |
| cascade32 | O3 | 53.026 | 48.545 | 0.916 | 0.821 |
| overlap24 | raw | 57.338 | 53.355 | 0.931 | 0.846 |
| overlap24 | O3 | 51.922 | 53.408 | 1.029 | 0.924 |

回復は既存prefix-repair/recover.pyを未変更で使用。各5反復、同一Python process、ランダム順。元sourceやmanifestを回復器へ渡さず、生成物が元binaryと一致するかを回復後に判定。全条件で一致。人間の解析器開発時間は未測定。

正54条件、83,196呼出し、期待trap 42,588。unique positive binaryは42。再生成66本はbyte一致。WABT別実行器360呼出し・1404 memory probe一致。

正常出口の速度改善は副次的な成果。追加の保護効果と独立した新規性を確立した結果ではなく、主発明に採用しない。
