# NaN表現を使う変換の事前判定

2026-10-12。判定：検討した構成は意味保存を満たさない。
保存したNaNのビット列を単なるマスクに使う修正は可能だが、
それだけでは既知の状態符号化の変更に留まる。新しい難読化として採用しない。

## 具体的な規則と反例

i32入力xをf64の静かなNaNの下位payloadに入れる。

    E(x) = f64.reinterpret_i64(0x7ff8000000000000 | unsigned(x))
    N(x) = f64.add(E(x), 0.0)

N(x)を表現として保持し、後段で整数に戻すことで元の依存関係を変える案。
対象とするのは通常のWasm意味論であり、特定CPUのpayload伝播への依存を
前提にしない。

仕様で許される結果集合N(x)は、すべてのxについて正のcanonical NaN cを含む。
x=0はcanonical入力、x=1は非canonicalなarithmetic NaN入力だが、どちらも
結果cが許される。N(x)だけを見る決定的な復号器Dには、
D(c)=0とD(c)=1を同時に要求することになり、不可能。
これは特定エンジンで実際に観測した反例ではなく、仕様の許容動作に対する
普遍的な意味が保存される条件が成立しないという反例である。

また、NaN演算を別々に二度実行して同じビット列を期待する方法も不適切。
例えば0.0/0.0の結果は通常のprofileでは符号が非決定的で、
f32の+canonical NaNと-canonical NaNを整数としてXORすると0x80000000。
同じ値を二度ロードすることと、演算を二度実行することを区別する。

## 可能な修正と新規性の範囲

一度得たビット列mをlocalに保存し、x xor mを持ち、最後に同じmで戻すなら
情報は失われない。しかしこれはマスク付き状態符号化であり、mの発生源を
NaNへ変更しただけである。NaNを毎回再計算する必要のない他の乱数源や
任意の整数でも同じ意味保存式が成り立つ。現目標が除外する符号化関数・
パラメータ・ランダム化の変更を超える独立性はない。
この判断はNaNを使うすべての将来の変換を除外するものではない。

## 一次資料

[WebAssembly Core numerics](https://webassembly.github.io/spec/core/exec/numerics.html#nan-propagation)
の冒頭の集合値意味論とNaN Propagationを確認。ページ表示は
WebAssembly 3.0 (2026-10-09)。通常profileでは符号が非決定的で、全NaN入力が
canonicalなら出力payloadもcanonical、それ以外はarithmetic NaNの集合から選ぶ。
deterministic profileでは正のcanonical NaNに制限されるため、こちらでも
payloadに埋めたxの回収はできない。

補助的に[design/Nondeterminism.md](https://github.com/WebAssembly/design/blob/main/Nondeterminism.md)
も確認したが、payloadの説明にcore本文との差があるため、本判定は上記coreを根拠とする。
[Tigress opaque predicates](https://tigress.wtf/opaque.html)は環境由来のentropyを
利用する既存の分類を確認した範囲に留まる。NaN方式の同一先行実装がある
と主張する根拠には使わない。

Wasm実装・Z3試験・性能試験は追加していない。仕様上の情報消失を、単一の
エンジンでテストが通ることによって解消することはできない。
