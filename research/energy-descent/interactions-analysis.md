# 違反同士の相互作用を合成する最終改良

2026-10-22。**このenergy方向は主方式に採用しない。** 独立した違反の和を符号付き相互作用へ変え、二つ以下の引数で局所最小を選べない例を生成した。それでも前回の変数消去本体を未変更で適用でき、実行費用が大きかった。初版、全体収束への変更、今回の相互作用という3設計段階を検査したため、係数や小例を増す継続は行わない。研究全体の目標は未達で継続する。

実装：[全状態制約合成](interactions-screen.py)、[実binary変換・回復](interactions.py)、[実験](interactions-run.py)、[監査・集計](interactions-audit.py)。初期版の[結果](../../results/invention-20261022/energy-interactions-audit-v1/facts.json)と、修正版の[結果](../../results/invention-20261022/energy-interactions-robust-audit-v1/facts.json)・[比較表](../../results/invention-20261022/energy-interactions-robust-audit-v1/comparison.md)を分けて保存した。同じ3回路の修正比較であり、6つの独立ベンチマークとは数えない。

最終の[検証記録](../../results/invention-20261022/energy-interactions-verification-v1.json)は8directory・616ファイルhash、実測source一致、構文、集計、selector条件と資料リンクを確認した。性能session18438/26502はいずれもexit0で終了済み。

## このturnの方向選択

前turnは全体収束への改良を実装・検証したprogress。今回はまずWasmメモリの動的再配置を検討したが、アクセス時のsplay等は既存の保護方式に明記されていた。共有セルから値を取り出す一般案もBloomier系の既知構成に近かったため、そのまま新案に数えなかった。新しいWasm固有方式が得られたとは主張しない。その後、前案の独立した違反の和を崩す具体的な追加仮説を検査した。以下は実行後の設計・判断記録であり、事前登録と偽らない。生成制約は各screenのsource snapshotへ実行前に固定されている。

## 合成するもの

元DAGの違反bitをe_i=z_i XOR f_i(x,z_<i)として、

```
E = sum_i w_i e_i + sum_{i<j} c_ij e_i e_j
1 <= w_i <= 16,  -16 <= c_ij <= 16
```

と置く。少なくとも一つのcを負にする。全Boolean入力と全内部状態を列挙し、元の状態ではE=0、他ではE>0かつ少なくとも一つの1bit反転でEが下がる、という線形不等式の選言を生成する。Z3 Optimizeで係数絶対値和を小さくする。反例を反復追加する前版のCEGISとは異なり、このscreenは最初から全状態を制約に含む。

実binary入力は[元の限定Boolean DAG profile](algorithm.md)。今回の合成上限をI+n<=8、n<=6とし、それより大きい入力は拒否する。一般のWasmプログラムや実アプリへの適用率は未検査。合成結果の違反多項式を展開・集約し、元ゲート区切り、係数のw/c区切り、元の順序をbinaryへ保存しない。座標置換・補数を適用したaggregateを、前版と同じWasm i32/i64評価器で実行する。

正当性は非負整数Eの厳密減少による。今回はW=sum(w)ではなく、B=sum(w)+sum(max(c,0))が全状態の上界になる。採用反転は高々B、停止確認を含め高々B+1 sweeps。入力bitを固定し、誤った局所最小がないので停止時にはE=0。DAGの元状態が唯一の零点になることを全状態制約で要求する。係数絶対値和によるi64無overflowとdata boundsの検査は前版を継承する。

## 初期合成条件の欠陥と修正

最初は各座標の規則q=[E(z_j=1)<E(z_j=0)]が少なくとも3変数に依存するよう要求した。3例で成立したが、これは同値energyの時に常に0を選ぶ規則の複雑さを測っていた。差分D=0ならどちらを選んでも最小値なので、その自由を使うと初期版の多くの座標に2引数の選択規則が残った。初期版で「簡単な局所規則を排除した」とは結論しない。

