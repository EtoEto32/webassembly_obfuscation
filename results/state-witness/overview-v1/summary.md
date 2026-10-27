# 現在の実測の索引

2026-10-24。保存済みJSONから導出。契約・store・呼出し・binaryの件数を合算してbug件数にしない。

|項目|実測|意味|
|---|---:|---|
|直接生成の条件照合|384契約 / 768 store|肯定側はこの追加検査では条件照合|
|小反例再生|248 + 32 / engine|Node・Wasmtime。自然なbug件数ではない|
|長い反例|12 / engine、最大97 API|小反例の費用測定には混ぜない|
|既知worklist|400条件一致|parser・WPを共有|
|source-only artifact|79 binary fileを再生成|複製を含む|
|ffmpeg制御変種|7320寿命差 / engine|1 GiB hashは同じ、元API実行0|

反例生成部分の費用比は37.80倍。前処理と生成中央値の和の比は1.30倍で、後者はend-to-endの正式測定ではない。

新しい一般アルゴリズムと自然な必要例は未確立。[研究判断](../../../research/state-witness/status.md)・[草稿](../../../research/state-witness/paper-draft.md)・[再現手順](../../../research/state-witness/quickstart.md)を参照する。
