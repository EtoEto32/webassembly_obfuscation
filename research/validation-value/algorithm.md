# 条件式をWasm妥当性へ移す構成

## 対象と保護目標

対象は `run(i32,i32)->i32` の純粋なCNF条件式。各literalは入力の1bitまたはその否定、clauseはOR、全体はANDである。変換器は実 `.wasm` を読み、限定したAST形状を検査する。任意の算術式をCNFへ膨張変換する機能はなく、memory/import/副作用等を含む元コードは拒否する。

攻撃者は変換後binary、方式、公開ホストadapterを知る。元の式・生成時clause一覧・内部値oracleは与えない。目標は外部validatorを使わず、同じ条件を計算する通常Wasmへ戻すこと。暗号鍵の秘密性、解析不能性、検出回避は仮定しない。

## 規則と意味保存

clause C=(l1 OR ... OR lk) に対して、空結果型のblockを作る。

```
block void
    if l1(input) then opcode unreachable else opcode nop
    ...
    if lk(input) then opcode unreachable else opcode nop
    i32.add      // 検査対象の列には明示的なoperandがない
    drop
end
```

上のifは検証用byte列の生成規則であり、補助モジュール中のWasm if命令ではない。各literalの真偽を一回計算し、該当byteを0x00/unreachableまたは0x01/nopにする。外側の生成器Wasmは常に妥当である。

全literalが偽なら、blockは通常の空stackのままでi32.addに達するためunderflowで不適合。一つでも真なら、そのblockのunreachable flagが立ち、空stackからのpopは型Botを許す。i32.addはi32をpushし、dropで消すのでblockの空結果型を満たす。nopとunreachableだけでは明示的な不整合型をpushしない。blockを閉じるとそのframeのunreachable状態は終わり、次のclauseを独立に検査する。従って全clauseが妥当であることと元のCNFが真であることが一致する。

この規則で1個のvoid関数を持つ小さな補助モジュールを生成し、標準の `WebAssembly.validate` のBooleanを返す。補助モジュールをinstantiate／実行しないので、列中のunreachableをruntime trapとして実行しない。偽入力で補助byte列がvalidationに失敗するのは意図した出力であり、外側のプログラムの不正やツールの未対応とは区別する。

```
read and validate source.wasm
recognize a pure bit-literal CNF expression
create a fixed module template with one block per clause
for each call run(a,b):
    for each literal occurrence:
        template[position] = 1 XOR literal(a,b)
    return validate(template) ? 1 : 0
```

## 実装と契約変更

Python標準ライブラリ、WABT1.0.42、Binaryen133を用いる。外側moduleは固定1page memoryと `env.validate(i32,i32)->i32` importを持ち、memoryをホストadapterへexportする。adapterは指定byte範囲を標準validationへ渡すだけで、再入・書換え・callbackをしない。startはなく、instance完成後にrunを呼ぶ。ホストはbyte列の生成時刻、内容、呼出し回数を元の関数の外部挙動として公開しない契約である。

従って単体core Wasmの元ABIをそのまま保つ変換ではなく、ホストadapterを含めた環境での値の保存である。既存の任意ホストにそのまま差し替えられるとはしない。元の関数はtrapと公開メモリ副作用を持たない。追加memory、validation資源不足、実時間は同値性の契約外。

現在の上限は256clause、4,096literal、補助byte列64KiB以内。CNF以外のBoolean回路を一般に同じ大きさで変換できるとは主張しない。型検査の未知型を解くSAT solverでもなく、与えられた入力のCNFを線形に検査する構成である。

## 方式既知の回復

1. binaryのdata segmentから補助モジュールの初期像を復元する。O3で先頭の零byteが省かれたり、localが再使用される場合も扱う。
2. 固定header、type/function/code section、blockとadd/drop/endを検査し、各clauseに属するpatch位置を得る。
3. runのstore8の値を、local.set/teeの代入を追って元の二引数の式へ戻す。全patchがちょうど一度書かれ、値が0/1であることを限定文法で検査する。
4. 各位置の式sを `s==0` に、同じblockをOR、全blockをANDに置き換え、純粋Wasmを出す。

この解析は実行oracleを呼ばず、元のclauseを参照しない。実験後の独立評価のみが元の式を使う。生成物の6条件すべてを回復し、得られたscalar式はZ3のbit-vector比較で全64bit入力に対し元式と同値だった。これはその6式の比較であり、任意の生成器や任意hostに対する形式証明ではない。

## 失敗原因

値の逆変換を持たなくても、使う検証器の状態が「各blockでunreachableを一度でも見たか」という1bitに閉じている。公開サービスをその到達範囲上で要約すれば、通常のCNFへ戻る。外部importの内部を標準optimizerが見ないことは、方式既知の解析に対する強度ではない。

最大のReject理由は、計算モデル変更の既存研究に対する独立した新規性が未確立で、実行を大幅に遅くした一方、全ての評価条件を短時間で元の条件式へ戻せたことである。主発明には採用しない。入力bit数、block数、nop数を増やすだけではこの失敗原因を変えられない。
