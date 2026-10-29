# 2026-10-24 最小実験の実測

対象はCore Wasmと制御したNodeホスト。Component Model/WIT/WASIの統合実装、既存ランタイムの脆弱性再現、特許性の証明ではない。

## A: 権限依存

|binary|方式|ケース|不正受付|不要拒否|二重受付|
|---|---|---:|---:|---:|---:|
|authority-raw.wasm|entry|216|105|0|0|
|authority-raw.wasm|global|216|0|84|0|
|authority-raw.wasm|resource|216|0|27|0|
|authority-raw.wasm|operation|216|0|0|0|
|authority-O3.wasm|entry|216|105|0|0|
|authority-O3.wasm|global|216|0|84|0|
|authority-O3.wasm|resource|216|0|27|0|
|authority-O3.wasm|operation|216|0|0|0|

同じ216シナリオをraw/O3で実行。現試作は依存選択を手書きしており、型からの生成器は未実装。

## B: 旧値viewと保持payload

|binary|判定|ケース|trap|不一致|退避byte合計|全コピーbyte合計|
|---|---|---:|---:|---:|---:|---:|
|snapshot-byte-raw.wasm|ranges|208|3|0|101|851968|
|snapshot-byte-O3.wasm|ranges|208|3|0|101|851968|
|snapshot-word-offset-raw.wasm|ranges|208|4|0|440|851968|
|snapshot-word-offset-O3.wasm|ranges|208|4|0|440|851968|
|snapshot-wrapped-address-raw.wasm|ranges|208|2|0|202|851968|
|snapshot-wrapped-address-O3.wasm|ranges|208|2|0|202|851968|
|snapshot-two-writes-raw.wasm|ranges|208|4|0|811|851968|
|snapshot-two-writes-O3.wasm|ranges|208|4|0|811|851968|
|snapshot-fill-raw.wasm|ranges|208|4|0|3644|851968|
|snapshot-fill-O3.wasm|ranges|208|4|0|3644|851968|
|snapshot-copy-raw.wasm|ranges|208|4|0|3102|851968|
|snapshot-copy-O3.wasm|ranges|208|4|0|3102|851968|
|snapshot-branch-raw.wasm|ranges|208|4|0|865|851968|
|snapshot-branch-O3.wasm|ranges|208|4|0|865|851968|
|snapshot-partial-trap-raw.wasm|ranges|208|208|0|208|851968|
|snapshot-partial-trap-O3.wasm|ranges|208|208|0|208|851968|
|snapshot-unknown-load-raw.wasm|full|208|0|0|851968|851968|
|snapshot-unknown-load-O3.wasm|full|208|0|0|851968|851968|

合計3744ケース、不一致0。コピーなしの不一致2296。解析できた16本では保持payloadが合計13,631,488→18,746 byte。RSSや総コピー量の比ではない。

### 時間（参考値）

単一Node process内、各方式warmup30回、300呼出し×9反復。ms/呼出しの中央値。固定順測定で、GC・実行順序の交絡があり、速度の優位を結論しない。view全体のmaterializeとchecksumを含む。

|binary|全コピー|範囲生成|同じ範囲の事前評価|コピーなし|
|---|---:|---:|---:|---:|
|snapshot-byte-raw.wasm|0.012134|0.012695|0.012699|0.012220|
|snapshot-byte-O3.wasm|0.012157|0.012583|0.012155|0.012178|
|snapshot-word-offset-raw.wasm|0.012085|0.012361|0.010365|0.010052|
|snapshot-word-offset-O3.wasm|0.011985|0.010268|0.010309|0.010031|
|snapshot-wrapped-address-raw.wasm|0.012199|0.011154|0.010039|0.010537|
|snapshot-wrapped-address-O3.wasm|0.012479|0.010945|0.010230|0.010008|
|snapshot-two-writes-raw.wasm|0.012007|0.010113|0.010403|0.010505|
|snapshot-two-writes-O3.wasm|0.012319|0.010975|0.010592|0.010324|
|snapshot-fill-raw.wasm|0.011979|0.010374|0.009891|0.009998|
|snapshot-fill-O3.wasm|0.011968|0.010250|0.010101|0.009999|
|snapshot-copy-raw.wasm|0.011879|0.010218|0.009840|0.009927|
|snapshot-copy-O3.wasm|0.011928|0.012031|0.012011|0.011960|
|snapshot-branch-raw.wasm|0.011944|0.010847|0.010531|0.010276|
|snapshot-branch-O3.wasm|0.012114|0.011998|0.016192|0.013294|
|snapshot-partial-trap-raw.wasm|0.023353|0.018486|0.017853|0.018191|
|snapshot-partial-trap-O3.wasm|0.017740|0.016687|0.016173|0.016126|
|snapshot-unknown-load-raw.wasm|0.009444|0.010902|0.011005|0.009634|
|snapshot-unknown-load-O3.wasm|0.012126|0.013105|0.013471|0.012024|

