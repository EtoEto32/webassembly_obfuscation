# 支持変数数を制限する置換列の書換え

## 対象と保護目標

対象は純粋な `run(i32,i32)->i32` のBoolean式。入力wordの指定bitを抽出し、AND/OR/XOR/NOTから0/1を返す。一般のi32算術、loop、memory、副作用、import、trapは元プログラムとして受け付けない。source readerは対応範囲外の命令を拒否する。許可した元演算はtrapしない。

公開入力・出力、全Wasm命令、初期data、generatorの方式を攻撃者が知る。seedや元式は攻撃CLIへ渡さないが、秘密鍵や秘密の実行環境にも依存しない。回復目標は小さい等価Boolean計算であり、元の変数名・原式の唯一の構文を当てることではない。

## 表現と既知の基礎

置換pを5個の値の配列として表し、`(a*b)[i]=a[b[i]]` と定義する。残りのSIMD lane 5..15は固定する。この規約で `i8x16.swizzle(a,b)` が積に対応する。

既知のBarrington構成を使い、式fを `P(x)=A1(x)...AL(x)` とする。f=0でidentity、f=1で固定5-cycle T=(0 1 2 3 4)になる。ANDには5-cycleのcommutator、NOTには逆とTの積を使う。各source leafは最初1bitだけに依存する。深さによる列長の膨張が大きく、実装は8192因子を上限とする。

## 今回の選択規則

各因子は `(support, table)`。supportは入力64bitのうち依存するbit位置の昇順。表を比較し、結果に影響しない変数は必ず取り除く。

```
word = known_width5_compilation(source_formula)
repeat 16 * len(word) attempts with a fixed PRNG seed:
    choose adjacent factors A, B and a direction
    skip if |support(A) union support(B)| > 3
    candidates = (B, inverse(B)*A*B)
              or (A*B*inverse(A), A)
    compute their complete small tables
    remove semantically irrelevant support variables
    accept a changed pair if table-entry cost does not decrease
emit each table as operational data and each product as SIMD swizzle
return product[0] != 0
```

一度の書換えは `B(B^-1 A B)=AB`、または `(ABA^-1)A=AB` により全入力で積を保存する。表の縮約もcofactorの一致による。最終の0位置はidentityなら0、Tなら1。変換後dataは私有memoryに置き、各表は16byte境界、索引は高々3bitのため、全入力で範囲内にある。memoryはread-onlyとして使用し、外部へexportしない。メモリ資源不足の一般的な振舞いまで同値証明したわけではない。

Hurwitz move自体は既知。支持集合に基づく選択・小表化を差分候補としたが、Wasm SIMD化や入力依存化だけを新規としない。

## 対照とアブレーション

- source：未変換。
- base：幅5へ変換するだけ。書換えを除く対照。
- basis：入力に依存しないR_iについて各因子をR_i^-1 A_i R_(i+1)へ変更、端点はidentity。既知の基底変更。
- fused：隣接因子の依存bitの和集合が3以下なら積を一表にする。既知の局所表化に相当する。
- braid：今回の支持制限付き書換え。

fusedとbraidは表サイズ・命令数が完全一致する対照ではない。その差は実測で示す。

## 適応的解析と失敗原因

まず実binaryをvalidateし、命令とdataを読む。loadのアドレスに影響するbitを保守的に追い、その小集合を列挙して実際の置換表を回復する。元の生成記録は読まない。小さいprefixはこの段階で一表へまとめられるので、抽出後の因子数・表entry数は生成時と異なる場合がある。

逆向き書換えによる厳密なentry数降下を最大32sweep試すと一部の依存は減るが、全部の1bit因子は戻らなかった。これを成功判定にしない。実際には、出力が必要とする一点だけを逆順に追えばよい。

```
state(x) = 0
for A in reverse(word):
    state(x) = A(x)[state(x)]
return state(x) != 0
```

stateは各具体入力で0..4の5値である。入力依存性を多終端判断図として保ち、Applyで合成し、最終的にBoolean ROBDDへ正規化する。公開情報だけで実行でき、生成の逆履歴を復元する必要がない。300,000生成node・20秒の上限を設定したが主50条件・追加16条件は全て回復した。構造を復元できなくても等価実装を得られることが今回の反証である。

一般のBDDは指数的に増え得る。今回の4つの非定数主例と追加2例で安く回復できたという限定した結論であり、任意の置換programへの多項式時間解除定理ではない。
