# 指定GCヒープの構築問題と限定判定

## 入出力と保護対象

対象はWasm GC実装を検査するための正しい入力生成である。秘密を隠す難読化や、エンジンの検査を回避する技術ではない。通常のconstructor/set命令だけで指定された有限ヒープを生成し、参照同一性を検証する。

入力は検証済み `.wasm` の型sectionとnode列。各nodeは型index、整数値またはnullまたはnode IDからなるfield列を持つ。arrayのfield列長が実際のarray長である。異なるIDは必ず異なるオブジェクトとし、同じIDを指す辺だけをaliasさせる。出力は元の型を使う新しいテストWATと構築計画の統計。元プログラムの全入力意味保存を主張するものではない。

## 対応断片

- final struct/array、具体的な型indexへの参照。元のrecursive groupを保持。
- targetの整数fieldはi32/i64/i8/i16。packed値はWasmの切詰め後の値を検証。
- mutable/immutable、nullable/nonnullの組合せ、共有child、循環、空array。
- 1〜128 node、各node最大128値。R readerの16 MiB/4096型制限も継承。

subtyping/nonfinal、shared、custom descriptor、targetのfunction参照やfloat、abstract nonnull参照、等価だが異なるtype indexへの辺は未対応。元binaryが使用する機能についてもR readerのvalidation gateに制約があり、今回の公開Dart binaryは全て拒否された。制限を曖昧にして「実Wasm全般に対応」としない。

空の外部storeから開始し、既存のGC参照をhostから渡さない。途中の補助オブジェクトを許し、終了時は要求nodeと辺を検査する。OOM、実装資源限界、外部副作用やfinalizerはこの定式化の対象外。

## 条件

型の構築可能集合 `Live` はRの既知worklistで得る。arrayは空で構築でき、structは必要なnonnull参照fieldの型が構築可能なら構築できる。nullable参照はnullを使える。

要求のうち**最終値がnode参照であるimmutable field**からなる依存グラフを `I` とする。辺 `u → v` は「uのconstructorより前にvを構築する必要」を表す。fieldがnullableでも、要求値が非nullなら依存辺を残す。

この限定断片・空store・通常constructor/setの条件下で、要求ヒープの実現には、(a)全要求node型がLiveに属すること、(b)Iが非循環であることが必要であり、以下の手順で十分となる。

必要性の説明: 実際に有限の構築列が存在すれば、その中で生成した各node型には有限の構築証拠がある。immutable fieldは作成後に書けないので、参照先は作成時に既存でなければならない。作成時刻の厳密な順序に循環は持てない。

十分性の説明: Iの依存順序でnodeを作る。immutableの参照先は既に存在する。mutable fieldの未構築参照先は、nullableならnull、nonnullならLiveの有限証拠による補助値で初期化できる。全node構築後にmutable fieldを要求値へ更新する。各最終nodeを一度ずつ新規に作るため、指定IDの区別を保持する。

これは条件付きの説明・導出であり、機械検証された定理ではない。全Wasm仕様を含む証明や、今回の全列挙を全入力証明と呼ばない。位相順序と二段階初期化そのものも新規アルゴリズムと呼ばない。

## 疑似コード

```text
realize(types, nodes):
    validate_request_types_and_bounds(nodes)
    Live := finite_constructor_closure(types)
    reject if any requested type is not Live
    order := dependency_order(immutable nonnull-valued edges)
    reject if order does not exist
    for node in order:
        for each field:
            if scalar/null or immutable or target already constructed:
                initial := requested value
            else:
                initial := null if nullable else obtain_finite_seed(field_type)
                remember mutable write of requested value
        create a fresh final node with these initial values
    perform remembered writes
    verify every value, array length, and pairwise distinct node identity
```

`obtain_finite_seed` は同型の既存final node、既存seed、有限証拠からの新規seedの順で利用する。seed共有をfinal nodeの共有に代用しない。長い型依存の構築には明示stackを使う。

計画部分は型と辺に対して線形の処理を基本とするが、出力する全node対の同一性検査はO(N²)。全実装・出力を線形と宣伝しない。`helper_allocations` は生成コード中の補助constructor数であり、JIT/GCの実割当数ではない。

## 対照と失敗条件

`dfs-staged` は普通の深さ優先探索で同じimmutable依存順序を作り、同じ二段階初期化を行う強い対照。`all-deps` はmutable辺もconstructor依存にするため、構築可能なmutable cycleを落とす。`null-patch` は既に構築済みの参照先を使えるが、未来の参照先をnullable fieldでしか仮置きできない。

immutable自己参照・immutable cycle、空storeから構築できないnonnull struct cycleは拒否する。外部seedが存在する別問題、型を書き換える別方式、未初期化参照を許す仮想機械まで不可能と主張しない。
