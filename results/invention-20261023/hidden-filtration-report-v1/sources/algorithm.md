# 有限回で不要な初期状態を除く更新系

実装対象はi32のAND/XOR/OR/定数rotateだけからなる単一pure関数。実WasmをWABTで検証・読取りし、式DAGを作る。最大24節点、1–32入力、結果1個。import、元のmemory、global、table、trapを起こす演算、一般CFGには未対応。private scratch最大8ページ、bulk memoryを使う。暗号化や秘密鍵への依存はない。

## 生成

1. 各DAG節点iに状態s_iを置く。F_x(s)_iを、その節点の演算を**更新前**の前駆状態に適用する式とする。入力xを直接読む節点もある。
2. 出力節点を最後に置く。最長DAG深さをDとする。
3. 入力だけを読む節点をtargetとし、targetでも出力でもない二つの節点a,bを選ぶ。N(s)_j=s_j XOR (s_a AND s_b) とする。controlsを書き換えないのでNは自己逆。
4. 出力座標を変えない可逆word-XOR行列Tを生成する。E=T∘N。無混合対照はE=I、線形対照はN=I。
5. H_x=E∘F_x∘E^-1をBoolean ANFとして展開・簡約する。配布するのはHとD、サイズ、および共通評価器。元DAG、E、E^-1、seedは含めない。
6. 関数呼出しごとにxを書き、HをD回同時更新して最後の座標を返す。初期stateをresetする必要はない。

```text
F, D = synchronous_map(parse_pure_i32_DAG(input_wasm))
T, N = choose_output_preserving_maps(F)
H = expand_ANF(T(N(F(N(T_inverse(y))))))
emit_wasm(H, D):
    write_inputs(x)
    repeat D times:
        new[:] = H_x(old[:])
        old[:] = new[:]
    return old[output]
```

## 意味保存の理由と限界

深さkの節点はFをk回適用すると、初期stateによらず正しい値になる。帰納法によりF_x^Dは元DAGの正しい全節点値への定数写像。Eが全単射なのでH_x^D=E∘F_x^D∘E^-1。最後の座標をEが変えないため結果は元関数と等しい。入力が変わっても、新しい入力を固定してD回実行すれば同じ論証が成り立つ。

これは限定言語の構成についての数学的説明。任意Wasmの意味保存、ホスト側の資源不足、一般的なmemory副作用まで証明するものではない。有限テストだけから全入力等価を主張しない。別途、回復済みpureコードの64bit入力全体をBitVecモデルでSMT照合した。

## 検査したrank条件

Hのstateを含む各単項式について、出力への係数ベクトルを集める。この行列がd次元でfull rankなら、非零な一定word-XOR観測lについてlHが入力だけの関数になることはない。bitごとに展開すれば32d次元の同じ条件を検査できる。これは一段の線形観測に対する条件だけで、非線形観測や適応解析の困難さを意味しない。

mix8非線形版はword rank 8/8でもbit rank 224/256。select10は320/320、chain12は384/384。word条件とbit条件を同一視しない。

## 二次観測による回復

公開状態yの一次項と二次項を候補Φにする。各P∈span ΦについてP(H(y,x))を展開する。既知観測と入力のrotate、XOR、二項ANDで生成する代数Aを作り、pullbackをAで割った商空間のnullspaceを求める。nullspaceの各関係は新しい計算可能な観測と、その値を作るacyclic式を与える。出力座標が既知観測のspanに入ればWasmを生成する。

この実装は近似標本回帰ではなく、Boolean多項式の完全一致による有限辞書解析。観測の持上げや線形代数自体を発明とはしない。辞書の回転集合は公開Hに現れるものと0に制限。原理上の万能回復器ではなく、上限到達・辞書不足・未対応を区別する。

本構成のE^-1は二次である。そのため非線形な座標対応が消えても、低次数の共同観測に依存構造が残る。今回の全18条件で実際に回復した。単に非線形層を増やす変更は別原理の発明と数えない。
