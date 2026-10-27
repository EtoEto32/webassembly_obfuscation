# 解除器の形式依存と、範囲証明による適用範囲の拡張

2026-10-23。**新しい難読化の発明ではなく、研究評価の適用範囲を実測した追試。** 可変二表の解除器は、動作が同じ84条件のうち60条件を形式未対応として拒否した。範囲を証明した式を受理する拡張では84条件すべてを等価Wasmへ戻せた。単なる未対応を保護効果として扱わないという評価条件を、実装と反例で具体化した。

- [事前計画](plan.md)、[解除規則と限界](analysis.md)、[調査追補](literature-note.md)
- [旧解除器の結果](../../results/invention-20261023/profile-boundary-v1/attacks.json)、[正当性](../../results/invention-20261023/profile-boundary-v1/checks.json)
- [拡張解除器の結果](../../results/invention-20261023/profile-boundary-adapt-v1/attacks.json)、[拒否対照](../../results/invention-20261023/profile-boundary-adapt-v1/rejections.json)
- [追加式の結果](../../results/invention-20261023/profile-boundary-holdout-v1/outcomes.json)、[別実行器・再生成・hash監査](../../results/invention-20261023/profile-boundary-audit-v1/audit.json)

| 同値変更（各6人工グラフ） | 旧raw成功 | 旧O3成功 | 拡張raw/O3成功 |
|---|---:|---:|---:|
| 未変更 | 6/6 | 6/6 | 12/12 |
| local番号変更 | 0/6 | 6/6 | 12/12 |
| 0の加算 | 0/6 | 6/6 | 12/12 |
| 入力guard順序変更 | 0/6 | 0/6 | 12/12 |
| partnerをXORで選択 | 0/6 | 0/6 | 12/12 |
| partnerを積和で選択 | 0/6 | 0/6 | 12/12 |
| partnerをselectで選択 | 0/6 | 0/6 | 12/12 |

主108実行条件227,340呼出し、拡張回復84条件176,820呼出し、追加60条件126,300呼出しで、値・trapの不一致0。各条件2,105入力で、同じ6fixtureと入力系列を使う。回復版には同一byte列が多数あり、独立したプログラム252個とは数えない。private memoryの物理一致は対象外で、trap後の連続呼出しも検査した。全入力についての実装の数学的同値証明ではない。

別WABT interpreterでは主84と拡張回復84を各6回、計1,008呼出し・336trapで照合した。主84本の再生成はbyte一致。主・拡張の411個のhashを監査した。追加式のNode結果はこのWABT監査の後に作成したもので、追加式を別VMでも確認済みとは主張しない。

拡張後に用意したshift/sub/orを含む2種×6fixture×raw/O3の24条件も回復した。一方、正しい`w=u`版12条件は最適化で周囲の命令が変化し、なお形式未対応だった。範囲を広げ過ぎたmask版12条件はSMTで反例があるため拒否した。主の誤store順・範囲逸脱12条件と追加の広いmask12条件では、動的検査も全条件で反例を検出した。副作用式・guard欠落・memory公開の3対照も拡張解除器は拒否した。

拡張84条件の読取・最適化・範囲検査・出力込み時間は151.5–191.5ms、中央値157.9ms。範囲検査は0.691–3.755ms。各条件1回の診断時間で、反復性能比較ではない。CPU/RSSの新しい保護性能比較は行っていない。

## 再現

Python3.9、Node24.15.0、WABT1.0.42、Binaryen133、`.tools/encoding-synthesis-python`のZ3 4.13.3。repository rootから実行し、出力先は未作成のdirectoryを指定する。既存のmutable-factor結果がなければ先に`python research/mutable-factor/run.py NEW_FACTOR`を実行する。

```powershell
python research/profile-boundary/run.py results/invention-20261023/mutable-factor-main-v1 results/new-boundary/main
python research/profile-boundary/adapt.py results/new-boundary/main results/new-boundary/adapt
python research/profile-boundary/audit.py results/new-boundary/main results/new-boundary/adapt results/new-boundary/audit
python research/profile-boundary/holdout.py results/new-boundary/main results/new-boundary/holdout
python research/profile-boundary/report.py results/new-boundary/main results/new-boundary/adapt results/new-boundary/audit results/new-boundary/holdout results/new-boundary/report
python research/profile-boundary/recover.py INPUT.wasm OUTPUT.wasm
```

旧解除器や既存の主実験を改変していない。これは形式の小変更で研究上の成功を誤認しないための評価改善であり、新しい有力な特許候補を確立したとは扱わない。
