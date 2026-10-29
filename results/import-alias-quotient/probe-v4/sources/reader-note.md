# 既知のWABT roundtrip問題の再遭遇

probe-v2の`2-data_init`, partition `[0,0]`, input `[0,1,4]`で、元実行は98を返したが商変換後はtrapになった。WABT 1.0.42の`wasm2wat --fold-exprs`が`memory.init`のdata indexとmemory indexをtext grammarと逆の順に出力していたため、変換器が誤ったindexを写していた。

これは**新規の不具合発見ではない**。[WABT PR #2838](https://github.com/WebAssembly/wabt/pull/2838)にNishuuzzが2026-08-26に報告している。本文と関連sourceを確認した。両indexが有効範囲なら再validationだけでは意味変更を検出できるとは限らない。今回もtransform後binaryはvalidateを通った。

実装はWABT 1.0.42を固定し、この出力順を読み取ってtext parserが要求するmemory,data順へ戻す。別版は無条件に同じ補正をせず拒否する。`--no-debug-names`も指定し、名前付きmemory operandsを数字と誤解しないようにする。helperやtool全体の修正、upstreamへの投稿は行わない。

probe-v1はBinaryenのbulk feature flag不足で中断、probe-v2は上記不一致で中断した。いずれも成功結果へ数えない。probe-v3以降で修正後の全検査を再実行する。

一次source: [writer](https://raw.githubusercontent.com/WebAssembly/wabt/1.0.42/src/wat-writer.cc)のOnMemoryInitExpr、[parser](https://raw.githubusercontent.com/WebAssembly/wabt/1.0.42/src/wast-parser.cc)のParseMemoryInstrVar。この既知問題の再検出だけでGの新規性は支持されない。
