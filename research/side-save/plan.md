# 現memoryを副情報とする共有退避の生成

2026-10-23、実装前。新規性未確立の補助アルゴリズム候補。prefix-repairは入口情報だけから修復し、loss-flagは表現Bを制限して退避を0にした。今回はBを固定したまま、全trap prefixの現memoryを使って共有退避次元を減らす。難読化の強度増は仮定しない。既知のcoded side-information/index codingと最も近く、その新名称への置換を発明とは呼ばない。

P_jはnative copy prefix、D_j=B P_j B^-1+P_j。入口退避z=V y0と現memory P_j y0からD_j y0を出す条件はrow(D_j)⊆row(P_j)+row(V)。row(P_j)が単調に縮むことを使い、最後のprefixから逆順に、P_jと既選択Vで表せないD_j行を追加する。各prefixの修復係数を合同式として検査してからWasmを出力する。

小幅で全subspaceを列挙し、greedyの保存次元が最小かを反証する。全般の最小性は交換論証を別記し、機械検査範囲を区別する。比較は同じB、同じcopy列のplain/既存basis/side。生成規則の保存量、temp数、サイズ、時間、trap後の状態、適応回復を実測する。保存量を実CPU stack量と混同しない。減量できても既知構成と同じ回復が残れば、強い新難読化の成功とは扱わない。
