# 出力履歴による内部状態の消去：事前ゲート

2026-10-19。直前のRelaxed SIMD案は出力に独立なmaskを固定できた。今回は元から存在する内部状態yを実行表現から消す。新規性は未確認で、非線形系の入出力実現・状態消去が近い。Wasmのi32剰余環では偶数係数に逆元がない点を確認するが、他のword形式でも使えるのでWasm固有性は限定的。

対象はbyte入力uを順番に読むscanで、同時更新 `x'=P(x,u)+b*y; y'=Q(x,u)+R(x,u)*y`、公開出力x。P/Q/Rは2変数の次数2以下の多項式、全演算mod2^32。出力履歴により `x_next=P(x_current,u_current)+b*Q(x_previous,u_previous)+R(x_previous,u_previous)*(x_current-P(x_previous,u_previous))` と更新する。最初の一歩は元の初期値から計算する。除算は使わない。

反証の第一候補はw=b*yを状態にした等価実装。bが偶数で元のyを一意に戻せなくても、`x'=P+w; w'=b*Q+R*w` で足りる。生成式からこの短い実現に戻せる費用を測る。元の状態の非一意性だけを保護効果にしない。

4モデル（b=3,6,256,2^31）×source/history/quotient×raw/O3、historyからの回復8本。バイナリを入力とするCLIを作り、実際に使われるprivate memoryの係数だけを抽出し、全moduleが既知profileと同じことを再構築で検査する。別の機能を隠したmoduleを受理しない。generic Wasm変換器ではない。

境界・ランダム・全短いbinary word、trapと公開memory保存、WABT別エンジン、局所代数と非単射性の対照を検査する。runtime/size/RSS/変換/解析時間を測る。公開ABI・入力load順序を維持する。元yを外部へ返す、yへの非線形依存を持つ、private memoryを外から書ける場合は対象外。