## C: 実資源と予約

|binary|方式|イベント列|受付数|実資源peak|上限|
|---|---|---|---:|---:|---:|
|budget-raw.wasm|cancel|cancel-storm|32|64|8|
|budget-raw.wasm|cancel|resolve-before-release|32|64|8|
|budget-raw.wasm|cancel|release-before-resolve|32|2|8|
|budget-raw.wasm|cancel|mixed-seeded|44|28|8|
|budget-raw.wasm|resolve|cancel-storm|4|8|8|
|budget-raw.wasm|resolve|resolve-before-release|32|64|8|
|budget-raw.wasm|resolve|release-before-resolve|32|2|8|
|budget-raw.wasm|resolve|mixed-seeded|44|26|8|
|budget-raw.wasm|release|cancel-storm|4|8|8|
|budget-raw.wasm|release|resolve-before-release|4|8|8|
|budget-raw.wasm|release|release-before-resolve|32|2|8|
|budget-raw.wasm|release|mixed-seeded|25|8|8|
|budget-raw.wasm|semaphore|cancel-storm|4|8|8|
|budget-raw.wasm|semaphore|resolve-before-release|4|8|8|
|budget-raw.wasm|semaphore|release-before-resolve|32|2|8|
|budget-raw.wasm|semaphore|mixed-seeded|25|8|8|
|budget-O3.wasm|cancel|cancel-storm|32|64|8|
|budget-O3.wasm|cancel|resolve-before-release|32|64|8|
|budget-O3.wasm|cancel|release-before-resolve|32|2|8|
|budget-O3.wasm|cancel|mixed-seeded|44|28|8|
|budget-O3.wasm|resolve|cancel-storm|4|8|8|
|budget-O3.wasm|resolve|resolve-before-release|32|64|8|
|budget-O3.wasm|resolve|release-before-resolve|32|2|8|
|budget-O3.wasm|resolve|mixed-seeded|44|26|8|
|budget-O3.wasm|release|cancel-storm|4|8|8|
|budget-O3.wasm|release|resolve-before-release|4|8|8|
|budget-O3.wasm|release|release-before-resolve|32|2|8|
|budget-O3.wasm|release|mixed-seeded|25|8|8|
|budget-O3.wasm|semaphore|cancel-storm|4|8|8|
|budget-O3.wasm|semaphore|resolve-before-release|4|8|8|
|budget-O3.wasm|semaphore|release-before-resolve|32|2|8|
|budget-O3.wasm|semaphore|mixed-seeded|25|8|8|

releaseと独立なlive集合によるsemaphore対照は全イベントで同一。一般のセマフォに対する新しい安全性は確認できなかった。

## 環境・監査

- 環境: Windows-10-10.0.26100-SP0 / Python 3.9.0 / Node v24.15.0 / 11th Gen Intel(R) Core(TM) i9-11900K @ 3.50GHz。
- WABT 1.0.42 / wasm-opt version 133 (version_133)。全22本がvalidationを通過。
- 主結果の60ファイルのhash一致、18上界の再算出一致。
- 別有限モデル186,624照合。これは任意のWasm binaryの全入力証明ではない。
- shared拒否、import/growの全コピー退避、書込み上界の欠落反例を確認。
- WABTでstore後のtrapでもstoreの結果が残る例を確認。
- 各snapshot moduleのlinear memoryは128KiB。Node全体のRSS等はresults.jsonに記録したが、方式別peak memoryは未測定。
- 生成時間はbuild.json（assemble/O3）とmanifest.json（summary_ms）。単回でprocess起動・キャッシュ等を含むため精密な費用比較には使わない。

## v1からの修正

v1は検査自体は完了したが、混合イベント生成にLCGの下位bitを使い、資源を一つも確保しない空疎な列になっていた。v2で上位bitを使い、受付が1件以上あることをassertした。raw/O3のsnapshot入力も同一seedへ揃えた。同じ範囲の事前評価をmanual実装と誤認しないよう名称を修正。v1を新しい独立証拠として合算しない。

## 達成していないもの

WIT自動生成、実Component Model runtime統合、実アプリケーションでの比較、跨るthreadの原子性、完全な先行特許調査、特許取得に十分な新規性・進歩性。
