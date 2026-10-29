# 符号化領域の範囲保証によるSIMD表引きの軽量化

2026-10-21。ユーザーの指示に従い、既存方式の実行負荷という課題を改善する方向を実装・測定した。難読化の基本構成を新発明と主張しない。**小規模な符号化計算で実行時間の改善を観測したが、特許の核となる独自性は未確立。主目標は継続中。**

## 課題・構成・効果

従来試作[isotope-swizzle](../isotope-swizzle/README.md)の符号化表方式は表引き処理が重かった。今回は表や符号化を変えず、byteごとの添字が0..15に収まることをコードから追跡する。証明できた `i8x16.swizzle` のみ `i8x16.relaxed_swizzle` へ置換する。この範囲では両命令の結果は一致する。範囲不明の場合は元命令を残す。

以前のrelaxed-carrierは実装依存の値をmaskとして利用した。今回の置換は、実装依存の結果が生じない入力範囲に限定する点が異なる。既存のSIMD表方式をもう一度新しい難読化原理として数えたものではない。

## 実装と意味保存の範囲

`prototype.py input.wasm output.wasm` は実バイナリをWABTで検証・読み取り、単一の純粋な直線関数を処理する。対応型はi32/v128、対応命令はソース内ALLOWEDに固定。memory、import、分岐、loop、call、float等は対象外。これは任意Wasm用の汎用パスではない。

各localに「各byteが0..15と保証される」情報を保持。定数、mask AND、範囲内同士のOR/XOR/bitselect、表の出力範囲、順序通りの代入を伝播する。加減算等で保証を失う場合はunknownへ落とす。scalar i32に対しては0..15保証のみを作り、extractから安易に引き継がない。初期localはWasmの零初期化を使う。局所的な規則の帰納的説明は意味保存の根拠だが、変換器全体の機械検証済み証明ではない。

逆モード `--reverse` も同じ範囲保証を検査してstrict命令へ戻す。これは解析側が使える軽い正規化でもある。今回、12本全てが元のO3バイナリとbyte一致した。したがって、この変更による解析耐性の増加は主張しない。元の符号化方式の耐性が一般に十分であるという認定でもない。

## 実験結果

- add/xor/mixedの3計算×decode/tableの2表現×符号化seed2＝12条件。独立な計算は3つ。
- 各7,872入力。元・変換・再O3・復元の4本、計377,856呼出しで不一致0。今回の照合oracleは従来のO3バイナリであり、新たな独立意味証明ではない。
- 負の範囲対照：添字全byte域0..255の無制約版は置換0、mask版は置換1。各256入力、合計1,024呼出し一致。仕様の二つの解釈をモデル化し、16..127では差が出る反例を保存。Nodeで見えた一種類の挙動だけで安全性を判断していない。
- JS呼出し込み108 fresh process：元/変換/再O3×12×3、50,000 warmup、9×50,000。変換/元中央値は0.882–1.088。
- 呼出し境界の影響を減らす追加測定120 fresh process：元/変換×12×5、Wasm内100,000 warmup、9×200,000反復。wrapper追加後に再O3しない。中央値比0.826–0.990。seed291021で順序を混ぜ、各条件の全checksumが一致。

[process間の範囲を含む比較表](../../results/invention-20261021/encoding-lowering-report-v1/comparison.md)。短いdecodeの一部とmixed-tableではprocess中央値の範囲も分離した。一部の小幅改善は範囲が重なり、普遍的な高速化とはいえない。CPU/V8一組の小規模合成例で、ARM・別エンジン・実アプリは未測定。Wasm反復には入力更新・loop費用も含む。

追加linear memoryと追加v128 localは0。命令encodingの差でbinaryは6–68byte増えた。変換時間はmanifestのms（外部reader/compiler/validator込み、各1回）を保存。RSSと生の反復時間もruntime.jsonに保存。解析処理の所要時間は既存復元器の値をmanifestに保存したが、追加保護の主張や人間の解析時間への換算には使わない。

## 先行性と特許候補としての位置付け

1. [Wasm公式Relaxed SIMD概要](https://github.com/WebAssembly/relaxed-simd/blob/main/proposals/relaxed-simd/Overview.md)のswizzle疑似コードを読んだ。0..15での一致は公開仕様そのもの。範囲解析も一般的なコンパイラ技術であり、命令の単純置換を独創的と断言できない。
2. [V8の固定commitのx64 selector](https://chromium.googlesource.com/v8/v8.git/+/e9775165b6fe77c4a94cf7802865ed40996197aa/src/compiler/backend/x64/instruction-selector-x64.cc)を一次検索抜粋で確認。定数添字が範囲内または上位bit設定済みなら補正命令を省く処理が既にある。今回のNodeの生成機械語を調べたものではなく、速度差の原因を確定したとはしない。
3. Luoqi Chen, Yufeng Tang, Liangju Zhao, Zheng Gong, **SIMD Optimizations of White-Box Block Cipher Implementations with the Self-equivalence Framework**, Inscrypt2024改訂論文集2025, LNCS15543 pp129–149, [DOI:10.1007/978-981-96-4731-6_7](https://link.springer.com/chapter/10.1007/978-981-96-4731-6_7)。出版社Abstract・書誌、著者[コードREADME](https://github.com/scnucrypto/SIMD-White-Box-Block-Cipher)を確認。affine層の小表化とSIMD並列表参照等が既知。本文は購読プレビューで未読。報告高速化率を今回の測定と同条件の比較に使わない。

今回の改善は役に立つ実装部品として残す。一方、現状の構成は公開仕様と通常の範囲解析から直接導け、独立した特許の核としては根拠が弱い。改善があったことを否定せず、次は「符号化の生成段階で軽量命令の適用範囲を拡げる具体的な割当規則」を検査する余地がある。ただし、その規則は未設計・未実証であり本成果に算入しない。

## 再現

```powershell
python research/encoding-lowering/run.py results/encoding-lowering-replay
python research/encoding-lowering/controls.py results/encoding-lowering-controls-replay
python research/encoding-lowering/internal.py results/encoding-lowering-replay results/encoding-lowering-internal-replay
python research/encoding-lowering/report.py results/encoding-lowering-replay results/encoding-lowering-internal-replay results/encoding-lowering-report-replay
```

Python3.9、Node24.15.0、WABT1.0.42、Binaryen133。入力は `results/invention-20261019/isotope-swizzle-v2`、基礎コードは `research/isotope-swizzle` と `research/connectivity-elimination`。入力ファイル名・hash・変換の証拠は[manifest](../../results/invention-20261021/encoding-lowering-v1/manifest.json)、[inverse照合](../../results/invention-20261021/encoding-lowering-report-v1/identity.json)、[コードhashとプロトコル](../../results/invention-20261021/encoding-lowering-report-v1/protocol.json)を参照。各出力先は未存在のディレクトリを指定する。
