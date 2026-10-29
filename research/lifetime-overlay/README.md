# 生存区間を使う型の重複配置

2026-10-22。**実Wasmの変換・回復・実験を行ったが、主発明には採用しない。** 同時には使われないi32/i64の格納場所を部分的に重ね、固定したアドレスの型を曖昧にする仮説。既知のstack coloringとの距離が小さく、到達定義の追跡で全条件のメモリアクセスをtyped localへ戻せた。

- [事前計画・仮説](plan.md)、[アルゴリズムと意味保存](algorithm.md)、[先行技術との照合](prior-art.md)
- [実測比較](../../results/invention-20261022/lifetime-overlay-report-v1/comparison.md)、[集計JSON](../../results/invention-20261022/lifetime-overlay-report-v1/facts.json)、[草稿追補](paper-note.md)

## 実装と対象

`prototype.py first input.wasm output.wasm` は通常のfirst-fit再利用、`conflict`は作業範囲を増やさない範囲で異なる幅との重複を優先する。Wasmの非整列アクセスが定義済みであることを使う。`.wasm`を実際にvalidate・解析し、アドレスを変える。生成器専用の隠れた対応表を必要とする変換ではない。

1pageのprivate固定memory、1関数 `(i32,i32)->i32`、定数アドレスの全幅i32/i64 load/store、非trap整数演算、resultを返さないifを対象とする。元セルの重複、初期memory値への依存、外部公開memory、動的address、loop/call/grow/atomic/import等は拒否する。一般のC/C++プログラムの適用率は測っていない。

`prototype.py recover protected.wasm recovered.wasm` は公開バイナリだけから回復する。元プログラム、配置表、実行oracleは使わない。O3が作るlocal.tee、値を返すif、i64.load32_u/sも評価順を守って扱う。部分的に異なる書込みからload値を組み立てる一般ケースは未対応。未対応を耐性の証拠に数えない。

## 結果

3合成kernel × plain/first/conflict × raw/O3と各回復版で正36条件、byte単位で異なる23本。独立した36アプリではない。

|検査|結果|
|---|---|
|WABT validation / Node実行|943,104呼出し、不一致0・予期しないtrap0|
|入力|各条件4,352対。diamondだけさらに下位16bitの全65,536通り。同一instanceを連続使用|
|方式既知回復|18/18成功。未対応・crash・timeout各0（v2）|
|誤った配置|3kernelすべてで反例を検出|
|別実行器|WABT interpreter144呼出し一致|
|再生成|正36本のbyte一致|
|適用外拒否|6種類のvalid Wasmを明示拒否|
|評価順・符号拡張の補助検査|4ケース、元/回復の288呼出し一致|

first/conflictの作業領域は全例12byte。型の幅が食い違うbyte数は、branchで4→8、diamondで0→4へ増えた。serialは両方式で同一binaryになった。これは独自の静的proxyであり、NotDec等の逆コンパイラ本体の失敗率ではない。

O3実行の中央値（ns/call）は以下。3 fresh process × 7 batch、16,384回warmup、15ms校正、共通Wasm loopで引数を毎回更新してchecksumを観測。Nodeの`--no-liftoff --no-wasm-lazy-compilation`を使う。252batch中10ms未満0。小差を安定した性能改善と主張しない。

|kernel|元版|first-fit|型衝突優先|回復後O3|
|---|---:|---:|---:|---:|
|serial|7.317|7.575|7.433|4.774|
|branch|2.714|2.760|2.875|2.280|
|diamond|38.521|38.281|38.938|37.730|

型衝突優先/元版は約1.01–1.06。元/配置版の線形memoryは65,536 bytes、回復後O3は0。作業範囲12byteという値をmemory使用量として報告しない。Node全体maxRSSは36,456–36,712 KiB。変換時間は6回の単発測定約38–45msで、主に標準ツール呼出しを含む。

回復は5反復ずつ計90回。型衝突優先の総時間中央値は約38–45ms、到達定義の処理本体は約0.156–1.181ms。O3 diamondではfirst-fitよりcore約10.6%、total約4.5%増えた。増加がないとは言わないが、16の合流を追うだけで済み、65,536経路の列挙は必要なかった。元のsource namesではなく同等なtyped computationsを回復する課題である。

## 結論と限界

格納場所を時間的に重ねること自体は値の可逆符号化とは異なる。しかし、今回の規則は生存区間による既知の格納領域共有で説明でき、型衝突という目的の追加も独立した新規性を確立しない。低い実行費用は確認できたが、適応的な解析に対する大きな追加効果は示せなかった。新発明の数を増やす材料にしない。

初版v1ではO3の9条件がlocal.tee未対応だった。実装を修正したv2では全18条件が回復した。v1の未対応を解析失敗と集計しない。テストは全入力の機械的同値証明ではなく、解析器はこの定数アドレスprofile向け。外部の逆コンパイラ、動的alias、ループ、共有memoryでの一般的な結論ではない。

## 再現

Windows / Python3.9以上 / Node24.15.0、`.tools/wabt-1.0.42/bin`、`.tools/binaryen-version_133/bin`。追加package不要。共有WAT helperは`research/connectivity-elimination/prototype.py`。使用したソースと結果のhashを各結果directoryへ保存する。CPUとV8は性能ログにある。既存outputは上書きしない。rootから未使用名で実行する。

```powershell
python research/lifetime-overlay/run.py results/lifetime-new/main
python research/lifetime-overlay/performance.py results/lifetime-new/main results/lifetime-new/performance
python research/lifetime-overlay/audit.py results/lifetime-new/main results/lifetime-new/performance results/lifetime-new/audit
python research/lifetime-overlay/report.py results/lifetime-new/main results/lifetime-new/performance results/lifetime-new/audit results/lifetime-new/report
```

性能測定中は他の重い実験を同時実行しない。今回は全processがexit0で終了している。
