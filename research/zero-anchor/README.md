# 命令の範囲外結果に合わせる符号化割当

2026-10-21。**既存の符号化演算の実行費用を削減する改良候補**。実装と一環境での測定により小規模な効果を確認した。新しい難読化原理・特許性・既存研究を一般に上回る保護能力を確立したという結果ではない。改善部品として保持し、主発明の検討は継続する。

## 既存方式の課題と変更

小さな値を置換Eで符号化し、各演算をdecode→計算→範囲補正→encodeで処理すると、4bitへの折返しmaskが必要になる。前の[範囲保証による命令置換](../encoding-lowering/README.md)は、添字が0..15と保証できる場所だけを軽量化した。

今回は、**範囲外になる結果を先に求め、その結果に機械命令の零出力が対応するよう、出力符号化を生成する**。範囲外を含む添字でも意味が一致するため、補正命令を削除できる。

byteごとに `x∈0..15, b∈{0,1}` とする。

| 演算 | 未補正byte添字 | 範囲外時のmod16結果 | 生成時の制約 |
|---|---|---|---|
| x+b | 0..16 | 0 | E(0)=0 |
| x-b | 0..15,255 | 15 | E(15)=0 |
| x xor b | 0..15 | なし | 追加制約なし |

例えば加算は `E[(x+b)&15]` を `relaxed_swizzle(E,x+b)` に置換する。添字16では仕様上0またはE(0)となるが、両者を生成時に一致させる。減算で255になる場合は常に0であり、E(15)=0なら所望の値になる。strict swizzleでもこの規則は正しい。Relaxed SIMDでしか成立しない原理とは主張しない。

より一般に、到達可能なbyte添字集合Sに対し `Z={i mod16 | i∈S, i≥16}` を求める。全ての仕様上の結果を一致させる条件は `∀z∈Z:E(z)=0`。Eが16要素の置換なら **|Z|≤1が必要十分**。空なら自由、1個ならその値を0へ置く。二つ以上ならこの方法だけでは不可能。これは範囲が全域を含む場合の有限条件であり、任意プログラム全体の同値性証明ではない。

```text
source.wasmを検証し、対応する純粋なbyte演算列を読み取る
各演算について、入力範囲から未補正添字集合Sを求める
Z = { i mod16 : i in S and i >=16 }
if |Z| > 1: この補正削除を拒否する
Eを置換として生成し、Zが1要素ならE(Zの要素)=0にする
入力の復号表、未補正byte演算、Eによる表引きを出力する
接続する次段の復号表と最後の出力変換をEに整合させる
生成した.wasmを再度検証する
```

任意の4bit加算ではZ=0..14となり適用できない。±2を許すだけでも二つの値が0を要求し、一つの置換では両立しない。複数分岐を共通Eへ合流させる場合にも要求を併合する必要があるが、そのようなCFGへの一般化は本試作に実装していない。

## 実装・非対応範囲

`prototype.py source.wasm output.wasm --mode anchor-free --seed 7` は実バイナリを入力する。WABT1.0.42で検証・読取・生成。Python3.9と既存のS式readerを再利用。3個のi32入力、1個のi32出力、各byteの下位4bit状態と入力から取り出す1bitの加減xorを対象とする。v128の16byte中、splatにより4byteずつ繰り返す。観測する出力は最初の4byteであり、16個の独立入力を処理した実験ではない。

memory、import、任意loop、branch、float、一般のC/C++出力、複数関数、単位bit以外の加数などは対象外。未知の命令を黙って通さない。変換対象にトラップする演算やmemory副作用がないので、今回それらの保存能力を実証したとはいえない。使用するWasm機能はSIMDとRelaxed SIMD。linear memoryは0、表はv128定数。

## 評価

測定前の[計画](plan.md)に対し、6計算形（add1/sub1/add8/add32/mixed8/xor8）、6方式、符号化seed2、raw/O3を比較した。plainだけseedを持たず、合計132本。長さを変えた合成例であり、6種類の実アプリではない。

- random-masked：自由置換で復号・計算・補正・再符号化。
- anchor-masked：今回の制約で置換を生成するが補正を残す。
- anchor-free：同じ制約・同じ表で補正を除く。
- random-table/anchor-table：二つの入力bit値ごとに演算と符号化を融合した表を作りbitselect。既知の表融合構成との比較。
- plain：未符号化計算。最も速い目安。

全byteの入力対65,536、境界1,728、乱数4,096＝各71,360入力。第三引数を含む全24bit組合せを列挙したものではない。独立scalar oracleとの主9,419,520呼出し、方式既知の復元132本の9,419,520呼出しで不一致0。候補24本のswizzleをstrictへ変えた決定的profileでも1,712,640呼出し一致。これら計20,551,680呼出しに予期しないtrapなし。

