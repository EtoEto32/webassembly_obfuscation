# 生成規則・正当性・回復可能性

## 対象と保護課題

元のBoolean DAGを `z_i = f_i(x,z_<i)` とする。実装入力は実.wasmで、1個のi32引数x、1個のi32結果、1–20個のi32 localを持つrunのみ。各localは番号順に一度だけ定義され、AND/OR/XORの2入力ゲート。入力はxのbit抽出、または先行local。返り値は最後のlocal。使う最大入力bit+1をIとし、I+n≤32を要求する。imports、memory、tables、globals、loop、if、calls、非Boolean算術等を含むsourceは対象外。sourceのcustom/debug section保存は保証しない。

解析者は配布Wasm、仕様、変換方式、実行器を知り、変更・実行も可能。source、seed、付属manifestは渡さない。保護課題は、反復とエネルギー表を除き、同じ出力を計算する非巡回Boolean回路を回復する費用。元の名前やゲート番号の完全一致は要求しない。暗号学的秘匿・マルウェア隠蔽は対象外。

## 構成

Boolean領域で各違反は `e_i=z_i XOR f_i`。AND=ab、OR=a+b−ab、XOR=a+b−2abという整数多項式に展開する。Boolean変数の冪はv²=vでまとめる。公開関数は

```
E(x,z) = sum_i w_i e_i(x,z)
```

のみを保持する。係数が同じmonomialへ加算され、元のゲート別区切りは残らない。`dag`は逆順で `w_i=1+sum_{j: i is a direct input of j} w_j`、`lex`対照は `w_i=1+sum_{j>i} w_j`。`flat`負例は全部1。`gauge`は内部座標の置換と0/1補数を多項式へ代入する。任意の非線形座標変換や暗号ではない。

```
read and validate source.wasm
extract ordered Boolean gates
choose weights backwards
substitute a seeded coordinate permutation and complements
expand and collect the integer multilinear polynomial E
check sum(abs(coefficients)) < 2^62
emit aggregate (monomial_mask:i32, coefficient:i64) records

run(x):
    pack fixed input bits and an arbitrary initial internal bit vector
    current = E(state)
    repeat n sweeps:
        for each physical internal coordinate j:
            trial = state XOR (1 << j)
            if E(trial) < current:
                state = trial; current = E(trial)
    return selected output coordinate XOR output polarity
```

初期内部値はxのbitから作るが、正当性はこの選び方に依存しない。入力bitは一度設定した後に反転しない。private非共有memory32の1ページへ表を格納し、storeやmemory.growは使わない。i64の各和の絶対値は係数絶対値和以下なので、符号付き比較を使ってもwrapしない。積は係数×0/1のみ。表の末尾と全load範囲を1ページ以内に生成する。正常なインスタンス化を前提とし、追加memoryの資源枯渇・時間・fuel・デバッガ観測を同値性へ含めない。

## 正答保証と、同時に生じる弱点

座標iを変えると変化する違反は、自身とiを直接読む子ゲートだけである。自身の違反を正すとEはw_i下がり、子の影響は絶対値で高々sum_children w_j。この和よりw_iが大きいので、**他の内部値が何であっても、座標iの最小化は `z_i := f_i` と完全に同じ更新**になる。元入力は固定され、各sweepで全座標が更新されるため、DAGの深さd以下のsweepで全ゲートが正しくなる。実装のn sweepsは十分な上界。補数と置換はこの議論を変えない。全初期値の論証は上記構造に対するもので、実装全体の機械検証ではない。

この保証は解析の入口にもなる。合計多項式から

```
D_j = E(z_j=1) - E(z_j=0)
update_j = [D_j < 0]
```

を計算できる。多項式がmultilinearなので、z_jを含む項だけ抜き出し、そのbitをmaskから消せばD_jが得られる。係数を個別の制約へ分解し直す必要はない。D_jの符号の真理値表を作り、結果に影響しない引数を消すと、元ゲートの親と同等な依存だけが残る。依存グラフをtopological sortし、一回評価のWasmへ変換する。

実装の攻撃は差分のsupportを全列挙し、最大20bit、回復後lookupは最大5入力までに制限する。一般の大fanoutに対して多項式時間とは主張しない。今回最大supportは10、消去後は全て2入力。係数表だけを誤って信頼しないため、表から既知実行器を再生成し、rawまたはBinaryen133 O3のbyteが対象に一致することも要求する。これは方式専用の厳しい適用判定であり、任意の変形・別compilerにも対応する汎用deobfuscatorではない。

## 修正を続けない理由

等重みではこの優越条件が失われ、誤った局所最小に停止する実例が得られた。重みの桁数や配置だけを変えても、優越条件を満たす限り同じ局所更新が回復する。差分項だけを実行時に評価するなど速度改善は可能だが、今回の更新関数が露出する理由は消えない。一般のenergy embeddingの不可能性ではなく、この正当性条件を使う生成族の限界である。
