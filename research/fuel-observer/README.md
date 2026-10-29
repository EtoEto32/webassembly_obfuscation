# 公開履歴から予約と返金を生成する限定Wasm試作

Fの累積予約を、公開済みのevent値と可変長event列へ拡張した。7自作例中3例でdepthだけの予約より低予算で完了可能になり、1例では公開後の返金を確認した。**新規性は未確立**。公開情報に応じたscheduleと重み付きobserverが強い先行技術であり、別原理の新案数に数えない。

[アルゴリズムと条件付き論証](algorithm.md)、[脅威モデル](threat-model.md)、[先行技術・請求項案](novelty-analysis.md)、[実験と否定的結果](results.md)、[草稿](paper-draft.md)、[初期計画](plan.md)。

追加で、公開Irisデータから生成した4分類器を検査した。150件の合計額は12.1～23.2%減少し、71,232値照合と限定bitvectorモデルでの全入力確認を行った。分類器は自作であり第三者製品ではない。短い処理では会計host費用が支配し高速化はない。

## 再現

リポジトリルートのPowerShellで実行する。出力先は未使用directoryにする。Python3.9、Node24.15.0、WABT1.0.42、Binaryen133、任意の独立runtime確認にWasmtime Python50.0.1を使用する。WABT/Binaryenは`.tools/`をhelperが参照する。

```powershell
python research/fuel-observer/probe.py results/fuel-observer/repro
node research/fuel-observer/guard-audit.cjs results/fuel-observer/repro results/fuel-observer/repro-guard
python research/fuel-observer/merge-audit.py results/fuel-observer/repro-merge
python research/fuel-observer/subset-audit.py results/fuel-observer/repro-subset
python research/fuel-observer/performance.py results/fuel-observer/repro results/fuel-observer/repro-performance
python -m pip install --target .tools/import-alias-quotient-python wasmtime==50.0.1
python research/fuel-observer/cross-engine.py results/fuel-observer/repro results/fuel-observer/repro-cross
python research/fuel-frontier/transform.py results/fuel-observer/repro/hidden-tail/original.wasm results/fuel-observer/repro-negative/dynamic.wasm --mode dynamic --release-values
node research/fuel-observer/negative-controls.cjs results/fuel-observer/repro results/fuel-observer/repro-negative
python research/fuel-observer/classifier.py results/fuel-observer/repro-classifier
python -m pip install --target .tools/encoding-synthesis-python z3-solver==4.13.3.0
python research/fuel-observer/symbolic-audit.py results/fuel-observer/repro-classifier results/fuel-observer/repro-symbolic
python research/fuel-observer/performance.py results/fuel-observer/repro-classifier results/fuel-observer/repro-classifier-performance
python research/fuel-observer/native-boundary.py results/fuel-observer/repro-native-boundary
```

個別binaryの変換:

```powershell
python research/fuel-observer/transform.py input.wasm output.wasm --merge-histories
```

生成される`output.json`はtrustedな解析contract。`guard.cjs`の`bind(bytes,contract)`で同じbinaryを結び、`run(secret,x,budget)`を呼ぶ。`capture:false`でtrace保存を省略できる。hash照合はcontractの署名ではない。guest/contract双方を攻撃者から受け入れる配布用検証器は未実装。

対応は1つの`run(i32,i32)->i32`、`env.mark(i32,i32)->()`、整数演算とvoid ifに限定。memory/global/一般call/loop/例外/threads/Componentは未対応。費用は**入力Wasmの論理opcode**であり、追加O3後も会計単位を変えない。物理時間を隠す方式ではない。

第二版では同じ公開語の経路をmaxで集約する。これは初期計画の後に経路爆発を抑えるため追加した修正であり、実験前から完成していたと扱わない。履歴が多ければ依然として拒否上限に達する。

分類器は保存済み`data/iris.zip`を使い再現時にnetwork不要。[出典と変更](data/README.md)を参照。symbolic checkerはsyntax readerを共有する別の有限実行実装であり、untrusted任意Wasmを受理する汎用証明checkerではない。
