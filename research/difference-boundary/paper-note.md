# 差分符号化メモリにおけるWasm重複コピーの境界修復と保護上の限界

## Abstract

私有配列を隣接byteのXOR差分として保持し、Wasm memory.copyを符号化配列のbulk copyと境界2点の補正へ変換する方式を試作した。補正区間の共有により更新費用を下げられた。主・追加120 targetとその観測用版の256,080呼出しで不一致0だった。一方、累積XORによる方式既知の解析は変換48条件すべてを元のraw binaryへ回復し、独立した難読化の主方式として採用する根拠は得られなかった。

## Introduction

元の値を格納しない表現を選んでも、その値を安く一巡で回復できる可能性がある。本研究追補では、計算式の置換列から、永続的なメモリ状態とbulk操作の意味保存へ対象を変え、更新効率と解析費用を独立に測る。

## Related Work

差分表現とprefix scanは既知である。WAVENはWasmのmemory仮想化とbulk命令処理を扱う。EP2831797B1は入力依存の格納位置変更、US9910971B2は符号化領域の計算を含む。今回確認した節・請求項・書誌は[先行技術台帳](prior-art.md)。一般原理が既知であることだけで全ての具体的規則を先行済みと断定せず、境界補正規則とその共有を差分候補として検証する。

## Motivation

各copyの前後に全配列を復号・再符号化すると、転送長が短くても配列全長の仕事が発生する。隣接差分ではコピー区間の内部の関係はそのまま移動でき、壊れるのは外との境界だけである。この性質によって、元の状態全体を置かずに操作を継続できるかを調べた。

## Threat Model

解析者は全binary、初期data、方式、公開I/Oを使える。秘密のruntime、キー、TEEは仮定しない。保護対象は私有状態の論理byteと更新・digest処理の簡潔な等価実装。元データやseedは攻撃へ渡さず、復元後の採点だけで元binaryを参照する。

## Proposed Method

D[i]=A[i] XOR A[i-1]とする。copy(d,s,n)前にc0=XOR D[min(d,s):max(d,s)]、c1=XOR D[min(d,s)+n:max(d,s)+n]を求め、D自身をmemory.copyしてD[d]へc0、末尾未満ならD[d+n]へc1をXORする。区間が重なる場合は共通部分を共有する。i64によるbounds検査を0長returnより先に行う。保存則と疑似コードは[algorithm.md](algorithm.md)に示す。

## Implementation

Pythonの限定profile変換器とCLIを作り、WABTで実Wasmを読み書きしBinaryen133 O3を適用した。固定1pageの私有memory、copyとdigestのみを許可する。汎用C/C++プログラムへの適用率は評価していない。データの配置長とprofileのNが一致しない入力等は拒否する。

## Evaluation

主3配列長64/1024/8192、追加1/2/65536について、plain・byte XOR・全復号版・境界版・共有版のraw/O3と回復物を検査した。公開digest、値/trap、対応する全memoryの不一致0。主60本のWABT interpreter check 360呼出しが一致、112,130小幅モデル比較が一致。4誤変換の反例と3拒否対照を保存した。主再実行60本のbyte再現も一致。

15 harness×3 fresh processで測定した。8KiB近接copyで全復号版約5067ns、共有境界版約39ns。遠い8byte copyでは境界2区間を別走査する約2429nsに対し共有版約1249ns。しかし元copyは約11nsであり、遠いcopyの費用はなお大きい。

方式既知の解析は変換48条件を全て元binaryとbyte一致する実装へ戻した。未変換対照を含む総60条件では、公開profileの索引化により照合順の偏りを除いた。主8KiBの復号部分はbyte XOR約0.360ms、差分版約0.418ms。全数値・反復・変換費用・RSSは[analysis.md](analysis.md)。

## Discussion

境界補正による効率化と解析耐性は別の結果である。全復号版・境界版・共有版は同じ差分dataを保持するため、更新を高速化しても初期状態の累積XORによる回復は変わらない。digestのconsumerも元byteを逐次現す。更新中に元配列全体がない事実だけから保護効果を導けない。

## Limitations

合成した限定profile、単一host、Node性能、固定micro-workloadである。一般のWasm逆コンパイラを評価した実験ではない。初期profile照合器のdata-count差による不備は修正して別記録し、解析耐性に数えない。有限テストは実装全体の形式証明ではなく、特許の新規性・進歩性も未確立である。

## Conclusion

Wasmの重複bulk操作を保つ境界修復と区間共有は実装でき、効率化を確認した。しかし既知の差分・scanによる回復に対して追加の保護機構を示せず、本案は難読化の主発明に採用しない。研究全体の独自で有効な主方式の確立は未完了である。
