# 実測と新規性の判定

2026-10-22。新たに調べた「入力によって計算順序が変わる循環」は実装できたが、**新しい難読化原理としては採用しない**。元DAGが固定された以前のbit-feedbackとは異なり、二つの入力条件を合わせた依存グラフは実際に循環する。ただし各条件への分解が直接公開されるため、今回の構成では解析上の障壁が残らなかった。

最終の[検証記録](../../results/invention-20261022/conditional-causality-verification-v1.json)で605ファイルのhash、source一致、構文、集計、資料リンクを確認した。性能v1/v2のcore/wrapper計30本はbyte一致し、二つの性能process sessionは正常終了済み。

## 対照と対象

4/8/12個の純粋なi32語演算関数を使う3fixture。add、定数乗算、xor、rotate、shiftを含み、各helperを入力bitによる二つの順序で合成する。データ入力は32bitで、条件は別引数の1bit。先の2bit energyコーパスとは異なるが、汎用アプリや実務上のIP保護事例ではなく限定した機構評価である。

raw/O3ごとにplain、順序選択VM、循環版、VMからの回復、循環版からの回復を検査した。同じ演算群・同じpredecessor表を使うVM対照からの増分を見る。循環版の固定schedule長は7/11/19で、選択した順だけを実行する対照の4/8/12より長い。

攻撃は生成manifestを使わず実binaryから抽出する。回復器の成功率は12/12で、未対応・timeout・crashは0。これを一般の逆コンパイラに対する成功率とはしない。回復本体の正条件検査は公開predecessor列とscheduleだけで済み、計算対象xの32bitを列挙しない。

## 正当性・負の対照

主[checks.json](../../results/invention-20261022/conditional-causality-v1/checks.json)は30条件×4,200入力の126,000呼出しと、診断版12本の12,288呼出しを記録する。診断版ではscratchセルへ0、全1、0x55555555、乱数を書き込む。scratch以外のmemoryが変わらないことも毎回確認した。診断用memory exportは主binaryには追加していない。通常呼出しは同じinstanceを継続使用する。

[監査](../../results/invention-20261022/conditional-causality-audit-v1/facts.json)では、実binaryからのhelperと元helperの32bit同値性を96回SMTで確認し、全てunsatだった。更にhelperを未解釈関数として扱い、任意の初期セルを記号値にして公開scheduleを評価し、24条件で元の関数合成と項が完全一致した。この組合せは限定した演算モデルでの全入力の根拠になるが、Wasm engine全体や任意のmoduleの機械検証ではない。主30本のbyte再現とWABTの120呼出しも一致した。

3つのscheduleを最後の1命令だけ短くすると実行不一致になり、回復器もscheduleの不足を拒否した。dataだけを保った異なる実行器3本はbyte検査で拒否した。div_sを含む有効Wasmは、余分な実行がtrapを増やし得るため入力profileとして拒否した。無効なbinaryのvalidator拒否を難読化効果とは数えない。

## 性能

主性能は[performance-v2](../../results/invention-20261022/conditional-causality-performance-v2/facts.json)。15target×3 fresh process、7batchずつ計315batch。warmup16,384回、20ms較正目標、最大67,108,864回。全batchが10ms以上。既存O3 coreに同じ未最適化Wasm loopを付加し、`--no-liftoff --no-wasm-lazy-compilation`で測った。CPU affinity・周波数は固定していない。

loopはLCGでxとsを変更してrunを呼び、xor checksumを返す。条件bitは交互で、xの下位bitと相関がある一つの分布。異なる条件比率の測定ではない。追加wrapperの63,000通常呼出しに加え、0/1/17/255反復のchecksumを独立JS参照と比較した。

|fixture|plain ns|順序選択VM ns|循環 ns|循環からの回復 ns|循環/plain|循環/VM|
|---|---:|---:|---:|---:|---:|---:|
|reverse4|1.960|10.162|16.129|1.967|8.231|1.587|
|permuted8|3.112|18.380|24.354|3.257|7.826|1.325|
|permuted12|5.328|27.163|42.650|5.245|8.006|1.570|

単位はns/call、process内中央値を取った後の3process中央値。[比較表](../../results/invention-20261022/conditional-causality-report-v1/comparison.md)と[詳細](../../results/invention-20261022/conditional-causality-report-v1/facts.json)にprocess中央値の範囲・サイズ・RSSを保存。元版と回復版の小差は速度優位とはいわない。両回復版のO3 coreは元版とbyte一致する。

元版O3は211/381/536bytes、通常VMは366/544/719bytes、循環版は356/518/693bytes。schedule表の共有で10/26/26bytes小さい一方、各runは余分な関数呼出しを要する。両VMはprivate linear memoryを65,536bytes、tableをn要素追加する。Node全体maxRSSは36,196–37,044KiB。tableやJITだけのmemory費用は切り分けていない。

循環版変換は約36.1–50.1ms、対照約38.3–44.1ms、いずれも単発のprofile検査・WABT起動込み。循環版回復の単発総時間は約61.0–88.2ms、対照59.1–88.3msで、実行器の再生成確認が大部分を占める。循環版の本体101反復の中央値は各0.0027/0.0043/0.0062ms。これは同一process・既読recordでの値で、総時間や人間の開発時間と混同しない。測定時に重い監査は並走させていない。

初回performance-v1は較正上限4,194,304回のため、速いplain/回復版の61batchが10ms未満になった。上限だけを増やしたv2を主結果とし、v1は削除しない。プログラムの正答失敗ではない。両runのcore/wrapper binary30本の一致を最終検証で確認する。

## 先行研究との実質的な対応

書誌・初回読解は[plan.md](plan.md)。追加でNeiroukhほか2008の§VのTheorem 2と§VI冒頭、§VIII冒頭を確認した。十分なscheduleが分かれば未知値を使う3値評価をやめ、任意の2値初期状態から実行できる点も既知だった。複数の必要順序を部分列として含むscheduleを作る機構は、本案に直接対応する。今回の2順序の最短supersequence DPと型の等しいWasm関数への移植が、独立した難読化原理になるとは評価しない。著者のhardware実験は再現していない。

Riedel/Bruck2003の本文は、以前のbit-feedback調査時には未取得だったが、今回表紙と導入・貢献節を実際に確認できた。循環導入を回路合成へ使うこと自体を新規性の根拠にできない、という判断を補強した。Malik1994は機関掲載の書誌・要旨までで本文は未読。公開特許US7249341B2は今回は取得失敗であり、特許請求項の精査が済んだとはしない。

[Wasm Core numerics](https://webassembly.github.io/spec/core/exec/numerics.html)のinteger shift/rotate節も確認し、量を32で剰余化するSMTモデルと整合させた。標準の語演算・型付きindirect call・private memoryの使用を独自技術とは数えない。

## 採否と次の制約

不採用の理由は、①生成・実行原理に具体的な先行例がある、②公開された二つの条件へ分解すれば線形長の合成が回復する、③小さなサイズ削減に対して実行費用が増え、回復の費用はほぼ同じ、の三点である。復元可能であることだけで難読化でないと判定したわけではない。

条件数やseedを増やすだけで別発明を作ったことにはしない。入力ごとに異なる順序を持つことと、その順序の回復が難しいことを今後区別する。研究全体で要求される独立した新規性と検証可能な保護効果はまだ未達であり、この試作を目的の達成へ読み替えない。
