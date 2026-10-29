# 同期import境界を含む条件合成

2026-10-24。[計画](guard-import-plan.md)、[実装](guard-import.py)、[限定論証](guard-import-proof.md)。従来のclosed parserはそのまま残し、host summaryを明示する別profileを実装した。新しい一般的WPや環境検証の発明とはしない。

write契約の注意：このページの`public`は対象全cellを毎回上書きする効果である。書込みをしない選択や部分書込みも許す契約は、後から追加した[may-public版](guard-import-may-results.md)を使う。旧試験群では両者の判定差が出なかったが、別の2-import対照では無条件一致と充足不能へ分かれた。

## 制御対照と検査

memory/tableの2種類に、importがinit前・init後・修復あり・長さ0・2回呼出し・到達不能・修復前read・修復後readの8配置を作った。16 binaryをvalidateし、read有無×write有無×public/returns×terminal/reenterの256契約を調べた。

|項目|結果|
|---|---:|
|条件分類：無条件 / 条件付き / 充足不能|158 / 42 / 56|
|固定した共通初期store|512|
|条件を満たす / 満たさないstore|358 / 154|
|否定反例：1 API / 2 API|136 / 18|
|Node・Wasmtimeそれぞれの比較実行|1,228|
|各engineの診断API / 準備API|2,732 / 2,456|
|各engineの実際のimport呼出し / cell書込み|1,988 / 896|
|pure table identity tag呼出し|各1,847|
|別array式の再帰・射影義務|1,164 UNSAT、unknown 0|

[実行結果](../../results/state-witness/guard-import-controls-v1/results.json)、[全条件・反例・trace](../../results/state-witness/guard-import-controls-v1/manifest.json)、[array検査](../../results/state-witness/guard-import-check-v1/results.json)。肯定例は3つのhost入力を再生し、否定例はSMTで選んだ具体入力を再生した。1,228は独立したprogram数や不具合数ではない。table参照は、この小例で作った純粋な定数関数を呼びidentityに対応付けている。任意関数を安全に呼べる一般oracleではない。

最初の起動はscript内の依存ファイル相対pathを誤っており、実験directory作成前にFileNotFoundErrorで停止した。`__file__`基準へ修正後に上記を実行した。これは解析アルゴリズムの成功/失敗例には数えない。

## 何を分けられたか

1. initで左だけがtrapし、右だけがimportを呼んだ後にtrapする場合、最終outcomeが同じでもhost traceは違う。
2. 書込みimportが修復の前にある場合と、その後にある場合では条件が違う。全ての書込みをAPI境界へ移すモデルでは表現できない。
3. returns/reenter契約では、`arm`が残す公開memory差を無視しても、次の`finish`のhost readがそれを観測する場合がある。readなし、またはread前の修復では差が消える。従来のclosed terminal/returns簡約を無条件にimport付きへ拡張しない。

## アブレーション

同じ512初期storeで、意図的に誤ったモデルを比較した。[結果](../../results/state-witness/guard-import-ablation-v1/results.json)。既存製品の能力比較ではない。

|除いた/移した要素|一致と誤判定|差ありと誤判定|
|---|---:|---:|
|import自体をnop扱い|90|0|
|host readを無視|14|0|
|host writeを無視|34|0|
|importを消し、書込みだけAPI間へ移動|70|12|

## 単純な有限探索との比較

[別の具体BFS](guard-import-finite.py)では、program定数と二つの追加値から成る有限domainの共通初期storeを全列挙した。256契約・1,024 storeで一致674/反例350、最大14状態、計13,490遷移を探索し、全て条件合成器と一致した。[結果](../../results/state-witness/guard-import-finite-v1/results.json)。このBFSは等式写像・SMT・固定点層を使わないがparserは共有する。条件生成器だけが解けるという結果ではない。数値は公平な性能比較ではない。

有限domain化は既知のdata independenceの応用である。このcopy/constant profileに限る縮約の論証を[付記](guard-import-proof.md)に記した。検査結果を、公式Wasm全体や任意hostに対する証明とはしない。

## 実復元実験の継続部分との接続

[元entryの4 fixture](guard-import-entry-results.md)を入力し、正規化したentryのoffset3（touchの直前）を明示して解析した。Aがdead/live、Bは右でdead/liveの二通り、write有無の16条件を検査した。1/4byte例はwriteなしで初期bytes依存、任意writeありで充足不能、修復・0長は無条件一致になった。[16条件と実行結果](../../results/state-witness/guard-import-continuation-v1/manifest.json)。追加44義務はUNSAT、unknown0だった。

継続を実行するderived binaryを生成し、両engine各32 entry・32 touch呼出しで検査した。結果は既に保存したmigrate stop1/stop2の全public memory hash・host trace・trap結果に一致した。元entry全体を先頭から解析するとdropで寿命差が消え、全16条件が無条件一致になる。この違いも保存した。

**指定した継続位置と寿命差の仮説を検査した実験である。** 復元器の保存PC・活性stack・寿命metadataを自動抽出して証明したものではない。import付き元binaryを読めるようになったことと、変換後復元器全体を解析できたことを分ける。新しい独立した不具合発見数を追加しない。

## 再現

[同じ条件を生成する一般SMT対照](guard-import-generic-results.md)も全256契約で一致した。さらに[profile境界](../../results/state-witness/guard-import-boundary-v1/results.json)で、未対応11例の拒否と、store8/一回通過loopの正規化4例を各engine8呼出しで確認した。

```powershell
python research/state-witness/guard-import-controls.py results/state-witness/local-import-controls
python research/state-witness/guard-import-check.py results/state-witness/local-import-controls results/state-witness/local-import-check
python research/state-witness/guard-import-ablation.py results/state-witness/local-import-controls results/state-witness/local-import-ablation
python research/state-witness/guard-import-finite.py results/state-witness/local-import-controls results/state-witness/local-import-finite
python research/state-witness/guard-import-continuation.py results/state-witness/guard-import-entry-inputs-v1 results/state-witness/guard-import-entry-v1 results/state-witness/local-import-continuation
```

host summaryはtrusted入力である。実hostが再入・grow・例外・外部stateを持つ場合や、指定した読取り/書込み範囲を超える場合、この結果は適用しない。閉じた版の最短反例の保証も、新profileへ移植済みとはしていない。
