# 反例の観測範囲の訂正と監査

2026-10-24。条件合成と反例抽出の契約は、**各API終了後の結果および全memory/table内容**を比較するものだった。private stateまで検査用exportで読むため、全ての反例を「公開APIだけで区別できる」と呼ぶのは誤りである。会話でもこの表現を訂正した。

[393反例の再実行・再分類](../../results/state-witness/guard-observation-audit-v1/results.json)は次の内訳になった。

|最初に差が出た観測|反例列数|意味|
|---|---:|---|
|元APIのreturn/trap|96|追加の内部状態観測なしで、この列により区別できる|
|元からexportされているmemoryのbytes|234|元API列と元の公開memory読取りで区別できる|
|検査時にだけ公開したprivate memory/table|63|この列を公開APIだけの反例と扱わない|

後者63件を持つmoduleは、元のmemory/table exportもbyte読取りAPIもなく、今回の限定profileでは、返却値・trapに影響するsegment状態対の有限グラフを閉じられた。その結果、**任意の元関数API列の返却値・trapは同一**だった。内蔵clock、OOM、実行時間等の観測は含まない。単なる「反例がまだ見つからない」ではなく、この限定契約でのモデル判定である。

最長128呼出しのchainを含む追加14例は、内部storeを比較するための対照だった。深さ4では10例のstore差が見つからないという結果は有効だが、「10例の公開API不具合を見逃す」という説明には使えない。資料上もstore契約の最短反例と明記する。

この訂正は等式条件や実行値の変更ではなく、**何に対する反例か**の訂正である。生成器の実装効果と元APIの意味保存を分けるというKの目的に照らして、自分自身の集計にも同じ区別を適用した。これを新たな不具合発見数や新原理の証拠に読み替えない。

```powershell
python research/state-witness/guard-observation-audit.py results/state-witness/guard-witness-v1 results/state-witness/local-observation-audit
```

この追試はNodeで実施した。393列自体は以前のNode/Wasmtime追試で一致しているが、今回の公開export分類とreturn/trapグラフの判定は、別々のengineで新しく全て再実行したとはしない。
