# 4点実行：実測と反証

2026-10-19。元式を4つのずらした入力で評価し、32bit環で高次項が消える条件から出力を合成するWasm変換を実装した。dynamic版の各lane入力写像は非単射で、通常O3後もSIMD評価が残る。しかし、方式を知る解析者は入力を逆算せず、定数係数を追って30/30条件をscalarへ回復できた。独立した新規性と十分な追加保護優位性は確立できず、主発明には不採用とする。

## 比較と正当性

5つの小さいpure polynomial kernel。cubic、quartic、bivar、反復4/8段のiter4/iter8であり、5個の実アプリではない。iter8は構文上の多項式次数256で、関数としての最小表現次数を測定したわけではない。source/diagonal/constant/dynamicの4方式×raw/O3で40本、回復30本、計70本。diagonalはSIMD化だけ、constantは固定方向の4点合成、dynamicは非単射の入力写像を用いる。

- 主70本×4,288入力=300,160呼出し、不一致0。境界64、walking bit128、seed固定乱数4,096を含む。
- 異なるランダム式12モデルの60本で257,280呼出し、不一致0。主と合わせ130本・557,440呼出し。再実行を独立カバレッジに加算しない。
- Python整数参照値とWABT interpreterによる主70本×6=420呼出し、不一致0。
- 回復30本と元binaryから抽出したscalar式について、Z3 4.13.3の32bit同値性問い合わせが30 unsat、sat/unknown各0。SIMD変換器・parser・compilerを含む全体の機械証明ではない。
- reduced widthおよび32bitで16,000組の単項式・方向を検査。全入力を列挙したものではない。
- sourceの除算・XOR・捨てられるtrap、および誤ったshift・出力重み・vector XORの計6件を拒否。後者3件の実Wasm反例は0→2,147,483,648、1→3,074、1,024→3,072だった。
- 各lane入力の非単射性は、異なる2入力が同じ値になる4組を実Wasmで確認した。これは全プログラムの解析困難性を意味しない。
- 条件を緩めても正しくなる正の対照として、3次式のshift=0と偶数係数4次式のshift=7を回復した。追加6本・25,728呼出しで一致。解析器が固定shift=8の構文だけを認識しているわけではない。この件数は上記130本の外数。

対象にはmemoryや公開副作用がなく、許可した演算はtrapしない。任意のmemory副作用・trapを保存できるという結果に拡張しない。WABTとNodeのvalidationを使用した。

## 実行費用

Windows10.0.26100、Intel i9-11900K @3.50GHz、Python3.9、Node24.15.0/V8 13.6.233.17-node.48、WABT1.0.42、Binaryen133。CPU affinity・周波数は固定しない。

最初のv1はJS境界を含む210 fresh processを測ったが、入力変換・呼出し側のJIT等によるばらつきが大きかった。その値を速度優位の主張に使わず、同一のWasm内部loopを各O3 binaryに加えたbatch-v1を主値とする。元/変換/全回復の35条件×3 fresh process=105 process。条件順は固定seedで混ぜ、逐次実行した。

各processで1,000,000 kernel呼出しをwarmupし、11標本×200,000呼出しを測る。表は3processの中央値の中央値と、process中央値の最小・最大。信頼区間ではない。loop、入力更新、rolling checksumの費用を含み、純粋な単一命令時間ではない。harnessは700検査と7,140回の参照呼出しで照合した。

|kernel|方式（O3）|元binary byte|ns/iteration [範囲]|source比|process RSS MiB|
|---|---|---:|---:|---:|---:|
| cubic | source | 50 | 0.679 [0.679, 0.726] | 1.00 | 36.49 |
| cubic | diagonal | 85 | 1.194 [1.192, 1.200] | 1.76 | 36.70 |
| cubic | constant | 156 | 2.902 [2.881, 3.079] | 4.27 | 36.69 |
| cubic | dynamic | 190 | 3.904 [3.856, 3.930] | 5.74 | 36.69 |
| cubic | dynamic recovered | 68 | 0.679 [0.679, 0.707] | 1.00 | 36.54 |
| quartic | source | 49 | 0.644 [0.620, 0.670] | 1.00 | 36.55 |
| quartic | diagonal | 66 | 0.928 [0.927, 0.929] | 1.44 | 36.66 |
| quartic | constant | 137 | 2.652 [2.639, 2.654] | 4.11 | 36.79 |
| quartic | dynamic | 171 | 3.570 [3.522, 3.601] | 5.54 | 36.78 |
| quartic | dynamic recovered | 61 | 0.644 [0.644, 0.644] | 1.00 | 36.52 |
| bivar | source | 53 | 0.803 [0.803, 0.805] | 1.00 | 36.60 |
| bivar | diagonal | 76 | 1.119 [1.119, 1.192] | 1.39 | 36.68 |
| bivar | constant | 147 | 2.949 [2.946, 2.951] | 3.67 | 36.70 |
| bivar | dynamic | 181 | 4.099 [4.062, 4.219] | 5.11 | 36.75 |
| bivar | dynamic recovered | 75 | 0.802 [0.802, 0.802] | 1.00 | 36.52 |
| iter4 | source | 113 | 1.774 [1.774, 1.788] | 1.00 | 36.66 |
| iter4 | diagonal | 279 | 3.916 [3.906, 3.990] | 2.21 | 36.76 |
| iter4 | constant | 350 | 6.093 [5.795, 6.237] | 3.43 | 36.72 |
| iter4 | dynamic | 382 | 7.306 [7.265, 7.336] | 4.12 | 36.68 |
| iter4 | dynamic recovered | 184 | 1.773 [1.773, 1.798] | 1.00 | 36.50 |
| iter8 | source | 187 | 2.953 [2.671, 3.083] | 1.00 | 36.61 |
| iter8 | diagonal | 495 | 8.198 [8.174, 8.591] | 2.78 | 36.66 |
| iter8 | constant | 566 | 10.392 [10.320, 10.902] | 3.52 | 36.66 |
| iter8 | dynamic | 598 | 12.136 [11.948, 12.779] | 4.11 | 36.71 |
| iter8 | dynamic recovered | 312 | 2.917 [2.908, 2.926] | 0.99 | 36.52 |

