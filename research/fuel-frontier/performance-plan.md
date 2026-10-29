# 性能実験の固定条件

probe-v2の7fixtureを対象に2026-10-24に固定。新しいアルゴリズムは追加しない。

- original/whole/segment/frontier/dynamic/late/manualの7方式、それぞれ4fresh process、順序seed2026102406。
- 各fixture 2,000 call warmup、5,000 call×9反復。secretは0–3を循環し、payloadも変える。十分な予算で同じ戻り値のchecksumを確認。
- 全方式のWasmを-O3。手書き対照は元Wasmの-O3にhost側の独立oracle由来scheduleを使う。
- chargeの整数・非負検査、残高更新を含む。compile/instantiateをsteady-state call時間に含めず別記。公開markerをrolling checksumに反映し、trace配列の保存は除く。Node processのmaxRSS、heap、external、arrayBuffersを記録する。
- 全process生データ、process中央値の中央値/IQR、paired比を保存する。費用不足でthrowする速度はこの実験に含めない。
- JS/Wasm境界回数が大きく異なるためdynamicとの速度差だけで発明価値を示さない。whole/manualとの比較を重視する。
