# コピー結果を実体化しない変換：初期ゲートの結果

2026-10-23。既知のlazy copy/read forwardingに近く、方式既知の回復が容易なため、主特許候補には不採用。値の座標変換から離れる候補の初期検査であり、一般のWasmや実用的な保護対象へ適用した結果ではない。

## 正当性と解除

- 2/4/8回copy×2parameter配置×raw/O3。未変換・変換・回復を合わせて36本、92,544呼出し、11,760期待trap、不一致0。
- 部分重なり、同一範囲、零長、memory末尾、uint32和のoverflow、不正query、失敗後の次の呼出しを含む。参照は独立JS copyWithin。privateな途中memoryの一致は要求しない。
- 2copyの全小モデル：memory長1..8、1,115,334個のorigin照合で一致。byte値ではなく出自indexを比較する。
- 別WABT interpreter：144呼出し一致。export memoryと範囲検査欠落の2不正profileを拒否。
- 検査を省く版とcopy順序を誤る版の12個すべてで反例を検出。正対象の件数に含めない。
- 方式既知の回復：12/12。元のparameter配置、source、seedを渡さず、条件式から抽出。回復Wasmは全12で元rawとbyte単位で同一。
- 回復の単回時間（WABT読取と完全profile照合を含む）78.032〜118.978ms。変換6件は99.307〜106.894ms。

初版はO3がoperand stackへ古い値を残してlocalを再利用する形式に未対応だった。stackとlocal.teeを実行順に扱うよう修正すると回復できた。未対応を難読化成功として数えない。

## 性能の限定的な対照

各copyは16KiB、呼出しごとに原版が64KiB scratchを初期化し、最後に1byteだけ観測する人工的な負荷。疎な読出しに有利な設定であり、通常のアプリ全体の高速化を示すものではない。共通Wasm loopの入力生成・呼出し・checksumを含む。

|copy数|未変換 ns|引戻し ns|回復後 ns|未変換/引戻し|
|---:|---:|---:|---:|---:|
|2|887.747|5.102|909.872|174.00|
|4|1207.468|9.562|1199.210|126.28|
|8|1781.238|18.056|1779.010|98.65|

27 fresh Node process、189batch、全batch10ms以上。各条件3process×7batch、warmup16,384、20msを目標に校正。process中央値の中央値を掲載し、全batchとprocess中央値はraw.json/summary.json。eager optimizing compilation指定、CPU affinity/周波数は未固定。

最初のruntime-v1では高速な版が校正の上限へ達し、36batchが10ms未満だった。反復上限を引き上げたruntime-v2だけを確定値に使い、v1と標本を合算しない。

|copy数|版|O3 binary bytes|linear memory bytes|
|---:|---|---:|---:|
|2|plain|4200|65536|
|2|pullback|4275|65536|
|2|recovered|4200|65536|
|4|plain|4226|65536|
|4|pullback|4387|65536|
|4|recovered|4226|65536|
|8|plain|4278|65536|
|8|pullback|4607|65536|
|8|recovered|4278|65536|

Node全process peak RSS 35,780〜36,172KiB。変換器だけのpeak RAMは未測定。

## 採否と次への条件

この負荷では計算を省く最適化として有利な値が得られた。しかし物理的なcopy列が範囲条件の列に移っただけで、その対応は公開binaryに残る。高速なこと、途中のmemoryが原版と異なること、copy命令が消えたことは、保護の根拠にならない。

lazy memcpy/read forwardingは既知で、Wasmの正確なtrap保持は必要な実装条件である。今回の条件保存を独立した新発明と認定しない。この枝の係数・copy段数・データ量を増やす改良は主案にしない。次は、更新前後の作用を局所的な対応式として残さない生成規則が必要である。

NotDec/StackSightの実行、大規模実アプリ、共有memory、persistentな外部状態、途中のhost観測は未検証。数学的なcopyの意味保存論証と有限Wasmテストを区別する。

READMEに再現コマンド。根拠はmain-v2/model-v1/audit-v1/runtime-v2。sources/にコードのsnapshot、provenance.jsonに根拠と使用ツールのSHA-256。外部公開・pushは行っていない。
