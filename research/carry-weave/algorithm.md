# マスク分割とcarry-saveの再結合

## 課題と対象

保護課題は、整数式の総和を構成する項の回復。解析者は配布Wasmと方式を知り、全命令・定数を読める。元Wasm、生成seed、正解の項一覧は解析へ渡さない。秘密鍵や暗号的な解除不能性は仮定しない。

入力は`run(i32,i32,i32)->i32`だけをexportする実Wasm。pureな直線整数式、i32 local、定数、add/sub/mul/and/or/xor、shift/rotateを受理する。返り値のaddを展開した4–128項が対象。各項の内部は他の許可整数演算を含められる。moduleのmemory・import・global・table、追加関数、追加export、trapを起こし得るdiv/rem、float、一般CFGは拒否する。特定の係数templateとの照合ではないが、任意のC/Rustモジュールを処理する一般passではない。custom/debug情報の保持も契約外。

Wasmのi32 wrapにより、加算順を変更しても同じmod 2^32の結果になる。SIMDの各i32 laneにも同じ意味を使う。これはWasmの明確な整数意味とSIMDを利用するが、数学原理自体は他ISAにも適用できる。

## 変換

元の項tを固定mask mで`u=t&m`、`v=t&~m`へ分ける。両者は重なるbitを持たず、u+v=tである。全項の分割片を一緒に並べ替え、4個ずつv128へ詰める。最後の組は0で埋める。

三つのvector a,b,dを、次の二つへ圧縮する。

```
x = a XOR b
s = x XOR d
c = ((a AND b) OR (x AND d)) << 1
```

各laneで`s+c=a+b+d (mod 2^32)`。bitwise演算はbit間のcarry伝播を行わず、最後に二つを加算するときに通常の加算へ戻る。

```text
read and validate input.wasm
convert allowed straight-line instructions to a shared expression DAG
flatten result additions into terms
evaluate each term once into an i32 local
for each term:
    choose mask and create complementary fragments
shuffle all fragments and pack four into each vector
while more than two vectors remain:
    choose three vectors
    replace them by sum and shifted-carry vectors
add remaining vectors
add their four lanes and return the scalar result
emit and validate output.wasm
```

主実験ではmask・並べ方ともseed37。原項係数は別seedで生成する。`plain`はscalar総和、`packed`は分割なしのSIMD加算、`csa`は分割なしの圧縮木、`splitadd`は分割・並べ替え後に通常SIMD加算、`splitcsa`が分割・並べ替え・圧縮。maskと選択順は秘密ではない。今回はランダムな配置規則であり、解析費用を最適化する新しいplannerが完成したとは主張しない。

## 意味保存

全vectorの全laneの和を不変量とする。分割は一項の和を保ち、並べ替え・packingは全体の和を保つ。3→2圧縮もlaneごとの和を保ち、零のpaddingは和を変えない。したがって最後の水平加算は元の総和と一致する。元項はtotalで副作用がないため、再利用・評価順変更を許せる。shift量はWasmの通常のmod32規則に従う。

この代数的説明は生成規則のモデルに対するもの。Python readerや変換器、WABT、Binaryen、V8まで含めた機械証明ではない。資源不足・実行時間・内部localの観測を保存するとはしない。memoryは元も変換後も持たない。

## 方式既知の回復

WATからlocal/stackを解決し、v128を4つの32bit式へ持ち上げる。出力の加算を多重集合frontierへ展開する。和sとcarry cがfrontierに揃った圧縮器を見つけたら、両者を取り除きa,b,dを追加する。これを繰り返す。zero-paddingにより2入力へ退化した場合は`(a XOR b)+2(a AND b)=a+b`も用いる。

残った`term&m`と`term&~m`をtermへ結合し、総和を再生成する。XORの結合・相殺、可換演算の順序、定数減算を正規化し、O3前後を同じ課題として採点する。元の加算の括弧付けを復元する必要はない。

**今回のforestに対する反証**：各圧縮器の両出力がさらに圧縮されるか最終総和へ入り、全て同じ重み1で観測されるなら、出力側の圧縮器から逆順に保存則を適用できる。分割片の距離やlaneの配置は、この逆順の存在を変えない。したがって全入力の探索やbitvector SMTは必須ではない。本実装は候補を反復走査するため最悪二次的な費用もあり得るが、依存情報を持つ逆順の処理では各圧縮器を一度ずつ扱える。この初等的な観察を新定理とは呼ばない。

回復器は対応命令と圧縮式の形に依存する。未知の命令は拒否し、認識できない圧縮式が残った場合は等価な式をそのまま出力し得る。CLIの終了成功と、元項を回復したという成功は別であり、実験では項の多重集合一致も検査する。
