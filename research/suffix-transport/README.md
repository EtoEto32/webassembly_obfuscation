# suffix受理条件のSIMD輸送：実Wasm試作と双対回復

2026-10-18。**実装・測定は完了したが、特許を目指す主方式には採用しない。** 未処理の入力に関する受理条件を逆向きに運ぶ構成を試した。実行時のベクトル状態は最大1,376種類だったが、方式既知の解析は出力側のrowを進めることで元の16状態を回復した。回復成功だけを棄却理由にせず、既知構成との差と実行・解析双方の費用を判断材料にした。

[事前計画](plan.md)、[先行技術と差分](prior-art.md)、[日本語草稿](paper-note.md)。研究全体の新規で有効な主方式は未確立である。

## 変換と保護目標

入力は最大16状態、2文字のDFA走査を含む実 `.wasm`。普通の状態更新 `q = delta(q,a)` を、suffixの受理条件 `v[q]` の更新 `v'[q] = v[delta(q,a)]` に変更する。入力byteを末尾から読み、16個の0/255 byteを `i8x16.swizzle` で同時更新する。初期値は受理集合F、最後の出力は初期状態q0に対応するlaneである。

混合版はGF(2)上の可逆行列Lを生成し、`z=L v` を保持する。`A_a[q,delta(q,a)]=1` とすると、更新は `z=B_a z`, `B_a=L A_a L^-1`、初期値は `L F`、出力は `ell z`, `ell=e0^T L^-1`。行列積は生成時に合成し、実行時にvへ戻す命令は挿入しない。行列の各列をswizzleによる複製、AND mask、XORで実装する。これは古典的な基底変換であり、それ自体を発明としない。

保護課題は、バイナリから小さな等価状態機械とそのWasm実装を回復する費用を増やすこと。秘密の外部oracle・鍵・暗号学的解除不能性を仮定しない。解析者は変換算法を知り、定数・命令・実行状態を読める。今回の回復器はバイナリだけを受け取り、設計モデル・L・seedを受け取らない。

## 対象範囲と意味保存

- `run(pointer:i32,length:i32)->i32` と固定1ページの非共有memoryだけをexportする単一関数module。各byteの最下位bitを文字とする。
- [prototype.py](prototype.py)の `plain()` が生成する厳密なテンプレートに限る。入力から遷移を抽出した後、同じテンプレートを再コンパイルして正規化WATの構文木が一致することを確認する。一般のC/Rust出力や任意ループを処理する変換器ではない。
- import、global、追加export、データsegment、共有memory、書込み等の副作用は対象外。ホストは呼出し間にmemoryを書き換えられるが、呼出し中に変更しない。
- uint32のpointer加算、length、境界外loadを扱う。空入力はpointerによらずloadしない。読むアドレスの集合が同じなので、正常値、bounds trapの有無、memory内容は保存する。実行時間、fuel、資源枯渇、trapに至る最初のアドレスの順序は同値性の対象外。

長さ0のsuffixではv=F。既処理suffixの受理条件がvなら、文字aを前置した条件は `A_a v` である。この帰納関係から最終値が元のDFAの受理値に一致する。混合版は各段階で `z=L v` を保つ。この算法上の論拠と有限の実行検査は区別し、任意のWasmプログラムについての形式検証済み同値性は主張しない。

## 適応的回復

回復器は制御骨格、1byteずつの逆向きload、文字の `&1`、位置に依存しない更新、最終観測の依存先を検査する。その上で16laneを独立なGF(2)記号として1stepを評価し、B、初期値、ellを抽出する。非線形なAND/OR、非正規mask、未知の制御は拒否する。O3で生成される一時vector localにも対応する。

次にrowの軌道を探索する。

```
queue = [ell]; state_number[ell] = 0
while queue is not empty:
    r = pop(queue)
    accepting[r] = parity(r & initial)
    for a in {0,1}:
        next = r * B[a]
        intern next and record transition(r,a,next)
minimize and canonically number the resulting DFA
emit an ordinary forward scanner as .wasm
```

