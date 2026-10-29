# 出力履歴による内部状態消去：実測と判断

2026-10-19。**この限定案は主発明に採用しない。** 元のyが一意に復元できなくても、w=b*yを使う短い等価実装を全8条件で回復した。通常の最適化に残ることや、元状態の候補数が多いことを、そのまま追加の保護効果とは数えない。

## 仮説と比較対象

事前の[plan.md](plan.md)に従い、同じP/Q/R/x0/y0に対してb=3,6,256,2^31を変える。独立した4アプリではなく、同じscan族の係数4条件である。sourceは元の2状態、historyは内部yを消した出力履歴、quotientはw=b*yを持つ等価な2状態の対照。rawとBinaryen O3を比較した。配布バイナリに元y/b/Qを復号用に残すことはしないが、方式既知の攻撃者は実行に使う係数から別の等価状態を作れる。

## 正当性と負の対照

- 主32本（24比較条件＋8回復）で66,080呼出し、trap9,216、不一致0。各呼出し後、trap時も含め公開memory64KiB全体が不変であることを確認した。
- 各binaryで境界42例、seed固定ランダム1,000例、長さ0..9の全binary word1,023例。ランダム検査は全入力証明ではない。
- WABT interpreterでは主32本に各7入力、合計224呼出しが一致。memory probeは各moduleの全7呼出し終了後に4箇所、合計128回であり、各呼出し後の全memory検査ではない。
- 小幅全列挙と32bitランダムの局所代数検査89,904状態組で一致。
- 異なるy0/Q定数から同じhistory binaryになる3組を生成。b=0端点も含む追加9本・18,585呼出し、trap2,592で不一致0。主実験との合計は84,665呼出し、trap11,808。v1/v2の再実行を別のカバレッジとして加算しない。
- yを公開、private memoryをexport、public store追加、private store追加の4つの有効Wasmをprofile対象外として拒否。過去入力を進めない誤変換は入力[1,2,3]で値の不一致を検出した。

全binaryはWABTとNodeでvalidationを通過した。拒否は対象外、誤変換は不一致として記録し、保護効果に数えない。今回の実行にツールクラッシュ・timeoutによる解析失敗は記録されていない。NotDec/StackSight等の一般逆コンパイラは今回実行しておらず、未評価である。

## 実行時間・サイズ・メモリ

主値はv2。各条件で独立Node processを3回起動し、10,000回warmup、11標本×3,000呼出しを測定した。表はprocess内中央値の3回の中央値、角括弧はその最小〜最大。1呼出しは64byte入力。72processを固定seedで並べ替え、逐次実行した。信頼区間ではない。

| b条件 | 方式 | byte | ns/呼出し [process中央値の範囲] | source比 | RSS中央値 MiB |
|---|---|---:|---:|---:|---:|
| b3 | source | 404 | 268.3 [266.2, 271.2] | 1.000 | 39.10 |
| b3 | history | 534 | 356.2 [349.7, 371.9] | 1.327 | 39.11 |
| b3 | quotient | 392 | 257.4 [251.5, 259.1] | 0.959 | 39.06 |
| b6 | source | 404 | 267.7 [267.2, 350.9] | 1.000 | 39.01 |
| b6 | history | 534 | 351.5 [349.3, 354.0] | 1.313 | 39.02 |
| b6 | quotient | 392 | 257.7 [257.7, 258.7] | 0.963 | 38.98 |
| b256 | source | 404 | 268.5 [267.5, 270.4] | 1.000 | 39.29 |
| b256 | history | 534 | 349.3 [348.8, 350.4] | 1.301 | 38.99 |
| b256 | quotient | 392 | 265.0 [257.9, 269.4] | 0.987 | 39.16 |
| b2147483648 | source | 404 | 269.1 [268.6, 269.2] | 1.000 | 39.16 |
| b2147483648 | history | 534 | 351.6 [351.4, 373.1] | 1.307 | 39.22 |
| b2147483648 | quotient | 392 | 257.6 [257.0, 270.8] | 0.958 | 39.16 |

O3のhistoryサイズはsourceの1.322倍、quotientは0.970倍。全方式に元からpublic/private各1ページのlinear memoryがあり、合計128KiB。追加のページはなく、historyは過去入力と出力の局所状態を持つ。RSSはNode全体のhigh-water markであり、Wasm単体のlive heapや1命令あたりのメモリ量ではない。private dataはsource84byte、history/quotient80byte。マイクロベンチの速度差を実アプリ全体へ外挿しない。

Node24.15.0 / V8 13.6.233.17-node.48、Intel Core i9-11900K @3.50GHz、16論理CPU、Windows10.0.26100、Python3.9.0、WABT1.0.42、Binaryen133。CPU affinity・周波数は固定していない。