修正版は、各座標jと各2引数集合Sについて、Sへの値が同じなのに一方でD>0、他方でD<0となる文脈が存在することを要求する。これにより、同値energyの選択を自由にしてもSだけの最小化規則は存在しない。2引数集合を全て検査すれば、それ以下の引数集合も排除される。監査は合成器のBool判定を使い回さず、各候補引数集合について厳密な符号要求が衝突するかを全列挙した。

修正版の初期局所規則は、fork/chainの全座標で最低5引数、orderedで4または5引数を要した。したがって、この小領域では「最初の状態から2入力ゲートを一つずつ読む」解析を排除できた。ただし、これは解析一般の困難性や指数時間下界ではない。

## 回復と、公開binaryだけによる前提検査

前版の`relaxed.eliminate`を変更せず使用した。各座標のDから最小化規則を作り、代入して変数を消す。修正版でも項数はforkで36→24→9→3→0、chainで41→25→10→5→0、orderedで46→22→9→3→0となり、全12条件を通常のDAGへ戻せた。消去後には局所規則が再び簡単になるため、最初の最小化規則の引数数だけでは防げない。

今回はsourceに頼らない前提検査も追加した。実行器のraw/O3再生成byte一致に加え、公開aggregateから次の反例をZ3で探す。

1. E<0となる状態。
2. E>0なのに1bit反転で下がらない状態。
3. 同じ入力で、E=0だが公開出力が異なる二つの内部状態。

全てunsatで、正確な消去の残りが恒等的0なら、反復実行と回復した最小化状態の公開出力が一致する。unknown/timeoutは回復成功としない。この追加は、生成器が正しい表を作ったという前提を減らすためのもの。前版の測定対象は生成条件を別途検証済みであり、以前の実測に誤答が見つかったという意味ではない。

相互作用を除いたforkの表は同じ既知実行器へ格納できるが、誤局所最小があり、新しい公開証明検査が拒否した。chain/orderedでは相互作用除去後も正当性検査は通った。アブレーションをすべて失敗例として数えない。

## 実測の範囲

対象は各2bit入力・4内部gateの3合成回路。意味のある外部入力は各4個しかないため、公開I/Oの4問い合わせでも出力表を作れる。今回の主回復器は問い合わせを使わないが、このコーパスで実用的保護を示せないことは最初から明確である。これは相互作用の成立条件を調べるscreenであり、難しい保護対象を選んだ実アプリ評価ではない。

初期版と修正版のそれぞれで、以下を実施した。同じ入力領域・対照の重複を含むので独立例数を合算しない。

- 30主条件（byte異なる24本）、61,860通常呼出し、全初期状態probe384呼出し、不一致0。
- raw/O3・優越/相互作用の12条件すべて回復。36個の公開前提検査、48消去段の最小化検査、12回復出力のsourceとのBoolean同値検査を確認。
- 30本のbyte再生成一致、別WABTで120呼出し一致。
- 45 fresh process×7batch=315batch、warmup16,384、20ms calibration目標、10ms未満batch0。CPU affinity/周波数は固定なし。性能測定と重い監査は同時実行していない。

修正版のO3、ns/call中央値：

|回路|元版|加算のみの優越対照|符号付き相互作用|相互作用からの回復|
|---|---:|---:|---:|---:|
|fork|1.026|128.139|215.645|0.987|
|chain|1.023|133.674|244.136|1.080|
|ordered|1.159|98.242|283.713|1.353|

相互作用/元版は約210–245、相互作用/優越対照は約1.68–2.89。各比はこの極小カーネルの値でアプリ全体の遅延ではない。元版と回復版の1ns付近の小差を性能優位と解釈しない。private memoryは保護版65,536B、元/回復0B。最適化後サイズは比較表に記録。Node process全体maxRSSは修正版37,752–38,276KiB。

修正版の回復単発総時間は約85.2–148.8msで、公開証明検査約25.1–75.6ms、消去本体約0.35–1.02msを含む。これらは同じ総時間を分解した指標で、独立時間として足さない。最小化規則が複雑になっても、元計算に戻す費用の明確な増加は示せなかった。変換時間は相互作用約1.26–3.76秒、優越対照約37.4–39.3ms（単発、合成・検証・WABT込み）。

