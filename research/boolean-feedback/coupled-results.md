# 後続状態による切替：結果と不採用理由

2026-10-23。[実験前の仮説](coupled-plan.md)を実装し、意味上の小部分を探す適応解析まで検査した。**SCC分割を壊す効果は実測したが、主特許候補には採用しない。** Boolean残差候補の第3設計段階として記録する。3案を水増しするための別候補扱いはしない。

## 生成規則と正当性

2座標の族はN_A=[0,0,1,2], N_B=[0,0,0,2]、3座標の族はN_A=[0,2,3,0,0,2,0,0], N_B=[0,4,3,0,0,0,0,0]。各三角Fの全状態に対して、両モードの遷移の和集合が正しい固定点以外にcycleを持たないことを検査した。最悪回数は3/5。rank証明136件・辺1,320本を別実装でも照合した。

各群gについてe_g=s_g XOR F_g(s)、cは後続stateのrotateのXOR、更新は `H_g = F_g XOR N_A(e_g) XOR (c AND (N_A(e_g) XOR N_B(e_g)))`。ANFを展開し、元F、群境界、モード分解、seedは配布しない。群ごとのFの先行入力が固定された後、cは毎回・毎bit変わっても正答へ収束する。群の元の順序に沿って帰納すれば上限は各群boundの和になる。selector中の回転は任意切替として扱えるが、Fの群内部の回転はこの論証では許さない。

単独で正しい補正器を自由に切り替えてよいわけではない。N_Aと零補正器ではF=(0, NOT s0, 0)において0→1→0のcycleが可能。実Wasmで8回更新後の第2語が0となり、正しい全1との差を確認した。この反例は切替安定性の既存理論を否定するものではない。

## 公開binaryからの適応解析

旧解析の最大3語SCCという制約に対し、切替版の最大SCCはmix8/select10/chain12で6/9/10語になった。旧解析器は全6条件を未対応と判定した。これを解析耐性の成功には数えない。

`coupled-attack.py`は最大3語の候補部分集合を探索する。候補内の1bit状態を列挙し、未回復stateと回転した未知state bitを毎回任意に変わる環境として存在量化する。固定入力bitを変数とするBDD遷移関係を作り、全初期状態の到達集合が7回以内に一つの吸収状態へ縮むことを検査する。合格した部分の出力を入力式へ置換し、残りへ進む。量化は実際の32bit間の関係を広げる保守的近似であり、未対応の回転を暗黙に無視してはいない。

生成側のN、F、群境界、順序を読まない。Wasmをvalidateし、公開descriptorからraw/O3評価器を再生成してbyte照合する。合成した小部分の収束上限の和が配布binaryの回数以内かも確認する。short-round改変は`bound_not_certified`、循環反例は`stalled`となった。

|関数|固定補正の解析 ms|切替補正の解析 ms|切替/固定の解析比|切替/固定の実行比|
|---|---:|---:|---:|---:|
|mix8|17.449|53.390|3.06|3.70|
|select10|28.416|99.877|3.51|3.74|
|chain12|282.430|842.292|2.98|3.50|

同じ新解析器を使ったO3値。固定版には既存SCC解析のさらに速い5.60/4.57/13.56msもあり、新解析器だけを最強攻撃としない。解析時間は読取りと出力生成を除く単回値。raw/O3・固定/切替の全12条件を回復し、timeout・crash・node capはなかった。回復式は元sourceの逐語復元ではなく、入力から同じ結果を得る通常の非反復Wasmである。

## 正当性と性能

主24binaryの102,552呼出しと、回復24binaryの102,552呼出しが一致。同じ入力集合の再利用を独立標本として足し合わせない。回復12モデルはSMT UNSAT。ランダムscratch6条件1,536呼出しで正答とdescriptor/tailの不変を確認。WABT interpreterでも切替6条件24呼出しを確認した。

BDD証明器は独立な有限graph計算と768ケースで照合し、256を合格、512を不合格とし不一致0。初版のランダム512ケースは全て不合格だったため、肯定例を追加した結果を`certificate-crosscheck-v2.json`へ分けて保存した。検証手段の完全性・任意Wasm全体の形式同値証明を主張しない。

実行時間の中央値は固定/切替でmix8=962.198/3,559.058ns、select10=1,456.787/5,448.828ns、chain12=3,026.453/10,600.049ns。plainは約1.20–1.41ns。O3サイズは固定/切替で1,071/2,793、1,207/3,225、1,936/5,072bytes。private linear memoryは各65,536bytes、plainは0。Node peak RSS35,740–36,164KiBはprocess全体の値。

36fresh process、7batch/process、warmup16,384、20ms校正、全252batchが10ms以上。共通Wasm wrapperをcoreのO3後に追加、入力は相関したLCG/rotate列。変換時間・batchばらつき・RSSは[集計報告](../../results/invention-20261023/boolean-feedback-report-v1/report.md)と生JSONへ保存した。独立したWASMixer等を同一費用へ調整した比較ではない。

## 研究判断

小SCCをなくす効果と、今回の解析器で約3倍の負担増は示せた。しかし実行も約3.5–3.7倍増え、元版に対する費用は大きい。任意外部stateに対して安定する小部分を作る正当性条件自体が、未知selectorを量化して意味上の群を回復する手掛かりになった。小規模3関数・1seedの結果であり、一般の結合方式を否定しない。

切替Boolean networkの安定性、BDD量化、部分系の収束判定はいずれも既存の考え方。全三角Fに共通の補正器族を選ぶ具体的なcompiler構成の新規性は未確立で、費用対効果も主張できない。主特許候補としてはここで不採用にし、同じ方式のパラメータ追加を別原理とは扱わない。

## 再現

```powershell
python research/boolean-feedback/family.py results/bf-family-replay
python research/boolean-feedback/coupled-run.py results/invention-20261023/hidden-filtration-smoke-v1 results/bf-coupled-replay
python research/boolean-feedback/coupled-batch.py results/bf-coupled-replay results/bf-coupled-attack-replay
python research/boolean-feedback/coupled-audit.py results/bf-coupled-replay results/bf-coupled-attack-replay results/bf-coupled-audit-replay
python research/boolean-feedback/family-audit.py results/bf-family-replay/certificates.json results/bf-coupled-replay results/bf-family-audit-replay
python research/boolean-feedback/coupled-performance.py results/bf-coupled-replay results/bf-coupled-runtime-replay
```
