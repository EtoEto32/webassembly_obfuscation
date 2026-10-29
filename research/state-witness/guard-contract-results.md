# 観測する範囲を選ぶ条件合成

2026-10-24。[実装前の計画](guard-contract-plan.md)、[実装](guard-contract.py)。これはKの診断精度を上げる別実装である。既知の関係解析・等式抽象を利用し、新しい一般的な観測同値理論とは主張しない。

## なぜ二つのstoreが必要か

全store契約では、各API後に左右のmemory/tableが等しいことを要求できた。しかし非公開の差を許す契約では、途中から左右のstoreが異なる。segment寿命が一致しても、その後のcopyでprivate tableの差がpublic tableへ移ることがある。そこで左右のcell変数を別々に持ち、両方のpost-state写像で条件を逆代入する。寿命が一致した状態も解析を継続する。

契約は三つ選べる。

|CLI値|観測|
|---|---|
|`full`|元APIの返却値/trap、および全memory/table|
|`public`|元APIの返却値/trap、および元からexportされたmemory/table|
|`returns`|元関数APIの返却値/trap。byteを返す読取りAPIがあればその値も含む|

tableの比較は元function indexの対応関係に基づくdescriptor一致であり、任意関数の意味が等しいことまで比較しない。したがって一般のcontextual equivalenceを完全に判定するものではない。下記の公開table例は、元からexportされた異なる定数関数を使い、hostから直接区別できる構成にした。

## 回帰と新しい対照

[既存134module・964storeの回帰](../../results/state-witness/guard-contract-v1/regressions.json)で、`full`の条件と反例最短長は従来と一致した。`full`は571一致/393差、`public`は634一致/330差、`returns`は850一致/114差だった。これは限定modelの分類で、修正後に全964入力を再度engineで実行した件数ではない。

[以前の監査](guard-observation-audit.md)のreturn/trap差96は、以前の全store反例列を選んだときの最初の差の分類である。`returns`の114は、この契約のために反例を選び直した結果であり、両者は集計対象が異なる。今回の114反例は全て長さ1だった。あるAPIではstore差が先に検出されても、別のAPIを選べばreturn/trapだけで差が出る場合が含まれる。

新しい13module・39契約・78storeでは、private tableへの差の生成、公開tableへのcopy、公開前の上書き、private memoryのbyte読取りAPIを検査した。57肯定storeは指定した複数列を実行し、21否定storeは合成した最短列を実行した。[Node](../../results/state-witness/guard-contract-v1/results.json)と[Wasmtime](../../results/state-witness/guard-contract-cross-v1/results.json)の各4,378 API呼出しで整合した。Wasmtimeのtable oracleは既知の純粋定数関数tagに限定し、別途20,868呼出しを要した。

private tableからpublic tableへ伝える例では、全store契約なら1回のmaskで差が出るが、public契約ではmask後にcopyを重ねてpublishする必要があり、最短長2/3/5/9/17/33を得た。公開直前にprivate tableを上書きする対照ではpublic契約が無条件一致となった。private memoryを読むAPIの対照では、memoryが非公開でもmask→readの2呼出しで返却byteが異なった。

## 検査用exportなしでの確認

さらに[8本の元binaryだけの実行](../../results/state-witness/guard-contract-reachable-v1/results.json)を行った。tableの初期値をactive elemで設定し、左は元API `retire`、右は元API `release_b`を呼ぶことで、二つのstateをどちらも到達可能にした。非公開tableの書換え、検査用export、observerは使っていない。

その後の診断列では、公開tableの関数をhostが実際に呼ぶ。未修復4例では、2/5/17/33呼出し目に、公開関数の返値が202対101に分かれた。公開前に上書きする4対照では101対101となった。Node/Wasmtime各228診断API呼出し、16準備API呼出し、16公開関数呼出しが一致した。

これは異なるAPI履歴から作ったstate対の観測実験である。実際の復元器がこれらのstateを作ったと主張しない。初期storeが到達可能であることをこの対照で確認したが、一般の合成条件の全割当ての到達可能性まで保証するものではない。

## 検査器と失敗対照

[独立した二つのarray式](guard-contract-check.py)で、各反復層の条件、安定した段、共通初期storeへの射影を確認した。[39契約・301義務](../../results/state-witness/guard-contract-check-v2/results.json)はUNSAT、solver unknownは0だった。parser/profileは共有し、影響範囲外のcellが左右で共通かつ不変という前提を置く。Wasm意味論全体からの機械化証明ではない。

最初のchecker実行v1はJSONの整数key/string keyの比較で停止したharness errorで、SMT成功件数には含めない。失敗記録と修正前scriptを保存し、正規化後のv2を結果とした。

segment寿命が揃っただけで解析を打ち切る不完全版は、公開tableへ伝わる6条件とbyte読取りAPIの2契約、計8否定storeを誤って一致とした。これらの反例列は上記engine実行で再現済みである。従来の全store契約で安全だった打切りを、観測の弱い契約へそのまま持ち込めないことを示す。

## 評価上の位置付け

新規性の候補は、復元状態の差を一律に成功/失敗とせず、選んだ契約に応じた条件と反例へ落とし込む限定手法と実証である。二項関係、観測範囲の選択、固定点計算の一般原理は既知である。実製品由来のstate対への追加適用と、近い検証器との同一課題比較は残る。

```powershell
python research/state-witness/guard-contract-cases.py results/state-witness/guard-witness-v1 results/state-witness/guard-observation-audit-v1 results/state-witness/local-contract
python research/state-witness/guard-contract-cross.py results/state-witness/local-contract results/state-witness/local-contract-cross
python research/state-witness/guard-contract-check.py results/state-witness/local-contract results/state-witness/local-contract-check
python research/state-witness/guard-contract-reachable.py results/state-witness/local-contract-reachable
```