## 関連資料と確認範囲

- Henrik Björklund, Sven Sandberg, Sergei Vorobyov, *Complexity of Model Checking by Iterative Improvement: the Pseudo-Boolean Framework*。[著者公開16ページ版](https://people.cs.umu.se/henrikb/papers/pseudo-boolean.pdf)の冒頭、§2の定義、§3冒頭を確認。表紙はPSI2003、LNCS2890のextended abstractを示し、[会議版PDF](https://www.dbai.tuwien.ac.at/staff/vorobyov/psi2003.pdf)にも同会議情報がある。公開拡張版全体が査読済みという判断はしない。Boolean cube上の局所改善・一意な最小という一般原理は既知。本試作は全faceでの一意性やinjectivityを要求しないため、同論文のCUPBF計算量結果を直接適用しない。全証明・実装評価は未読。
- Dechter1999のmin-sum消去、Pinkasのpenalty構成、Odense–d'Avila Garcez2025の意味対応は[前版の確認範囲](relaxed-analysis.md)を継承。符号付き相互作用と全状態制約の今回の特定生成器がそのまま既出とは確認していないが、既存の擬Boolean最適化・制約合成からの独立した新規性は未確立。
- 動的メモリ案の事前除外：[US7975149B2 Software protection using data structures](https://patents.google.com/patent/US7975149B2/en)は検索抽出の要旨、splay説明、請求項1–4等を確認。直接openは一度cache missで、全請求項の精査はしていない。[US9117094B2 Data location obfuscation](https://patents.google.com/patent/US9117094B2/en)の検索抽出は周期的再配置、pointer scrambling、self-balancing/splayを明記。法的な権利範囲や特許性の判断ではない。
- 共有セルのlookup案の事前除外：Bernard Chazelle, Joe Kilian, Ronitt Rubinfeld, Ayellet Tal, *The Bloomier Filter: An Efficient Data Structure for Static Support Lookup Tables*, SODA2004, pp.30–39。[著者の書誌](https://www.cs.princeton.edu/~chazelle/pubs.html)、[本文](https://www.ee.technion.ac.il/~ayellet/Ps/nelson.pdf)の表紙・要旨・導入の固定supportに関する箇所を読んだ。査読会議論文。全構成や実装結果は未読。lookup構造の既知性を確認したもので、Wasm難読化への同一適用があると断定しない。

## 再現・採否

Python3.9、Z3 solver4.13.3.0、Node24.15.0、WABT1.0.42、Binaryen133。依存配置は[前版の再現](relaxed-analysis.md)を参照。各出力directoryは新しくする。

```powershell
python -X utf8 research/energy-descent/interactions-screen.py results/interactions-new/screen --robust-selectors
python -X utf8 research/energy-descent/interactions-run.py results/interactions-new/main --robust-selectors
python -X utf8 research/energy-descent/relaxed-performance.py results/interactions-new/main results/interactions-new/performance
python -X utf8 research/energy-descent/interactions-audit.py results/interactions-new/main results/interactions-new/performance results/interactions-new/audit
python -X utf8 research/energy-descent/interactions.py transform input.wasm protected.wasm --robust-selectors
python -X utf8 research/energy-descent/interactions.py recover protected.wasm recovered.wasm
```

flagなしで初期のzero-tie規則の条件を再現する。Optimizeの複数の最適解があるため、係数や探索時間の一致は要求しない。各runのsource、実binary、hash、全状態制約、回復結果を保存した。

初期の引数数条件は同値値の選択で簡約できるため弱く、修正後の条件も逐次消去を防がなかった。技術的に成立した部分は記録するが、強い新規性・低費用な追加保護を得たとは評価しない。小さな文法の上限を越えるよう合成するだけで難読化を発明したことにしない、という制約を次の方向選定へ引き継ぐ。
