# 同符号群の係数混合：実測結果

主結果はmain v2 / runtime v1 / audit v1。3合成関数、各4 channel、1 encoding seed。raw/O3や変換条件を独立ベンチマークと数えない。

| fixture | plain ns | permutation ns | mix ns | recovered ns | mix/plain | O3 bytes plain/perm/mix/recovered |
|---|---:|---:|---:|---:|---:|---|
| axis | 2.402 | 2.348 | 2.372 | 1.782 | 0.988 | 200/209/206/120 |
| diagonal | 2.462 | 2.355 | 2.350 | 1.957 | 0.954 | 206/209/206/123 |
| oblique | 2.411 | 2.443 | 2.345 | 1.858 | 0.973 | 206/209/206/123 |

値は各processの9 batch中央値を、3 fresh process間で再び中央値にしたns/呼出し。入力更新・loop・checksumの共通費用を含む。recoveredはraw生成のまま追加O3なし。他3版はO3後。全版に同じbench wrapperを後付けし、追加最適化しない。
正36条件の2,377,728呼出しは不一致0。各条件65536 reduced入力と512上位bit違い。混合条件を破る負6条件は全て反例あり。別WABTでは36本×8入力=288呼出し一致。全42本のbyte再生成一致、4対象外profile拒否。
公開binaryだけを入力とする方式既知の回復は18/18成功。fixtureごとに元版・permutation・mixのraw/O3すべてが同一の短い等価binaryとなった。元の4係数列や混合行列を一意復元したという意味ではない。
回復本体単回値の範囲は47.493–55.738 ms。読取・profile照合・出力compileの時間は別で、反復統計や人間の解析開発時間ではない。
Node全processの最大RSS範囲は35872–36252 KiB。通常3版のWasm linear memoryは各65536 bytes、回復版はmemoryなし。Pythonの全列挙signatureや解析器のpeak memoryは測定していない。
214/324 batchが10ms未満。calibration上限2^22に達した場合もあり、目標batch時間を全件満たしたという解釈はしない。CPU affinity/frequencyは未固定。
この規模でmixとplainの時間は近いが、数%の差を確定した高速化とは扱わない。費用増大は小さい一方、対照より解析を難しくする機構は実証できなかった。
近い既存技術は、有限データ上で同じactivation patternを持つ係数のconeとmerge。整数格子を全列挙する差分だけで独立した新規性があるとは結論しない。