`r=e_q^T L^-1` なら `r B_a=e_delta(q,a)^T L^-1`。したがって生成されたプログラムでは、row軌道は元の到達状態数以下で閉じる。逆向きcolumnの状態数が大きくても、それを全列挙する必要はない。この有限row軌道探索を、一般の重み付きオートマトンに対する線形空間の基底計算と混同しない。汎用のWasm同値性判定器でもない。

## 実験と結果

4/8/16状態の巡回型と、到達性・最小性を確認した固定seedの一般型の計6例。元、suffix、混合suffixをraw/O2/O3で比較した。54本と回復54本で計108本。最適化器はBinaryen 133。小さい例でもvectorは16laneで、未使用遷移を状態0へ埋める。

主実験：[suffix-transport-v1](../../results/invention-20261018/suffix-transport-v1/comparison.md)。追加監査付きの全再現：[suffix-transport-replay-v2](../../results/invention-20261018/suffix-transport-replay-v2/audit.json)。再現は主108バイナリの集合・SHA-256が全一致した。

|項目|結果|
|---|---|
|WABT/Nodeの主バイナリvalidation|108/108成功|
|Nodeによる値・trap・全memory比較|249,804呼出し、不一致0、うち540 bounds trap|
|WABT interpreter|432呼出し、不一致0|
|方式既知の回復|54/54成功、未対応/クラッシュ/時間上限/解析失敗は主条件で各0|
|元と回復DFAの同値性|54/54、積状態の全探索と最小DFAの正規番号表現が一致|
|生成した行列とバイナリ抽出結果|再現で保護36条件の更新・初期値・出力・共役関係を検査、不一致0|
|逆向きベクトル状態数|cycle4:6、general4:7、cycle8:10、general8:55、cycle16:16、general16:1,376|
|回復後の最小状態数|それぞれ4/4/8/8/16/16|

Nodeは長さ0〜10の二値全2,047語、固定seedで作る256個のbyte列、10個のpointer/length境界を各バイナリへ入力する。元・変換・回復それぞれを独立のDFA参照計算と比較し、毎回65,536byte全体を検査する。WABTは同じ108本にデータと0/1/3/8byteの呼出しwrapperを追加して比較した。通常の返り値に関する全語の根拠は抽出したDFAの同値性であり、任意のエンジン実装の証明ではない。

誤変換の対照ではXORをORへ置き換えた有効なWasmが2,303入力中1,183件で異なり、線形解析も拒否した。strideを1から2へ変えた対照は解析が拒否し、停止しない可能性があるため実行しなかった。再現ではsourceにmemory書込みを加え、変換器が拒否し出力バイナリを作らないことも確認した。[対照結果](../../results/invention-20261018/suffix-transport-replay-v2/negative-analysis.json)

## 費用とアブレーション

主実験O3、512byte/呼出し。3 fresh processそれぞれの中央値から中央値を算出。全例・ばらつきは[比較表](../../results/invention-20261018/suffix-transport-v1/comparison.md)、raw/O2も含む値は[summary.json](../../results/invention-20261018/suffix-transport-v1/summary.json)。

|general16|bytes|実行ns/call|回復解析ms|
|---|---:|---:|---:|
|元|129|436.0|1.805|
|suffix、混合なし|170|1,007.5|0.590|
|suffix、混合あり|1,171|6,099.0|3.738|

6例の混合版は実行時間が元の11.91〜13.99倍、解析時間が1.74〜2.12倍だった。**解析側の元プログラム処理は16状態×2文字の命令解釈であり、定数表を直接読む最速解析ではない。** これらは実装依存の観測値で、最適解析の下界でも人間の作業時間でもない。無混合化すると解析・実行とも安くなる。混合の効果は認めるが、この構成では大きな実行負荷に対する保護上の利点が弱い。

