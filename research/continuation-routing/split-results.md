# 固定切断による継続分割：実装と反証

2026-10-21。前回は継続の実行可能性を確認したためprogress。今回は限定的だが実wasm入力からの変換器と、対象wasmのみを読む復元器を実装した。

## 検査した規則

単一引数のi32命令列を非空のA,B,Cへ分ける。workerは `C(suspend(A(x)))`、driverは捕捉した継続を `B(payload)` でresumeする。戻り値は `C(B(A(x)))`。i32のtotalな加減算・乗算・bit演算のみで、メモリ・外部呼出し・例外・除算は扱わない。任意のWasmや入力依存の動的切断は未実装。CLIは実験driverであり、汎用製品ではない。

これは前回の未確定な「対にして再分割する規則」の固定切断部分を実装して最も簡単な反証を試したもの。高度な計画規則を完成させたとはしない。

## 実験

`split.py`：長さ8/32/128、各3命令列、各3切断位置、計27変換。9個の独立した元プログラム。各命令を加算・減算・xor・奇数乗算に制限し、全体をi32上の置換にした。乱数and/orの連続で定数へ潰れる弱いテストを避けた。元のv1はand/orも含み定数化の恐れがあるので、主結果に採用しない。

各105入力（5境界値＋100固定seed乱数）、source/target/recoveredの3種類をBinaryen wasm-shellで実行。主結果v2の8,505呼出しは全一致し、27件で復元式が元の式と構文的に一致。復元器は元の式・切断位置・seedを入力として受け取らない。正解との照合は実験driverだけで行う。

`optimized.py`：27変換にBinaryen -O3を適用。各105入力のtarget/recovered、計5,670呼出しが全一致。復元器が最初に失敗した理由は、最適化がhandler生成blockをresumeの引数へ移動し、子孫のonを検索していた実装が外側resumeまでhandlerありと誤認したため。直下のonだけを調べるよう修正し、Binaryenのtuple展開形を認識して全27件を復元した。最適化後の構文一致は要求せず、独立Python評価値との一致を検査した。

復元はworker中のsuspendをhandlerの計算で置換し、そのpayloadへsuspend引数を代入する。この実験族では命令列を展開するだけで、経路探索は不要。最適化後の復元器は観測したtuple展開形に限定したプロトタイプであり、任意の敵対的Wasmで健全な一般解析器ではない。形状検査だけで未テストの入力全般の正しさは主張しない。

主結果v2のサイズ比target/sourceは1.078–1.780倍。復元所要時間は24.89–35.30ms、各1回、disassembler・assemblerプロセス起動込み。これは解析本体の反復性能測定ではなく参考値。従来CPSとの同費用比較、JIT実行速度、RSS、適応解析器の開発時間は未測定。この条件から解析費用の優位を主張できない。

## 判断

固定切断は継続機能の単純利用であり、構造回復は局所的な記号代入で済む。全件復元成功だけを理由に棄却するのではなく、独自の規則・追加効果が未確認であるため、**特許の主候補として採用しない**。未知の動的切断方式まで無効と証明したわけではない。今後検査するなら、切断・live値割当計画が既存CPSと異なる機構と効果を持つ必要がある。

## 再現と証拠

```powershell
python research/continuation-routing/split.py results/invention-20261021/continuation-split-replay
python research/continuation-routing/optimized.py results/invention-20261021/continuation-split-replay results/invention-20261021/continuation-optimized-replay
```

- [raw結果](../../results/invention-20261021/continuation-split-v2/records.json)、[全コマンド・stdout/stderr](../../results/invention-20261021/continuation-split-v2/commands.json)
- [O3結果](../../results/invention-20261021/continuation-optimized-v2/records.json)、[全コマンド・stdout/stderr](../../results/invention-20261021/continuation-optimized-v2/commands.json)
- `continuation-optimized-v1` は最初の1件の実行後にStopIterationで停止した中間成果。成功集計に含めない。端末tracebackは会話にあり、完全な失敗ログファイルは当時保存していない。

主結果は同一Binaryen系のassembler/interpreterによる有限検査。独立実装での意味保存検証、数学的全入力証明、特許成立の確認ではない。
