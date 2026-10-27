# 遷移二乗と双模倣によるBoolean計算

## 入力・出力と保護仮説

入力は実際の.wasm。private memory等も持たない単一export run(i32)->i32の式で、入力bit抽出、AND、OR、literal否定のみを受け付ける。出力はprivate memory上の重み付きgraphをpartition refinementで評価するWasm。結果は0/1である。外部から得る秘密、乱数による近似、暗号はない。

保護対象は、配布binaryから元と同程度に簡潔なBoolean計算を回復する作業。graphの頂点番号や生成seedを完全再現することは要求しない。解析者は方式、全binary、実行環境を利用できる。保存した元source、正解graph、seed、生成ログは解除器へ渡さない。結果採点では別途元式を参照する。

値の座標変換ではなく、**別の関係判定問題を実行して結果を得る**方向を検査する。ただし回路から確率的双模倣への還元は既知であり、独立した発明とは扱わない。今回の追加仮説は、1段と2段の遷移を合成することでgateの局所的な境界を弱めることであった。

## 既知還元を使うgraphの構成

各式gに、同じ色を持つ2状態u_g,v_gを与え、その双模倣同値性がgの真偽になるようにする。

- literal：2個のabsorbing state。色の一致条件を当該入力bitまたはその否定とする。
- AND：u_gは子のu_a,u_bへ各1/2、v_gはv_a,v_bへ各1/2で遷移する。異なる子式の色群を分ける。
- OR：w=(u_a,u_b)、x=(v_a,v_b)、y=(v_a,u_b)、z=(u_a,v_b)という各2遷移の中間状態を同色で作る。u_gからw,x、v_gからy,zへ各1/2で遷移する。2通りのmatchingが論理和を実現する。

これはChenほか2012 §2の構成に基づく。重複した遷移先は重みを加算する。確率samplingはせず、分母2の整数行列A=2Pで同値性を決定する。同じsubexpressionを共有し、最後に頂点番号をseedで置換する。置換は保護効果の独立した要素とはしない。

## 調べた変換

```
parse_and_validate_boolean_source(input.wasm)
(labels, P, output_pair) = circuit_to_bisimulation_graph(source)
L = (I + P) / 2
Q = L * L
emit_integer_partition_evaluator(labels, 16*Q, output_pair)
```

全重み16Qは0..16の整数。元のA、L、source式は出力に添付しない。Wasmはラベルで初期partitionを作り、各状態から各classへの重み合計が違う組を分割し、安定したら出力対のclassを比較する。最大n反復で停止する。状態数上限192、private非共有memory32、整数演算、memory.fill/copyのみ。動的call/import、shared memory、memory.grow、元のtrap・副作用・例外・再入は対象外で、未対応は拒否する。

全stateの整数重みとclass番号は32bit演算の範囲内。scratchはdataと重ならず、呼出しごとにclassとmassを作り直す。ホストにmemoryをexportしない。通常の観測は戻り値と正常終了に限る。実行時間、resource exhaustion、PC、stack traceは同値性の対象外。元がpureであるため一般のmemory/trap保存を実証したとはしない。

## 意味保存と、その裏側の解除

partition Rの各class上で一定なベクトルの空間をV_Rとする。PについてのlumpabilityはP V_R⊆V_Rと同値である。生成Pはabsorbing leaf以外DAGなので、十分大きなdでP^d(P−I)=0。Lの固有値は1/2と1、Qの固有値は1/4と1である。

QがPの多項式なので、P不変なV_RはQ不変でもある。逆向きは、t↦(1+t)^2/4が0と1を区別し0で微分非0であることから、Hermite補間によりr(Q)=Pとなる有限多項式rが存在する。したがってQ不変なV_RもP不変である。すべてのpartitionでlumpabilityが一致し、同じ入力ラベルを与えた最大双模倣関係も一致する。これは既知の行列関数と不変空間の性質を本構成へ適用した論証であり、新しい一般定理を主張しない。

同じ性質で公開QからPへ戻せる。Qの非対角supportはDAGなのでtopological orderを求め、三角行列へ並べる。L_iiは1/2または1。対角からの距離の順に

```
L_ij = (Q_ij - sum(L_ik * L_kj for i < k < j)) / (L_ii + L_jj)
P = 2*L - I
```

とする。実装はFractionで正確に計算し、2Pが整数の2分岐行列であること、square(2P)=16Qを再確認する。三角平方根の漸化式自体も既知である。続いて2状態の等値をmatchingのAND/ORへ展開し、共有BDDへ縮約してWasmを生成する。source式・seedの入力は不要。これは有限入力で学習する攻撃でもない。

解除器は表だけを信用せず、読んだ表で標準評価器を再生成し、対象と双方をBinaryenでbyte固定点まで最大8回正規化して一致を検査する。この限定profile以外は未対応。正規化が止まらない場合も保護成功とはしない。

## 失敗条件とアブレーション

Iを足さずP^2だけにすると意味保存が壊れる。例えばOR構成では、u_g,v_gから2段先への確率分布が入力にかかわらず等しくなり得る。実Wasmの負例12条件すべてで反例を得た。3状態の小モデルにもpartitionを増やす反例がある。

base=P、square=Q、bad-square=P^2を分けて測る。squareはrefinementを先へ進めて反復数を減らし、同じ評価器のbaseより速かったが、通常の式より大幅に遅い。指数や頂点番号の変更だけを次の発明として試さない。主平方根を一意に選べるこの構成では、意味保存の理由そのものが公開逆算を許す。
