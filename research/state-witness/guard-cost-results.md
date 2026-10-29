# 条件合成の費用と適用範囲

2026-10-24。[測定前の計画](guard-cost-plan.md)。[修正版v2実測](../../results/state-witness/guard-cost-v2/results.json)を使用する。v1では非memo化BFSにも不要なcache用key作成・登録が残っていたため、これを除去して再測定した。v1も履歴として保持する。

## 反復測定

Python 3.9、Windows 10 API表示10.0.26100、逐次の3独立process、各process2 warmup/7反復。実行順をseed固定でshuffleした。WABT読取り/model構築を解析時間から分離し、その所要時間はprocessごとのJSONに残した。測定はPython解析器の費用であり、Wasm関数の実行時間や復元器自体の速度ではない。

長さ128の人工copy-chainで、初期storeを調べるbatchの時間は以下となった。準備込み欄は**準備のprocess中央値とbatchのprocess中央値の和**であり、同一試行の合計を再度中央値にしたものではない。

|資源・入力分布|条件判定（準備込）ms|反例抽出（準備込）ms|具体BFS ms|memo化BFS ms|
|---|---:|---:|---:|---:|
|memory・末尾だけ違う1件|56.725|60.322|13.924|14.041|
|memory・同一肯定store32回|57.291|57.352|3.597|0.265|
|memory・末尾5位置の32割当て|57.308|162.584|423.242|421.639|
|memory・一様乱数32件|56.713|56.773|0.350|0.504|
|table・末尾だけ違う1件|57.798|61.863|17.785|17.752|
|table・同一肯定store32回|58.431|58.510|4.600|0.307|
|table・末尾5位置の32割当て|58.422|176.892|538.331|535.975|
|table・一様乱数32件|57.790|58.101|2.909|3.060|

準備費用はmemory128で56.695ms（process中央値の範囲55.499–56.818）、table128で57.767ms（57.498–58.305）。深い反例が多い32入力をまとめて調べる人工分布では、準備を含めても反例抽出がBFSより速かった。一方、単一のstore、同じstoreの反復、すぐ差が出る一様乱数ではBFSが速い。無条件の高速性は主張しない。

現在の反例準備は、元の固定点を計算した後に履歴を再構成する二重計算を含む。これも測定に含めた。条件だけが欲しい場合の最小実装費用ではない。BFSは一つの具体storeの判定、条件合成は全初期storeに対する式を返すので、出力能力にも差がある。

process全体のpeak RSSは25.59–26.09MiB。128位置の準備でPythonが追跡したallocation peakはmemory約1.131MiB、table約1.144–1.149MiBだった。この値はnative allocationを含まず、方式別の総memory使用量でもない。bytecode sizeとmodel読取り時間もraw JSONに保存した。解析は元binaryを実行用に変更しないため、guest binary size overheadは発生しない。検査用exportを追加する別の実行harnessのsizeは混同しない。

## 状態数の限界

[無関係なdropの対照](../../results/state-witness/guard-state-limit-v1/results.json)では、独立dropを10個にすると1024状態・約50.067ms、11個で状態数上限に達した。同じ6例を既存def-use解析は全て証明でき、10個で約0.328ms、11個で約0.342msだった。Wasmtime768 API呼出しで対照のstore一致も確認した。追加した記号的解析が常に既存の簡単な方法を上回るわけではない。

この問題は[依存segmentへの射影](guard-projection-results.md)で改善した。修正前の結果は保持し、既知の依存関係削減を新原理とはしない。

```powershell
python research/state-witness/guard-cost.py results/state-witness/guard-witness-v1 results/state-witness/local-guard-cost
python research/state-witness/guard-state-limit.py results/state-witness/local-guard-state-limit
```
