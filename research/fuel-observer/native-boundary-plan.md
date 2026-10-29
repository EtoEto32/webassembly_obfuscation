# ネイティブfuel接続の境界反証計画

2026-10-24。7例でoffset 0/4が通過したことを一般化しないための追加検査。F-Oの会計原理の拡張ではなく、既存bridgeの反証ゲート。

公開marker間の純計算を極小にすると、挿入した開始marker等のnative費用がsource単位の予約を超える可能性がある。各ケースは現transformerが受理する有限・pure i32 subsetで作る。秘密値は0/1、公開marker列は同じ又は秘密を明示公開する二種類。marker数0/1/2/4/8/16/32、秘密依存の追加xor数0/1/4/16、raw/O3を測る。

最初に豊富なnative fuelで結果・イベント・callback時のnative残量を記録する。次にsource contractと同じ予約差分をnative fuelへ反映し、offset 0/4の全予算0..whole+1について独立の経路oracleから得た公開台帳と照合する。不一致、native trap、予算停止、値不一致を分ける。大きい負荷や第三者サービスを対象にしない。

失敗が出た場合にoffsetを都合よく増やして成功扱いにしない。まず失敗した実binary・台帳・runtime版を保存し、source論理費用モデルの結果とnative enforcementへの一般的接続を明確に分ける。これはWasm runtimeの脆弱性探索ではなく、自作会計bridgeの成立条件の検査である。
