# 並行演算グラフ：共有memoryとatomicによる早期反証試験

**主発明には不採用。** 動作するWasm変換器、実worker実行、方式既知の回復器を作った。主101,376呼出し、追加72,912呼出し、WABT240呼出しで不一致0だが、24/24の主変換を通常Wasmへ回復した。解析時間は逐次VMとほぼ同じで、並行化の増分効果を確認できなかった。特許目標の達成や新規性の確立を意味しない。

- [事前計画と3方向の比較](plan.md)
- [アルゴリズム・意味保存条件・回復手順](algorithm.md)
- [先行論文・特許との照合](prior-art.md)
- [実測・アブレーション・採否](analysis.md)
- [論文形式の日本語追補](paper-note.md)

## 環境と範囲

Windows、Python 3.9.0（標準ライブラリ）、Node 24.15.0/V8 13.6、WABT 1.0.42、Binaryen 133で実行した。CPU等は主結果のenvironment.jsonにある。リポジトリ内`.tools/wabt-1.0.42/bin`、`.tools/binaryen-version_133/bin`を利用する。共通tool関数は`WASM_TOOLS_ROOT`で`.tools`の場所を変更できる。新しいサービス・課金・外部公開は不要。

入力は実`.wasm`。単一関数・単一export、1〜16 i32引数・1 i32結果、純粋な全域演算・select、4096命令/localまで、DAG 1024nodeまで。memory/import/loop/除算等は拒否する。出力は共有1pageをimportし、`init`、`work`、`result`をexportする。ホストadapterが全worker完了を待つ必要があり、元のexportを呼ぶだけの置換ではない。workerの生成・joinはホストの責務。

攻撃者は方式、全binary、hostを知り、memory観測・単一worker実行・通常Wasmへの書換えが可能。保護課題は演算依存と同じ関数を計算する簡潔な実装の回復。秘密seed、実行順の秘密性、全interleaving探索の強制を仮定しない。回復器開発の人的費用は未計測。

## 変換と回復

リポジトリrootのPowerShellから実行する。outputは存在しないパスを指定する。

```powershell
python research/concurrent-frontier/prototype.py input.wasm output.wasm --seed 20261019
python research/concurrent-frontier/prototype.py input.wasm serial.wasm --serial-nonatomic
python research/concurrent-frontier/recover.py output.wasm recovered.wasm
```

`harness.cjs`の`pool(file, workers)`は既存poolへ`run(inputs)`するadapter。`workers`は1/2/4を検査した。non-atomic版は1thread専用。各workerのinstantiate完了を待ってからinitする。呼出しの重複・worker離脱・ホストmemory改変を許容しない。`close()`で終了する。

## 再現

結果ディレクトリは既存内容を上書きしない。下のパスが存在する場合は別名へ変更する。

```powershell
python research/concurrent-frontier/run.py results/concurrent-reproduced
python research/concurrent-frontier/verify.py results/concurrent-reproduced results/concurrent-verify-reproduced
python research/concurrent-frontier/model.py results/concurrent-verify-reproduced/sc-model.json
python research/concurrent-frontier/measure.py results/concurrent-reproduced results/concurrent-performance-reproduced
```

主試験は36target、24回復を生成し、Nodeの通常実行とworkerを検査する。verifyは個別命令・境界条件・誤変換・非対応例・WABT別engineを検査する。measureは108 fresh processを逐次起動する。他の重い処理を止めて実行する。正常終了時にそれぞれsummary.jsonがある。

保存済み主結果は`results/invention-20261019/concurrent-frontier-v2/`、追加は`concurrent-frontier-verify-v2/`、性能は`concurrent-frontier-performance-v2/`、最終監査は`concurrent-frontier-final-audit-v1/`。main v1→v2で36targetと24回復のbyte一致を確認する。probe、修正前のharness、測定準備の失敗、誤った循環fixtureも削除せず理由を添えた。`report.py`/`audit.py`はこの保存済み結果の集計用で、再現先を自由指定するCLIではない。

ここから正当性・新規性・解析費用を別々に評価できる。難読化だから解除不能である必要はないが、本案では並行化による解析費用の追加優位性が観測されず、実行費用が増えた。
