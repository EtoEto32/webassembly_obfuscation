# 部分文字列をまたぐ変換と、その一般的な解除条件

## 対象と保護目標

対象は二項の重み付き文法を評価するWasm。保護したい情報は文法の簡潔な生成規則である。開始変数のparse countを返す。重みは R=Z/(2^32)、積は文字列の連結。整数の掛け算が可換でも、変数列の順序は交換しない。出力は剰余であり、ゼロを「不受理」と読み替えてはならない。

解析者は配布バイナリと方式を知り、実行、データ読取、命令の変更が可能。元文法、生成パラメータ、seed、対応表は渡さない。一般の意味理解ではなく、等価な二項文法へ戻すタスクを測る。任意の内部stateを問い合わせるAPIは存在しない。

## 生成規則

空語・単位生成を持たない系 X=A+Q(X) を考える。Aはterminal項、Qは二次同次の非可換多項式ベクトル。a≠0、b,c≠aを選び、m=X_b X_c とする。

Y=X+α e_a m、D(Y)=Y−α e_a Y_bY_c は相互逆。G(Y)=A+Q(D(Y))+α e_a Y_bY_c とおく。X=F(X)とY=G(Y)は一対一に対応する。a≠0だからX_0=Y_0であり、返却時のdecoderは不要。

chartでの関係は、各i<jについて

`Y_a[i,j] = X_a[i,j] + α Σ(i<k<j) X_b[i,k] X_c[k,j]`。

同じセル内だけの座標変換とは異なる。元の規則をただ呼ぶcodec関数は生成しない。展開・同類項整理して最大四次の規則を作り、共通suffixを補助変数にして二項化する。この二項化自体は既知の処理である。

```text
read and exactly validate the Wasm evaluator profile
F := terminal terms + binary rules from its active data segments
choose a != start and b,c != a
replace each occurrence of variable a by (a - alpha * b c)
add alpha * b c to equation a
collect coefficients modulo 2^32
binarize each long right-hand side using shared suffix variables
emit a Wasm evaluator with the transformed rule table
```

右辺の変数項は全て次数2以上。各非空文字列の係数は真に短い部分文字列だけに依存するので、長さについての帰納法で解の存在と一意性が得られる。補助変数の二項化も連結の結合則と同じ帰納法で一致する。アルゴリズム上の意味保存論証であり、生成Wasm全体を証明支援系で検証したという主張ではない。

## 任意の重みにも適用できる解除

最初の0/1規則向け攻撃は、G_aにあるbc項の係数が元係数にαを加えた値になることを使った。実験後、0/1という仮定を除くため次を導いた。

L(Q)を「Qの単項式のaを一箇所ずつbcに置き換えた項の和」、D(Q)を「Q内のaa項をbcbcへ置き換えた項」とする。変換後の次数別成分は

`G2 = Q + α e_a bc`, `G3 = −α L(Q)`, `G4 = α² D(Q)`。

L(e_a bc)=0なのでL(Q)=L(G2)が公開係数から分かる。未知βに対し **G3+β L(G2)=0** を解けばよい。各係数は一変数の線形合同式で、奇数による除算だけで解ける。解集合の交差はβ=r mod 2^kとなる。

**単一shearから生成された系なら、その最小剰余rを一つ試せば十分である。** 真のαとの差をδ=β−αとするとδL(Q)=0。各出力座標で、語abcの係数はQのaa係数そのものである。b,c≠aのため他の二次項からこの語は現れない。よってδQ_aa=0であり、δ²D(Q)=0も従う。逆置換後の四次成分はδ²D(Q)、三次成分はδL(Q)なので、両方とも消える。βがαと違っても、返却する開始級数と等価な二項文法を得る。

これは係数が偶数の場合も成り立つ。αを完全に特定する必要はない。実装では証明の適用を仮定して結果を採用せず、逆置換の全係数と再変換の一致を検査する。

二項化された補助変数の境界dはbinaryに保存しない。攻撃器はd=2..Nを試し、suffixが単一・重み1の二項定義として展開可能なものだけを採る。a,b,cも列挙する。生成seedや元のa,b,cを読む処理はない。回復候補のうち規則数が少ないものを選ぶ。元文法の変数名・同一の重みを取り戻すことは必要条件にしない。

この証明は、一般の非線形変換、shearの任意合成、epsilon規則、出力自体を変更する変換、文法を隠す別の評価器には適用しない。それらの困難性も主張しない。

## Wasmの契約

入力は `run(low:i32,high:i32,length:i32)->i32`。2bitずつ0..3の記号を格納し、lengthは0..32。空入力は0。未使用の上位bitは無視する。範囲外length・alphabet外記号は、chartを書き換える前にtrapする。memoryはprivate、固定長、非共有。import、別export、memory.grow、浮動小数点、threads、一般のC/Rust由来Wasmは非対応。

読み取ったheaderを信用するだけではなく、全関数・export・memory・dataを再生成し、WABT folded ASTをrawまたは同じBinaryen133 O3結果と完全照合する。したがって、これは一般のWasm parser/compilerではなく、限定profileの実バイナリ変換である。