recoveredはO3後の変換物から回復したものに追加O3をかけていない。binaryサイズは測定harnessを付加する前。全条件のlinear memoryは0page、GC allocationもないが、Wasm/Node/JIT自体のメモリ使用量0という意味ではない。RSSはprocess全体のhigh-water mark。実アプリ・別機器への速度一般化は行わない。

## 解析・変換費用

各バイナリを読み込んだ後、付値と定数係数の射影を9回測定。表の解析msは中央値、全回復msはvalidation・read・compileを含む単回値。

|kernel|方式|射影中央値ms|vector memo節点|付値積の組合せ|全回復ms（単回）|
|---|---|---:|---:|---:|---:|
| cubic | diagonal | 0.0227 | 7 | 3 | 58.94 |
| cubic | constant | 0.0520 | 11 | 12 | 58.51 |
| cubic | dynamic | 0.0622 | 15 | 14 | 60.03 |
| quartic | diagonal | 0.0153 | 5 | 2 | 61.35 |
| quartic | constant | 0.0461 | 9 | 13 | 58.91 |
| quartic | dynamic | 0.0643 | 13 | 15 | 60.84 |
| bivar | diagonal | 0.0213 | 7 | 3 | 62.57 |
| bivar | constant | 0.0521 | 11 | 14 | 58.60 |
| bivar | dynamic | 0.0604 | 15 | 16 | 58.18 |
| iter4 | diagonal | 0.0853 | 28 | 6 | 58.75 |
| iter4 | constant | 0.1395 | 32 | 53 | 63.81 |
| iter4 | dynamic | 0.1450 | 36 | 55 | 58.15 |
| iter8 | diagonal | 0.1563 | 52 | 10 | 59.77 |
| iter8 | constant | 0.2248 | 56 | 117 | 60.98 |
| iter8 | dynamic | 0.4067 | 60 | 119 | 63.31 |

15変換の単回時間は57.91〜63.91ms。外部tool起動を含むため小さい差の有意性を主張しない。解析器の開発費用・人の解析時間は測定していない。NotDec/StackSight本体は実行していない。主解析では未対応・crash・timeout・誤答は0で、全30条件がrecoveredである。

## 何が分かったか

前案の「最後に一つのlaneを取り出す」という弱点には対処している。4点の出力が合成に必要で、各入力写像の逆関数も一般には存在しない。それでも公開命令からkの定数係数を伝播すれば元のDAGが戻る。生成時に高次項を消す条件が、解析時にも保持すべき係数を最大4個に制限しているためである。高次数や非単射性による困難性を期待した仮説は支持されない。

動的版の解析費用増は存在する。しかしconstant対照に対して大きな非局所の探索を強制せず、実行側ではsourceの約4〜6倍の反復時間を要した。Python解析時間とV8実行時間を直接割って保護効率にしない。回復可能という事実だけで不採用にせず、安い射影の構成、実測した増分、[近接する自己還元・符号化計算](prior-art.md)との技術差を合わせて判断した。

初期probe-v1は記録用dictのmode重複というrunner bugで中断した。修正後のprobe-v2と主v1の70binaryは全てbyte一致。初期失敗を保護効果や意味不一致へ加算しない。主実装の修正・主要な設計変更は行っていない。

## 保存結果

[主manifest](../../results/invention-20261019/nilpotent-stencil-v1/manifest.json)、[主正当性](../../results/invention-20261019/nilpotent-stencil-v1/correctness.json)、[解析全標本](../../results/invention-20261019/nilpotent-stencil-v1/attacks.json)、[batch性能全標本](../../results/invention-20261019/nilpotent-stencil-batch-v1/benchmark.json)、[追加検査](../../results/invention-20261019/nilpotent-stencil-verify-v1/random/correctness.json)、[誤変換の反例](../../results/invention-20261019/nilpotent-stencil-verify-v1/counterexamples.json)、[SMT結果](../../results/invention-20261019/nilpotent-stencil-proof-v1/proof.json)、[byte再現](../../results/invention-20261019/nilpotent-stencil-v1/replay.json)。新規で有効な主発明・特許性の確立は未達である。
