# 到達性の実測と仮説への影響

2026-10-27。生データは `results/gc-execution-gap/probe-v1`、再集計・監査は `analysis-v1`。

## 標準設定による比較

4型shape×64seed×2設定の512試行から502binaryを生成した（各設定251成功、5生成失敗）。default側251binaryは以前のRのstock出力とbyte一致し、5失敗理由も一致した。crateへの追加パッチは使っていない。変えたのは公開設定 `disallow_traps` のみで、seedが同じでも二つの設定が生成するコードは同一ではない。

各binaryへnullを入力した結果:

|無計数の結果|default|no-traps|
|---|---:|---:|
|正常終了|78|119|
|fuel終了|90|97|
|trap|83|35|
|対象get/set命令を含むmodule|35/251|0/251|
|対象get/setの静的site数|41|0|
|対象アクセスを一度以上完了したmodule|1/251|0/251|

no-trapsで正常終了は増えたが、array.get/setおよびstruct.get等を生成対象から外す実装により、今回の対象アクセスは消えた。これをテスト効果の改善とは言えない。no-trapsにもarray.lenのnull trapが残った。あくまでこの設定・版・shapeでの観測であり、wasm-smith全体の品質や新規runtime bugの主張ではない。

## 入力構築で解決できる範囲

|shape|各設定の生成数|default対象site数|nullで成功したmodule|深さ1で成功したmodule|
|---|---:|---:|---:|---:|
|nonnull自己参照array|62|7|0|0|
|nullable自己参照array|64|6|1|2|
|i32 array|64|6|0|0|
|nonnull自己参照struct|61|22|0|対象外|

最後のstruct型は空storeから構築できない負の対照である。その22siteを「適切な入力生成なら成功したはずの未到達箇所」と数えない。

構築可能な3 array shape、計190moduleについて、深さ1入力の19対象siteを分けると次のようになった。

|siteの結果|数|
|---|---:|
|その関数に一度も入っていない|7|
|関数には入ったがsiteに未到達|10|
|siteに到達したが完了していない|0|
|一度以上完了|2|

19は190本内の静的siteの数。反復回数ではない。改善したmoduleはnullable-arrayのseed 50だけで、Rで観測した結果と整合する。元の入力をさらに深くしたり、aliasを複雑にしたりするだけで、未呼出しの関数やそれ以前の停止が解消されるという証拠は得られなかった。

全4shapeのnull入力では、41siteのうち関数未到達19、関数内未到達18、到達後未完了3、完了1だった。構築不能structを含む集計と、構築可能arrayの集計を区別する。

## 計数器が与えた影響

null/深さ1の計882入力条件をfresh instanceで実行し、同じ100,000fuelの下で計数あり/なしを比較した。6条件では、無計数版のstack exhaustionが計数版ではfuel exhaustionへ変わった。nullable-array seed17/no-traps、seed26/default、scalar-array seed53/no-trapsの各2入力である。正常終了の戻り値の相違はなかった。

計数の追加が実行資源を変える以上、終了理由まで完全な意味保存を証明したと扱わない。site計数は各計数版の観測である。fuel増量で全入力同値と証明されたわけでもない。

10校正入力はarray.len/getの成功・null trap、未実行branch、未呼出し関数、packed struct getを含む。計数あり/なしのWasmtime20呼出しに加え、Node20、SpiderMonkey20で期待結果とcounterが一致した。一般的な計数変換器全体の証明ではない。

## 監査と限界

1,597file hash、1,004binaryの再計数/再生成、882分類の再計算は不一致0。生成・検証・実行の異常は別記録。初回資料取得のDNS失敗はpriors-v1、回復後の5一次資料はpriors-v2。既存paper/main.texのhashは今回開始時から不変。

4つの小型shape、64seed、Wasmtimeを主実行環境とした限定調査である。大規模実アプリ、全fuzzer設定、各エンジン内部の分岐coverage、独立seed反復の信頼区間、欠陥発見率は未測定。計数版の実行msは診断値であり、この実験からfuzzerの速度優位を主張しない。

## 研究判断

入力構築だけでは到達性の主な不足を解消できないという根拠が増えた。標準のno-traps設定でも対象命令が消える。一方、Binaryenには境界チェック付き生成・非null値生成・既存参照の再利用が既にあるため、これらを足すだけの方式を別原理の新案としない。今回の成果は、R/Sを主テーマへ昇格させない理由の具体化と、次の課題選定に使える実測・計数基盤である。