各主条件を3 fresh process、長さ32/512、各200回warmup、9反復×200呼出し。計162 process。固定seedで順序をシャッフルし、JS呼出し・offset生成も計時に含めた。CPU固定・JIT tier固定はしていない。独立な再現でも実行倍率は11.90〜13.83倍だった。32byteの測定にはprocess間の大きなばらつきがある。

線形memoryは全条件65,536byte。主実験のNode process最大RSSは40,128〜41,132 KiBで、Node/V8の費用を含み、Wasm単体のメモリ費用を分離しない。12件の変換時間は117.35〜122.76 msで、WABT起動・テンプレート照合・生成・validationを含む。1条件1回のため安定した時間分布の主張はしない。解析時間は1回warmup後の9回で、WABTによるvalidation/WAT化/parseの1回分26.99〜33.23 msを除いている。回復バイナリの生成・validationも別。解析器開発時間・ピークメモリは測っていない。

## 再現

リポジトリrootから、未使用の出力先を指定する。既存の結果ディレクトリは上書きしない。

```powershell
python research/suffix-transport/run.py results/invention-20261018/suffix-transport-repro --compare results/invention-20261018/suffix-transport-v1
```

単独変換・回復例（出力ディレクトリ名は適宜変更）：

```powershell
python research/suffix-transport/prototype.py mixed results/invention-20261018/suffix-transport-v1/general16.plain.raw.wasm results/invention-20261018/suffix-demo/encoded.wasm --seed 20261018
python research/suffix-transport/prototype.py recover results/invention-20261018/suffix-demo/encoded.wasm results/invention-20261018/suffix-demo/recovered.wasm
```

環境はPython 3.9.0、Node v24.15.0 / V8 13.6.233.17-node.48、WABT 1.0.42、Binaryen 133、Windows 10 build 26100、Intel Core i9-11900K 3.50GHz。Pythonの追加packageは不要。NodeはPATH上、WABTは `.tools/wabt-1.0.42/bin`、Binaryenは `.tools/binaryen-version_133/bin` を使う。共通パーサ/tool呼出しは [connectivity-elimination/prototype.py](../connectivity-elimination/prototype.py) をimportする。必要な公式配布は [WABT](https://github.com/WebAssembly/wabt/releases)、[Binaryen](https://github.com/WebAssembly/binaryen/releases)、[Node.js](https://nodejs.org/en/download/archive)。固定版の実行ファイルが既にある環境で測定した。

結果内の `sources/` と `audit.json` は実行時コードのsnapshot/hash。snapshotは来歴確認用で、単独配置で動くpackageではない。再現コマンドはリポジトリ内のソースを使う。smoke-v1/v2には最適化後のif深度・一時localへの対応不足を直した過程があり、これらを保護の成功件数に含めない。

保存後の件数・source hash・binary hash・再現一致・文書リンクを [audit_saved_results.py](audit_saved_results.py) で別途検査した。[監査結果](../../results/invention-20261018/suffix-transport-replay-v2/verification-audit.json)。これは保存証拠の整合性検査であり、別の正当性実行試験や新規性の証明ではない。

## 判断と限界

新しい数学原理を必須とはしていない。しかし現構成の逆向き受理条件、行列表現、共役、双対回復は既知の枠組みに収まり、Wasmの実装上の差だけで独立した新規性を確定できない。測定は6個の合成scanner、各1混合seed、1機械に限る。著者WASMixer・NotDec・StackSight本体との比較、同じ実行負荷の他方式、実アプリケーションは未評価である。

したがって「全件回復されたから難読化失敗」ではなく、**現時点の具体的差分と費用対効果では主候補に進めない**と判断する。すべての関係表現・逆向き実行が無効だという結論でもない。次の案では、実行状態の増加を保護根拠にする前に、観測側の更新が小さな集合・線形空間に閉じるかを検査する。
