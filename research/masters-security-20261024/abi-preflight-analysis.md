# 展開前検査の結果：主発明要素には不採用

2026-10-24。Aのhost側検査が値のliftより後になるという境界を調べた補助試験。**事前上限は有用だが、追加したmemoizationの新規性・費用優位は確認できなかった。**

730byteの実Componentに`list<list<list<u8>>>`を渡す。Jcoが生成した既知のimport trampolineへ、memoryからの展開より前に検査を挿入した。汎用のbinary変換器、WIT全型への実装、Wasmtimeの改修ではない。固定位置が見つからなければ変換を拒否する。

費用モデルはleaf byte数＋非leaf list要素数＋全list数。単位8192の予算とし、実際のRSSやWasmtime fuelとは区別する。memoのkeyは(type depth, pointer, length)。同じ部分構造を再計算しないが、その費用を各出現で加算する。上限+1で飽和させる。memoryが変わらない一呼出し中だけcacheを有効にする。

[最新の正当性試験](../../results/masters-security-20261024/abi-preflight-v4/results.json)は45実Component呼出し、内容checksumと受付が一致。3方式それぞれ15条件で、予算内10・予算超過5。前検査の2方式は超過5条件でhost本体を呼ばず、後検査は呼出し後に拒否した。単体で3不正layoutを拒否し、呼出し間のmetadata変更に対して再検査することを確認した。検査とliftの間の並行変更を防ぐ実装ではない。

[性能の最終表](../../results/masters-security-20261024/abi-performance-v2/report.md)は15 fresh process、各20 warmup・9×50呼出し。非memoの前検査を対照としたmemo版の時間比中央値は、tiny1.025、共有受理1.026、共有拒否1.101、非共有拒否1.799、大きい共有拒否1.251、空leaf0.970。6例中5例で遅い。後検査より早く拒否できる結果は、既存のfuel・走査上限の考え方でも得られるため、新しい安全原理とはしない。

初回性能版は非memo側にも不要なkey文字列生成が残っていた。これを取り除いたv2を採否に使う。v1は記録として残し、都合の良い測定だけを採用しない。正当性v1はimport objectの形を誤った試験実装の失敗で、セキュリティ拒否へ数えない。v2は長さ検査、v3以降はchecksumも検査し、v4は非memo実装を改善した同じ45条件の再試験である。

残る限界は、標準的なfuel方式との同じruntime比較、hostの実割当量に対応する費用、resource・variant・stringへの対応、共有memoryの排他、第三者application。これらが未実装の段階で主請求項を広げない。[近接する先行技術](prior-art-followup.md)を参照。