## 変換・解析費用

sourceからhistoryへの全変換は4条件の単発値で107.80〜109.35ms、historyからquotientへの全回復は8条件の単発値で105.53〜153.65ms。これらには外部ツールの起動・validation・WAT再構築を含み、単発値の差を統計的な効果としない。

方式既知の回復器はバイナリの実行用係数表だけを読む。元ソース・manifestは渡さない。8/8の回復binaryは各quotient.rawとbyte一致した。別比較ではsource/history/quotientの24条件を、同じ全module検査を使ってcanonical化し、24/24が対応するquotient.rawとbyte一致した。O3結果を以下に示す。

| b条件 | 方式 | 抽出＋全profile検査 中央値ms（5回） | WAT生成のみ 中央値ms（31回） | Python生成heap peak byte |
|---|---|---:|---:|---:|
| b3 | source | 117.271 | 0.0243 | 7368 |
| b3 | history | 113.087 | 0.0215 | 7040 |
| b3 | quotient | 115.154 | 0.0220 | 7040 |
| b6 | source | 106.851 | 0.0223 | 7368 |
| b6 | history | 108.185 | 0.0215 | 7040 |
| b6 | quotient | 107.315 | 0.0214 | 7040 |
| b256 | source | 109.731 | 0.0224 | 7368 |
| b256 | history | 110.903 | 0.0214 | 7040 |
| b256 | quotient | 109.187 | 0.0224 | 7040 |
| b2147483648 | source | 110.333 | 0.0225 | 7328 |
| b2147483648 | history | 110.232 | 0.0215 | 7040 |
| b2147483648 | quotient | 110.519 | 0.0213 | 7040 |

前者にはWABT/Binaryenによる検査・最適化の再実行を含む。後者は係数取得後のWAT生成だけで、検査・解析・compile全体ではない。historyに一貫して大きい追加解析費用は観測しなかった。ただしgeneric decompilerの能力や人間の所要時間を測ったものではない。

四つのb条件ではy→b*yのkernelサイズが1,2,256,2^31と増えるが、回復はその候補を列挙せず同じ手順で終わる。元のyを正確に当てる課題と等価プログラムを作る課題の違いが、今回の失敗原因である。

## アブレーションと設計見直し

historyを消して十分状態wだけを保つquotientが、今回の機構を除去した対照である。bの偶奇・kernel幅も変えた。独立した複数の保護要素はなく、無関係な要素を追加して成功数を増やしていない。

更新のy依存を高次多項式へ拡張する修正も[補題と反例](extension.md)で検討した。97,380組の多項式検査で不一致0。合同類の代表を一つ選べばb*F(y)を計算できるため、多数の原状態候補を調べる必要はない。一方、実Wasmのrotate62呼出しで31反例を確認し、同じ縮約を任意のbit演算へ拡張できないことを示した。これは次の設計条件であり、新しい難読化方式や保護効果の実証ではない。

## 支持する主張と限界

支持するのは、限定profileの除算なし状態消去、テスト範囲の意味保存、非一意な元状態でも短い等価実装が回復すること、および多項式拡張だけではこの弱点を解消しないことである。独創的で有効な主発明、特許性、一般Wasmへの適用、全入力の実装同値性、他方式より優れた保護は主張しない。

最も近い一般原理は入出力差分式・状態実現であり、Wasmの有限word環への限定適用だけを新規性とはしない。[先行技術の読了範囲](prior-art.md)を明示した。今回の方式の不採用は解除不能性を要求したためではなく、既知原理との差と実行費用に見合う追加効果を確立できないためである。

## 生データと再現

[v2 summary](../../results/invention-20261019/output-recurrence-v2/summary.json)、[benchmark全標本](../../results/invention-20261019/output-recurrence-v2/benchmark.json)、[正当性](../../results/invention-20261019/output-recurrence-v2/correctness.json)、[transform](../../results/invention-20261019/output-recurrence-v2/transforms.json)、[recovery](../../results/invention-20261019/output-recurrence-v2/analysis.json)、[同じ検査費用での比較](../../results/invention-20261019/output-recurrence-compare-v1/comparison.json)、[追加正当性](../../results/invention-20261019/output-recurrence-verify-v1/noninjective/correctness.json)、[拡張の反証](../../results/invention-20261019/output-recurrence-extension-v1/results.json)。

v1/v2は主32binaryがbyte一致。verify/compareはv1の実物を使い、実行時間の主値にはv2を使う。再現コマンドは[README](README.md)、本文生成は`python research/output-recurrence/report.py`。測定を再実行せず保存値から表を作る。研究全体の主方式は未確立であり、この記録を全研究の完了とはしない。
