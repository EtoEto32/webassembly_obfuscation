# 生存区間と型衝突を使う配置、および回復

## 保護の対象と攻撃者

正当な配布ソフトウェアのprivate working memoryを対象にする。攻撃者は全binaryと生成方式を知り、修正・最適化・実行できる。秘密鍵、非公開decoder、信頼できるhostを仮定しない。具体的な解析課題は、アドレスを固定した型付きセルとして解釈しにくい表現から、型の確定した一時値と分岐ごとの代入へ戻すこと。ソースの名前・コメントまで回復する課題ではない。

## 生成

1. WABTで入力をvalidateし、folded WATを解析する。[事前計画](plan.md)のmodule/profile外を拒否する。
2. 全load/storeを、定数の実効アドレスと幅によるセルとして同定する。ソースで重なる異なるセルは拒否する。演算で参照するセル集合を求める。
3. 構造化ifを逆向きに辿る。store dでは `live_before=(live_after-{d}) ∪ uses(value)`。ifでは両枝の入口と条件のusesの和集合を使う。入口liveが空でなければ初期値依存として拒否する。
4. 同時にliveなセル同士、およびstore先とその直後にliveな他セルの間に干渉辺を張る。後者を省くとdead storeが必要な値を壊し得る。
5. 干渉次数の降順、幅の降順、元アドレス順にセルを置く。干渉相手とはbyte区間を重ねない。first-fit対照は自然境界に整列する最初の位置を選ぶ。conflictは作業範囲の末端を小さくすることを第一目的、異なる幅との重複byte数を大きくすることを第二目的にし、残りを小さいアドレスで決める。
6. アドレスとalignment hintだけを書き換える。conflictでは非整列位置も許す。全配置は1page内とし、出力を再validateする。

```
live = backward_dataflow(structured_body)
G = interference(live, writes)
for cell in degree_width_order(G):
    feasible = positions_inside_page_disjoint_from_assigned_neighbors(cell)
    position[cell] = argmin(feasible, (footprint, -cross_width_overlap, address))
rewrite_each_static_memory_address(position)
```

これは最適配置を保証する算法ではなくgreedy heuristic。正当性の必要十分な最小干渉グラフを保証するものでもない。分岐入口の和集合による過剰な干渉は安全性を保つが配置自由度を狭める。

## 意味保存の議論

各実行点で、これから読み取る元セルの値が対応する物理区間にあることを不変条件にする。入口には読み継ぐセルがなく、すべての読みには同じ呼出し中の先行storeがある。storeは他のliveセルと重ならず、書込値の評価は書込み前に行う。分岐は元と同じ条件と命令順を使うため、各枝と合流に対して帰納できる。すべてのアクセスは範囲内で、整数演算はWasmの固定幅意味論のまま。private memoryの返却時内容は外部観測に含まれない。

この議論は対象profile内の規則についてのもので、任意Wasmの同値性証明ではない。memoryのexport、共有、外部call、動的アドレス、永続状態の入口読み、trapする命令へそのまま拡張できない。テストの成功は全入力の機械的証明ではない。

## 適応的回復

解析者は元レイアウトもJSONも使わない。実バイナリを解析し、最適化後のlocal.tee、値を返すif、i64.load32_u/sを、評価順を保存する一時local列へ変換する。先行するlocal.getの後で同じlocalをteeが更新しても、先行値を取り違えないようsnapshotする。

store値を新しいtyped localに保存し、各byteへ `(local番号, byte位置, 幅, 型)` を記録する。loadの全byteが同じ全幅定義を指す場合、local.getへ置き換える。分岐で異なる定義が合流する場合は、新しいtyped localへ両枝の末尾で代入する。経路の組合せは列挙しない。部分byteが別々の定義を持つ一般的なloadの再合成は今回未対応で、成功に数えず拒否する。

対象の3kernelでは全18バイナリが回復した。diamondは16個の二分岐を持つが、回復側の合流localは16個で済んだ。入力の全65,536パターンを正当性検査に使ったことと、解析器が経路列挙したことを混同しない。
