# API呼出し後の状態比較に対する最短反例列

2026-10-24。[事前計画](guard-witness-plan.md)、[解析実装](guard-witness.py)。既知の固定点・反例復元・幅優先探索を利用した、Kの限定profileの診断機能である。新しい一般探索アルゴリズムとはしない。

**観測範囲を訂正・明確化した。[監査](guard-observation-audit.md)による393列の内訳は、元return/trap差96、元公開memory差234、追加observerだけのprivate store差63である。後者63は元関数APIの結果だけでは区別できない。** 本書の「反例」は各API後の全memory/tableを含むstore契約への反例を意味する。

条件を満たさない具体storeについて、固定点の反復履歴から、初めて差が出る元API呼出し列を復元する。G_iが初めて不成立となるiが最短長で、原因のAPIへ進むごとにrankを一つ減らす。trap後にhostが再呼出しする場合を含む。初期storeの元program入口からの到達可能性は保証しない。

## 実測

[134 module・964 store](../../results/state-witness/guard-witness-v1/results.json)を分類し、571件で条件が成立、393件で反例列を出した。memory手書き12、既存乱数96、table手書き12、追加copy-chain14 moduleを含む。393反例はNodeと[Wasmtime](../../results/state-witness/guard-witness-cross-v1/results.json)で全て再現し、各engine1,806 API呼出しで最初の差が予測した末尾に出た。tableのWasmtime比較は既知の純粋定数関数tagに限定し、別途43,841tag呼出しを要した。571肯定分類をこの反例再生で実行検証したと数えない。

全964 storeで、同じ限定modelの**重複状態を除く具体幅優先探索**とも照合し、分類と反例の最短長が一致した。これは完全に独立した意味論実装ではなく、bulk効果を共有する比較である。既存の深さ4全列検査で得られた反例との長さも照合した。

copy-chainはmemory/tableそれぞれ長さ2/4/8/16/32/64/128を用いる。最後の異なるcellが先頭へ届くまでcopyを繰り返し、最後にtestを呼ぶ必要がある。最短長はそれぞれその長さであり、**10例は深さ4の検査ではprivate store差を発見できない**。元の関数APIのreturn/trapは同一であり、公開API不具合の見逃しや実製品の10不具合とは数えない。

## 十分性だけでなく反復式も照合

[別のarray式による検査](guard-layer-check.py)で、各有限深さの条件と「一回の観測一致かつ前段の後続条件」が同値かを確認した。[130条件・667義務](../../results/state-witness/guard-layer-check-v1/results.json)は全てUNSAT。検査器のfootprint上限32により大きいchain4例を保留し、solver unknownは0だった。固定点の安定した最後の段も検査した。

これは**共有parserから作ったmodel内の各反復式の同値検査**である。公式Wasm意味論からの機械証明、一般APIの最短反例生成、到達可能性の証明とは区別する。

## 優位を誇張しない

重複除去した具体探索も、長さ128の対照を255状態で解けた。反例一つのために記号条件を準備する場合、今回の単発診断時間では準備費用が探索費用を上回る条件がある。無策な全列列挙だけを比較対象にして指数的優位を主張しない。準備時間・抽出時間はmanifestに残したが、ウォームアップ付き性能実験とは区別する。

その後の[準備費用込み反復測定](guard-cost-results.md)でも、単一state・反復した同一state・一様乱数ではBFSが速く、深い反例の32割当てでは準備を償却できるという限定した結果となった。[segment依存関係の射影](guard-projection-results.md)は無関係な状態列挙を減らしたが、既知の削減法である。

研究上の追加価値は、初期storeが条件を満たすときと、満たさず具体反例が出るときを一つの限定modelで説明できる点にある。最近接の条件合成・モデル検査の一般原理は既知であり、この対象への適用と実証を修士研究の候補として評価する。

```powershell
python research/state-witness/guard-witness-cases.py results/state-witness/guard-controls-v1 results/state-witness/guard-random-v1 results/state-witness/guard-table-controls-v1 results/state-witness/local-witness
python research/state-witness/guard-witness-cross.py results/state-witness/local-witness results/state-witness/local-witness-cross
python research/state-witness/guard-layer-check.py results/state-witness/local-witness results/state-witness/local-layer-check
```
