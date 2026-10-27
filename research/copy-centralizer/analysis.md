# 実測値と採否

## 正当性と構成

| profile | N | copy数 | 中心化空間次元 | Bの非零係数 | 複数byteを混ぜる行数 |
|---|---:|---:|---:|---:|---:|
| blocks16 | 16 | 5 | 16 | 48 | 16 |
| overlap8 | 8 | 4 | 4 | 12 | 4 |
| irregular8 | 8 | 3 | 6 | 16 | 4 |
| allcells8 | 8 | 56 | 1 | 8 | 0 |

4つの小さなAPI profileであり、独立した実アプリ4個ではない。各profileで同じ初期dataを4 mode×raw/O3に使用。共通乱数generatorはseed固定だが対象ごとに継続するため、512回のランダム操作列は対象間で完全同一ではない。境界write/readは共通。referenceはJSのbyte配列・snapshot copyで、値とtrapを照合し、物理memoryを既知のcodecで復号した全64KiBとも照合する。

主32条件は22,016呼出し、192 trap、13,832全memory比較、不一致0。回復8条件は5,504呼出し、48 trap、3,447全memory比較、不一致0。trapは範囲外read/writeであり、固定copyのOOB coverageではない。範囲外copyは変換の適用条件から除く。全入力同値の形式証明とはしない。

2/3セルの28制約系について全7,392行列を列挙し、連立制約の基底が生成する集合と可換条件の真値集合が一致した。主32本を最終実装からbyte一致で再生成。主・回復40本の追加wrapperについてWABT/Node/独立byte oracleのchecksumが一致した。wrapperは各1回で、全memoryを別実行器で網羅した意味ではない。

制約から最後のcopyを落とす誤変換と、write時の旧値差分を除く誤変換をraw/O3で各実行し、全4負例で相違を検出。memory公開、追加export、領域外copyの3 valid WasmをCLIが拒否した。

## 実行費用

O3 coreに共通の未最適化Wasm loopを追加。Nodeは`--no-liftoff --no-wasm-lazy-compilation`、warmup128、pilotで64から反復数を倍増（目標5ms、最大1,048,576）、9 batch、3 fresh process。順序seed211045。表はprocessごとのbatch中央値の中央値、角括弧は3 process中央値のmin–max。JIT機械語の検査や別CPU/別エンジンの性能測定は行っていない。

入力選択workloadは1回の論理write、LCG値で選ぶ1 copy、1 read、loop・checksumを含む。JS境界費用を1操作ごとに計測する構成ではない。

| profile | plain ns | uniform ns | conjugate ns | native ns | native / conjugate |
|---|---:|---:|---:|---:|---:|
| blocks16 | 6.208 | 6.560 | 25.115 [24.310–25.493] | 17.632 [17.614–18.001] | 0.702 |
| overlap8 | 2.490 | 2.741 | 7.782 [7.697–7.901] | 3.284 [3.280–3.296] | 0.422 |
| irregular8 | 6.032 | 6.591 | 15.964 [15.434–16.415] | 10.694 [10.379–10.733] | 0.670 |
| allcells8 | 12.315 | 12.557 | 27.834 [27.022–28.305] | 20.596 [19.955–20.842] | 0.740 |

混合が残る最初の3条件では、同じBを毎回復号する自作対照より処理全体が約30–58%短い。一方plainより約1.32–2.84倍遅い。allcells8はB=Iで、無意味な変換処理を省いた比較にすぎない。比較先を既存難読化製品やData Randomization論文の実装と呼ばない。

先に測った「全copyを固定順に毎回実行する」workloadも保持。native/conjugateは最初の3条件で約0.085、0.238、0.364だった。copy数が多く、短い固定列をエンジンが最適化できる条件である。入力選択への変更で差が縮むので、固定列の大きい高速化率だけを主張しない。両workloadそれぞれ48 fresh process、合計96。257反復のfresh instance checksumは各profileで4 mode一致。時間の反復値が同じになることを再現条件にはしない。

O3 core bytes（plain/uniform/conjugate/native）は、blocks16=211/235/4369/1484、overlap8=181/205/1606/618、irregular8=159/183/1484/701、allcells8=1373/1397/13962/1698。線形memoryは全て65,536 bytes。Node全processのRSSはruntime.jsonのrssBytesに保存し、codec単独の使用量とは呼ばない。変換時間はvalidator・reader・profile再生成・コンパイル込みでnative約76–82ms、各1回の診断値であり統計比較ではない。

## 方式既知の回復

raw/O3×4 profileの全8条件で回復。最終版の未対応、crash、timeoutは0。最初のO3 reader未対応は修正履歴に残す。

行列学習は1条件96 API呼出し、別途128 writeの検査。全8条件の学習768呼出しと検査1,024呼出しを正当性の主22,016呼出しへ足さない。処理全体は各約170–180msで、reader、Node起動、観測用export追加、回復compile等を含む単発値。人間の解析器開発時間ではない。

より安い攻撃は、copy関数を読取り、初期論理dataを32 readで得てplain版を構築する。実際に全8条件・合計256 read・0 writeで実行し、検証済み回復版と全てbyte一致した。全処理約122–132ms、単発であり最適な攻撃時間や統計的優位の推定ではない。行列を混ぜても、この公開APIなら同じquery数でcloneできる。

## 判定と残る課題

操作集合に適合する混合codecを自動生成し、同じcodecの復号版より軽く実行できた点は実装上の成果。一方、同程度の費用で既存方式より保護できる証拠、独立した新規原理、特許性は未確立。主難読化方式には採用しない。

今回の弱点は、固定線形codecの回復可能性に加え、公開read/write/copy ABIそのものが短いcloneを作るのに十分な意味を与えること。Bの密度やNだけを増やす追試ではこの条件が変わらない。次の候補では、回復したい意味が公開ABIから直接指定できない実際の計算を保護対象にし、元の計算へ戻る十分統計量が短く残っていないかを実装前に検査する。ただしAPIを隠すことだけを新発明にしない。
