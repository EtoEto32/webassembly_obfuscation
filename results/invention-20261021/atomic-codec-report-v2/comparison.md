# アトミック表現の実測比較

同じcounter入力のO3、競合なし、Wasm内部fetch-add loop。3 fresh process × 9 batch。値はprocess中央値の中央値。min/maxは信頼区間ではない。

|方式|ns / update|min–max ns|binary bytes|
|---|---:|---:|---:|
|plain|7.1317|6.9241–7.1414|312|
|native-neg|7.1216|7.1202–7.1238|351|
|cas-neg|7.5571|7.5528–7.5624|533|
|cas-affine|8.3117|8.2880–8.3739|760|
|native-affine|7.1345|7.1304–7.1477|533|

同一codecのCAS対照からの時間短縮：反転 5.76%、affine 14.16%。
全条件の線形memoryは65536 bytes。RSSはNode全processの最大値であり符号化単体の使用量ではない。
並行試験の実行件数をこの競合なし性能測定の反復数へ加算しない。共有初期化・compile・instantiateを計時外とし、各batch前の公開storeも計時外。
公開storeによる識別時間はWasm compile/instantiateを含む各1回の診断値。人の攻撃開発時間や一般逆コンパイル費用は測っていない。
