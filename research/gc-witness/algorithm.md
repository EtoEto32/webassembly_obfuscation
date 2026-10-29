# 型とアクセス要求を区別する構築証拠

入力は検証済み.wasmの型section、対象type index、有限の参照アクセスpath。任意の元moduleを同値変換する方式ではなく、同じ型groupを宣言する独立したテストmoduleを生成する。

## 対応範囲

Core GCのfinal struct/array/function、numeric/vector/packed field、具体型のnonnull参照およびnullable参照。継承、nonfinal、shared GC、descriptor、continuation、nonnull abstract参照は拒否。16MiB/4096型の上限を持つ。型解析の入力binaryでは標準検証を先に行う。出力はWATをwasmtime.wat2wasmで組み立て、wasmparser 0.227.1で検証する。

## 判定

`live(T)`は、この型の非null値を、外部から型付きGC値を与えられずに有限の構築で作れることを表す。

```
function T: live(T) = true
array T:    live(T) = true          // array.new_fixed T 0
struct T:   live(T) = AND live(U)   // nonnull concrete reference fields Uだけ
```

numeric値は0、nullable値はnullで満たす。空structはtrue。functionはunreachableを本体にしたstubのref.funcで作る。functionが正常な値を返せるとは主張しない。

structの未充足依存数と逆辺を作り、0になった型をworklistへ追加する。型/field数をV/Eとしてこの判定はO(V+E)。対照のmemo化DFSにも同じ漸近計算量がある。

## 構築

```
Build(T, path):
  同じ(T,path)のlocalがあれば参照する
  pathが空:
    function -> ref.func(stub)
    array    -> array.new_fixed T 0
    struct   -> 各fieldを0/null/Build(U,[])で満たす
  pathが空でない:
    struct   -> 指定fieldはBuild(U,tail(path)); 他はdefault witness
    array    -> path先頭はelement 0; Build(U,tail(path))を1個入れる
  結果をnonnullable localへ保存する
```

pathの終点も具体的参照に限定する。出力のrunはそのpathを実際にたどり、終点が非nullなら1を返す。型が構築可能でも、要求されたpathが空型の値を必要とすれば拒否する。例: 自己参照struct Sのarray Aは空なら構築できるが、Aのelement 0を読むためのnonnull Sは作れない。

## 限定した正当性の説明

worklistへ入った順に構築できる。structの必須fieldは既に構築済み、arrayには要素が不要、functionのbodyは型検証上unreachableで任意のresult型を満たす。path付き構築はpath長を減らし、off-pathでは基本証拠を使う。local.getは同じ直線block内のlocal.setより後に置く。

逆に対応範囲で必須struct依存だけが循環していると、最初に作られる該当objectに必要な先行値が存在しない。arrayとfunctionをこの循環条件に入れてはいけない。この説明は有限のWasm constructor操作・外部seedなしの対象に限定する。任意のhostが与えるstoreの全状態に関する型空性定理ではなく、機械証明も未実施。

共有はalias関係を変える。treeとDAGを同値実装として比較しない。mutabilityは型を保存するが、全てのalias配置・値内容・長さを生成するものではない。OOM、実装の上限、入力moduleの副作用、実行時trap一般を除去する保証もない。

`memo`と`worklist`は判定方法だけを変え、構築backendを共通化している。`tree`はmemoを使わず展開する。両DAG方式の出力が一致するのは、この共通backendによる部分もあるため、独立した2実装による全正当性証明とは扱わない。