加減それぞれ128置換×全32入力対×二仕様解釈＝16,384モデル照合も一致。誤anchor例ではこのNodeのrelaxed実行が正しく見えてもstrict版で不一致になる。単一環境のテストだけで削除条件を決める危険を示す。strictへの置換は第二CPU/第二エンジンでの実行ではない。3非対応入力を拒否した。

性能は66 O3条件×5 fresh Node process＝330process。共通Wasm loopから100,000 warmup、9×200,000呼出し。順序seed21102026。wrapperのloop・入力更新費用込み。各計算形のchecksumは全方式で一致。詳細は[比較表](../../results/invention-20261021/zero-anchor-report-v1/comparison.md)。

8段加算・32段加算・混在8段の6条件で、anchor-free/anchor-maskedの中央値比は0.844–0.908（実行時間約9–16%減）。この6条件ではprocess中央値の範囲も分離した。anchor-table比は0.843–0.926（約7–16%減）だが一部process範囲は重なる。未符号化plain比は1.82–2.14であり、元プログラムより速いわけではない。

O3後も削除したmask差が残り、binaryは同じanchor-masked比でadd8の834→674、add32の2646→2006、mixed8の798→678byte。新しい線形memoryは不要。最大RSSは全processの生ログに保存したが、Node/JITを含むprocess全体の値であり、保護データ単独の使用量とは区別する。変換時間はmanifestに各1回の外部reader/compiler/validator込みのmsとして保存。

xor8のrandom-masked/anchor-masked/anchor-freeはseed・optごとにbyte一致する。それでも測定比は約1.01–1.04にぶれた。小さい差を改善と読む根拠にしない。1段の差も約1–4%と小さい。これはこのCPU/V8と限定例での費用改善で、ARM、別エンジン、実アプリでの再現は未確認。

## 方式既知の解析と保護上の限界

`recover.py`はseed・source・生成時の置換を受け取らず、binary内の定数表と演算から、論理値→物理値の16要素対応を伝播する。二行融合表は基準行を座標系とし、もう一行がadd/sub/xorのどれかを全32組で確認する。範囲外版は全到達値でmod16との整合を確認して同じ座標へ戻す。

132/132条件で元計算の正規化式と一致した。非対応0、クラッシュ0、タイムアウト0。回復したbinaryも独立oracleと照合した。通常O3は表を残したが、適応的解析に対する増分の保護効果は未確認。解析bodyの時間は各1回を保存し、性能分布・人間の解析時間とはしない。候補の命令が減るため、復元器の訪問数と一部解析時間も減る。

零への対応を一つ固定すると、置換の選択肢は16!から15!になり、その値の意味が方式から分かる。これは4bitの形式的な選択肢減少であって、攻撃に4bitの安全性があったという意味ではない。本復元器では自由置換版も全復元できたが、それをあらゆる攻撃に対する保護同等性の証明にしてはならない。今回の成功範囲は符号化処理の費用削減に限る。

## 特許検討の位置付け

[技術構成と先行技術の対応](../patent/zero-anchor.md)に、既知部分・差分候補・未確認部分を記録した。0を保存する符号化自体、SIMDの小表実装、範囲解析は既知。本案の差分候補は、範囲外出力との整合制約から符号化を生成し、補正を省く具体的な生成手順。ただし公開仕様から容易に導ける最適化と評価される可能性があり、狭い一致文献が検索で見つからないことだけでは新規性・進歩性の確認にならない。工学的な改善を否定せず、出願の主核として確定もしない。

## 再現

リポジトリrootで、未存在の出力先を指定する。

```powershell
python research/zero-anchor/run.py results/zero-anchor-replay
python research/zero-anchor/controls.py results/zero-anchor-replay results/zero-anchor-controls-replay
python research/zero-anchor/recover.py results/zero-anchor-replay results/zero-anchor-recovery-replay
python research/zero-anchor/benchmark.py results/zero-anchor-replay results/zero-anchor-runtime-replay
python research/zero-anchor/report.py results/zero-anchor-replay results/zero-anchor-runtime-replay results/zero-anchor-controls-replay results/zero-anchor-recovery-replay results/zero-anchor-report-replay
```

依存はPython、Node、`.tools/wabt-1.0.42/bin`、`.tools/binaryen-version_133/bin`、`research/isotope-swizzle/prototype.py`、`research/connectivity-elimination/prototype.py`、`research/encoding-lowering/internal.cjs`。新しいpip/npm依存なし。環境詳細はresultsのenvironment.json。全132本の再生成byte一致、ソースsnapshot/hash、測定条件をreportのidentity.jsonとprotocol.jsonへ保存する。
