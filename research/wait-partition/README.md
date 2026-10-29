# Wasm native waitとfield混合の両立条件

2026-10-22。実Wasmの変換器、待機比較の条件、競合反例、差分検証、適応的memory回復、性能測定まで実行した。**意味保存の知見として保持し、主発明には採用しない。** 既存の有限環方式についての限定した構成的新規性候補は別に保持する。

詳細：[事前仮説](plan.md)、[アルゴリズムと攻撃モデル](algorithm.md)、[先行資料](prior-art.md)、[日本語草稿追補](paper-note.md)。原子的アクセスを64bit単位にまとめるだけではwait32の比較を保存できない。観測するfield集合ごとに許される混合を選ぶ試作である。

## 実測

主結果は [wait-partition-v1](../../results/invention-20261022/wait-partition-v1/manifest.json)、[独立監査](../../results/invention-20261022/wait-partition-audit-v1/audit.json)。4種類の待機footprint × 元版/恒等CAS版/自動混合版 × raw/O3 = 24条件。4種類は同じ小さなfixtureの設定であり、独立した実アプリ4件ではない。

- 50,088呼出し、期待trap13,680で戻り値／trap一致。792回の全64KiBメモリ照合も一致。有限テストで全入力同値性を証明したとはしない。
- 4workerで二fieldを競合更新。24条件、393,216 atomic add、旧値の一意性と最終値一致。待機・通知48条件で正しいアドレスが起こし、別のアドレスは起こさなかった。
- snapshot-based wait翻訳が誤る履歴を5回再現。元版と適合版の計10履歴はnot-equalで終了。計15件は主正当性の呼出し件数に足していない。
- 24binaryをbyte一致で再生成。WABT interpreterで逐次288呼出し（うちtrap72）、unsupported入力6件を拒否。未知wait32アドレスでは両fieldを観測する保守的選択へ落ちる。benchの別検証は1,008呼出し一致。
- 全24条件のcodecを、公開binaryと公開store API／物理memoryから4回のstoreで同定。同定したdecoderで全memoryを照合。元ソースとmanifestのcodecは攻撃者へ渡さない。型推定や一般閉鎖APIの解析結果ではない。

O3、単一threadの加算loop。値は3独立Node processの中央値で、それぞれ9batchを測定した。

| wait footprint | 元版 ns/update | 恒等CAS | 自動混合 | 自動/元版 |
|---|---:|---:|---:|---:|
| low | 7.128 | 8.643 | 9.460 | 1.327 |
| high | 7.124 | 8.697 | 9.601 | 1.348 |
| both | 7.133 | 8.649 | 8.659 | 1.214 |
| wideのみ | 6.954 | 8.620 | 10.242 | 1.473 |

自動混合の両32bit待機版は恒等表現で、保護効果を付加していない。非自明な3設定は恒等CAS比約9～19%の追加時間。O3の自動版は1,688～2,136bytes、元版448～505bytes。実験の全版のlinear memoryは64KiB、追加tableなし。whole-process maxRSSは39,564～40,672KiB。変換は約39.9～42.8ms（各1測定、WABT処理込み）。競合時のthroughputや公平性は測っていない。

性能は合計36process/324batch、10ms未満のbatchなし。warmup32,768更新、12msを目安に反復数を適応設定。CPU affinityや周波数は制御していない。解析は各O3 binaryを7回同定し、読出し・compile/instantiate・観測を含む中央値0.165～0.224ms。毎回4storeで、問い合わせ数の増加はない。同じNode内の反復なのでエンジンcacheの影響があり、数十µsの差を保護効果とは判定しない。

## 再現

Windows 10.0.26100、Python 3.9.0、Node 24.15.0/V8 13.6、Intel Core i9-11900K。リポジトリの `.tools/wabt-1.0.42/bin` と `.tools/binaryen-version_133/bin` を使用。追加パッケージ不要。ツール出力は新規ディレクトリを指定し、過去の結果を上書きしない。

```powershell
python -X utf8 research/wait-partition/run.py results/wait-main-new
python -X utf8 research/wait-partition/audit.py results/wait-main-new results/wait-audit-new
python -X utf8 research/wait-partition/report.py results/wait-main-new results/wait-audit-new results/wait-report-new
python -X utf8 research/wait-partition/prototype.py input.wasm output.wasm --mode auto
```

`prototype.py` は実 `.wasm` を検証して読み、命令を書き換え、標準WABTで再出力する。対象外機能とホスト側の初期符号化契約は[algorithm.md](algorithm.md)参照。named exportやimport形状、限定APIの存在は評価の前提であり、汎用商用バイナリ対応ではない。`common.cjs` の `identify(file)` はcodec同定の再現用入口。

最適化後も混合は残ったが、安い逆変換を取り除けなかった。次案ではCAS幅や回転量の変更だけを新原理に数えず、意味保存の対応範囲と解析費用の増分を別々に評価する。
