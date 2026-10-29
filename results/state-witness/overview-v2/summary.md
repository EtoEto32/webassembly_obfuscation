# 現在の実測の索引

2026-10-25。保存済みJSONから導出。契約・store・呼出し・binaryの件数を合算してbug件数にしない。

|項目|実測|意味|
|---|---:|---|
|直接生成の条件照合|384契約 / 768 store|肯定側はこの追加検査では条件照合|
|小反例再生|248 + 32 / engine|Node・Wasmtime。自然なbug件数ではない|
|長い反例|12 / engine、最大97 API|小反例の費用測定には混ぜない|
|既知worklist|400条件一致|parser・WPを共有|
|独立した既知等式backend|404条件一致|frontendを共有、等式WPは別実装|
|実アプリの元処理|40 command、20比較対一致|自然な復元bugではなく制御変種|
|公式Wizer CLI|4受理 / 4明示的未対応|受理例は二engineで観測一致|
|source-only artifact|79 binary fileを再生成|複製を含む|
|ffmpegの先行起動対照|7320寿命差 / engine|1 GiB hash一致、当該試験だけでは元API実行0|

反例生成部分の費用比は37.80倍。前処理と生成中央値の和の比は1.30倍で、後者はend-to-endの正式測定ではない。

追加の既知等式backendは人工chainでK worklistより1.50–3.73倍速かった。新しい解析算法の主テーマとして現状のKは推奨しない。

独立した用途で評価判断を改善する証拠が未達。[厳格な採否判断](../../../research/state-witness/masters-verdict-20261025.md)・[草稿](../../../research/state-witness/paper-draft.md)・[再現手順](../../../research/state-witness/quickstart.md)を参照する。
