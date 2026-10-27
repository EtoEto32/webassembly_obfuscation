# 重なる状態対と到達不能表領域：事前計画

2026-10-19。前回resource-triggerは実装・実測・144本再現と監査を完了した進捗であり、単なる待機ではない。公開結線が正規化手順を与える失敗を踏まえ、今回はメモリ内の表の意味を、複数値の整合関係に依存させる。

検討した方向：(1)fieldのbit-plane配置変更、(2)共通の冗長tagを保つ条件付きtable、(3)隣接する本来の状態を重ねて表現する更新table。(1)は既存bit packing/array restructuringに近い。(2)はtagを一つに固定して元と等価な実行を選べるため、今回の主案から外した。(3)では重なりが別の実データを保持し、tagのようには捨てられない。これらを新発明3件とは数えない。独立した新規性は未確認。

状態は2bit cellの環。c[i]を更新するとき、両側pair E[i-1](c[i-1],c[i])とE[i](c[i],c[i+1])を一つの256-entry tableへ入力し、二つの更新pairを一つのbyteで返す。整合する入力は64通り、残り192通りは到達しない。そこをrandom permutationで埋め、更新後のpair encodingも変えれば、各tableを全域の代数として読む解析を妨げられるかを検査する。各更新はcenterについて全単射とし、全初期状態を受理する。暗号化や暗号安全性は提案しない。

Wasmではbyte-addressable private linear memoryのload8_u、固定幅shift/bitwise、i64入出力で実装する。原理は他ISAにも移植でき、Wasm固有原理とは主張しない。入力は実.wasmの明示的なcell更新profile。一般プログラムを受理するとは言わない。

比較は元演算、各cell単独の符号化table、重なるpairで無効領域0、無効領域random、さらに各更新後の再符号化。通常O3後も評価する。課題は、重なった16値状態から独立な4値cellと64-entry更新則を回復すること。元の演算子名そのものの回復とは区別する。

最大の反証候補：現在のpair対応が分かると有効64入力を列挙できる。出力二つの共起グラフは、共有center値ごとの4個のK4,4になる可能性がある。連結成分から共通centerを回復し、隣接値の保存から新しいpair対応を伝播できれば、無効領域の埋込みとencoding変更を探索なしに除ける。この攻撃を公開binaryだけを入力として実装する。

正当性は境界/random、縮小全状態、誤った有効table entryの負例、独立oracle、WABT/Binaryenを使用する。解析時間はreaderと本体を分離し、回復成功率だけで棄却しない。先行white-box encodings、invalid entries、common-information support graphとの相違を確認する。特許・論文上の新規性も費用上の優位性も、実験前には未確立。
