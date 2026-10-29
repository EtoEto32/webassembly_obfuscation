# 有限回更新と隠れた依存順序：実装・反証

2026-10-23。動くWasm変換と方式既知の解析器を実装した。**有力な特許候補を確立したとはしない。** 可逆座標変換の先行特許に近く、今回の非線形版も0.12–4.75秒で等価なacyclicコードへ回復できた。実行費用も大きい。一般の同種方式が全て弱いという結論ではない。

[実験前の仮説](plan.md)、[生成規則と意味保存](algorithm.md)、[実測表](../../results/invention-20261023/hidden-filtration-report-v1/report.md)、[先行研究との差](prior-art.md)を参照。

## 再現

Python 3.9標準ライブラリ、Node 24.15.0、WABT 1.0.42、Binaryen 133。Wasmツールはrepoの`.tools/`を既定にする（`WASM_TOOLS_ROOT`で変更可）。追加のSMT照合は`.tools/encoding-synthesis-python`のz3-solver 4.13.3.0を使う。新しい出力先を指定する。

```powershell
python research/hidden-filtration/smoke.py results/hfl-replay-build
python research/hidden-filtration/prototype.py results/hfl-replay-build/mix8-plain.wasm results/hfl-single.wasm --mode nonlinear
python research/hidden-filtration/adaptive.py results/hfl-replay-build results/hfl-replay-adaptive
node research/hidden-filtration/check.cjs results/hfl-replay-build
python research/hidden-filtration/performance.py results/hfl-replay-build results/hfl-replay-runtime
```

`smoke.py`は入力3種とraw/O3比較を作る。`run.py`は同じ作成に加えて全18対象へ一次・二次を別々に試す。歴史的main-v1の密な消去手順による時間切れを再調査する場合は`--dense-elimination --seconds 45`を付ける。現行既定は非零係数だけを辿る等価な消去で高速化した版。主判断には現行の`adaptive.py`（一次から開始し、停止時に二次へ進む）を使う。

```powershell
python research/hidden-filtration/run.py results/hfl-replay-main --seconds 45
python research/hidden-filtration/audit.py results/hfl-replay-main results/hfl-replay-audit
python research/hidden-filtration/verify.py results/hfl-replay-main results/hfl-replay-adaptive results/hfl-replay-verify
```

`attack.py INPUT OUTPUT --degree 2 --seconds 45`は配布binaryだけを受け取る。公開係数表から評価器raw/O3を再生成し、binaryが完全一致する場合だけ解析する。source/seed/変換記録は読まない。これは独自family向け解析器であり、NotDecやStackSightを実行した結果ではない。

## 保存した検証

- main-v1：72個の元版・変換版・回復版へ307,656呼出し、不一致0。歴史的解析36回は回復24、一次の辞書停止6、45秒timeout6。timeoutの一部は無混合対照にも生じた。
- adaptive-v1：18/18対象を回復、24解析試行。回復raw/O3の36個へ153,828呼出し、不一致0。主結果はこちら。初期timeoutを保護成功に数えない。
- audit-v1：ランダム初期state1,152モデル、E F=H Eの1,152モデル、scratchを毎回変える4,608Wasm呼出し、descriptor・範囲外領域の保持を確認。偽係数表を持つ改変kernel9個を拒否。
- verify-v1：回復18個のpure BitVecモデルを元版と比較し全てUNSAT。WABT interpreterで24版×4入力=96呼出しを確認。これは一般変換器全体の機械検証ではない。
- runtime-v1：36独立process×7測定=252 batch、10ms未満のbatchなし。コアO3後に共通Wasm反復wrapperを追加、warmup16,384、20msまで反復数を校正。相関したLCG/rotate入力列、Windows/V8単一環境。各process中央値の中央値を報告。Node peak RSSとWasm論理memoryを別記。

開発時に解析器の商空間簡約、hash保存path、失敗時の出力folder生成を修正した。元の失敗ログ・注記を残し、クラッシュや開発ミスを解析耐性として扱っていない。不要な観測を除く`--prune`も試したが、この例では有効でなく、最終回復はpruneなしの高速消去で得た。

3個の手作り小規模関数、1生成seed、pure i32限定という限界がある。WASMixer等との同費用比較、人間の解析時間、実アプリの保護は未検証。新規性を支持しない結果なので規模を増やして成功例を探す前に、生成原理を見直す。
