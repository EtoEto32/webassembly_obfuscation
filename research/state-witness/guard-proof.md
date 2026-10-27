# 等式条件合成の意味と論証

2026-10-24。`guard-analysis.py`の限定profileに対する非機械検証の論証。新しい一般モデル検査原理ではない。

## 契約

元moduleのmemory最小宣言容量を固定し、同容量の二つのmemoryは初期時点でbyteごとに等しい。容量を変えるAPIは受理しない。globals/table/import/startは受理しない。APIは定数アドレス・長さによるmemory.init/copy/fill、data.drop、nopの有限列、または任意i32に対する単一load8_uだけである。後者はmemoryが等しい時、同じ値又は同じtrapを返し、stateを変えない。

左右でsegment有効状態のみが異なる。各APIの終了（return又はtrap）で、API結果とmemory全bytesが等しいことを要求する。hostはtrapを捕捉し、その後もAPIを呼べる。メモリを書き換える外部操作はAPI列に含まない。初期memory条件は全byte割当てを表すが、元programの入口から到達可能なstateかは判定しない。

## 一回の呼出し

segment状態が固定なら、各bulk操作の境界条件はmemory/segment長と定数operandのみで決まり、memory内容には依存しない。したがって最初のtrap位置と呼出し後のsegment状態が確定する。範囲の加算は数学的な非負整数で行い、i32 operandの符号なし解釈の後にwrapしない。0長でも両方の境界条件を確認する。

各memory cellの呼出し後の値は、初期cellを示す変数又はbyte定数である。copyの全読取りを先に表現してから書き込むことで重複copyを保存する。trapした操作は何も書かず、先行操作の書込みは残る。有限の影響範囲以外は左右とも同じ初期cellのままである。

結果が片側return/片側trapなら当該APIの条件はfalse。それ以外では、各影響cellの左右の式を等置した連言がmemory一致の必要十分条件になる。異なる位置でtrapする場合も、この条件が成立すれば選んだ観測契約では一致する。

## API列の固定点

segment状態対をs、APIをaとする。T(s,a)を後続のsegment状態対、E(s,a)を一回の結果/memory一致条件、L(s,a)を左側memoryのcopy/constant写像とする。次式を計算する。

```
G_0(s) = true
G_(n+1)(s) = AND_a [ E(s,a) AND G_n(T(s,a))[L(s,a)] ]
```

右辺の角括弧はpost-stateのcell変数へ左側写像を逆代入する操作である。Eが成立する場合は左右のpost-memoryが等しいので、左側を代表にできる。左右segment状態が揃ったsは、同じmoduleを同じstateから実行するためtrueで打ち切れる。

API列長nまでの一致条件がG_nであることはnについての帰納法で従う。各式は有限cell集合とbyte定数の等式連言のままである。等式を同値類へ正規化し、相異なる定数が同じ類へ入ればfalseとする。G_nは単調に強くなり、有限の同値類分割しかないため、資源上限なしでは固定点へ到達する。固定点は任意有限長API列についての条件を表す。

この必要十分性は**各API後のmemory全一致を要求する契約の内側**に限る。非公開memoryの差をAPIが将来決して読まないような、より弱いcontextual equivalenceまで完全に判定するわけではない。またruntimeのOOMやstack limit、非決定的host動作は含めない。実装上の1024状態/1024反復上限では保留を返し、成功に換算しない。

## 既知技術との関係

逆代入は通常のpredicate transformer、等式の正規化は通常の同値類計算である。PSyCO（Lopes/Monteiro, VMCAI 2014）のabstract/Introductionは有限前提言語での弱い前提の自動合成を既に述べる。Symbolic Register Automata（D'Antoni/Ferreira/Sammartino/Silva, CAV 2019）のabstract/Introductionと検索で読んだbisimulation節も、記号的な等値関係での検証を扱う。これらの一般原理を発明とはしない。今回の追加価値の候補は、Wasm bulk命令のtrap前副作用とsegment寿命に対する具体的な条件合成・再現例である。

12自作例・216初期memoryの深さ4までの呼出し列を、Node/Wasmtimeそれぞれ10,428 API呼出しで照合した。これは実装の検査であり、本節の論証を機械検証したことにはならない。

## funcref tableへの拡張

[table版](guard-table-results.md)では位置を資源番号と位置の組で表し、table slotの値は初期slot変数又はnull/元function indexの参照定数になる。閉じたmodule、固定table容量、外部参照なしを前提とする。同じsort内のcopy/constant写像なので、上記の逆代入と固定点の論証をそのまま適用できる。memory byteと参照定数は異なるsortであり、互いにcopyしない。table.fillは定数参照、APIは単一numeric定数返却も受理する。観測契約へ全table内容の一致を加える。

初期table割当ての元program入口からの到達可能性は判定しない。`conditional`という表示は式が空でないことを表す。許される参照の種類が一つしかない等の特殊なdomainで、その式が全割当てに恒真となる可能性まで表示上で簡約していない。式自身の意味と表示名を区別する。

## 反例列と最短性

具体store Mが最終条件を満たさない場合、最小のiでG_i(s)(M)が不成立になる。一回の局所条件が不成立なら、そのAPIで差が出る。局所条件が成立してもG_(i-1)(T(s,a))(L(s,a)(M))が不成立となるAPIが少なくとも一つある。後者でs/Mを更新しiを一つ減らす。G_0は常にtrueなので有限回で前者へ達し、API列が得られる。開始時にG_(i-1)が成立しているため、iより短い反例はない。

[反例生成の実測](guard-witness-results.md)では独立engineで393列を再実行した。加えて130条件について、各層の式とarray意味論での一段遷移条件の同値を667義務で確認した。これは共有された解析model内の検査であり、Wasmの機械化意味論に対する健全性・完全性の証明には置き換わらない。

## 選択した観測に対する二つのstore

[契約版](guard-contract-results.md)では観測対象Oを全resource、元公開resource、返値/trapだけから選ぶ。APIにbyte読取りがあればその値も観測する。局所条件Eは返値/trapとOのpost-cellの等式である。影響範囲外のstoreは初期に共通で、受理したAPIが変更しない。byte読取りの任意i32引数は、影響範囲内のbyte一致と、共通容量の境界条件で扱う。

Eはprivate storeの一致を保証しないため、左変数Lと右変数Rを別々に残す。次式で両側のpost写像を逆代入する。

```
G_0(s,L,R) = true
G_(n+1)(s,L,R) = AND_a [ E(s,a,L,R)
                         AND G_n(T(s,a), L'(s,a,L), R'(s,a,R)) ]
```

segment寿命が一致してもL/Rに過去の差が残り得るので、そこで打ち切らない。最終条件を得た後、初期store共通という前提L=R=Mを代入してMの条件へ戻す。式の有限性と各層の呼出し深さに関する帰納法は前節と同じで、左右の変数を倍にした有限等式領域を使う。反例抽出も二つの具体storeを更新してrankを減らす。最短性は**選んだ観測契約と受理したAPI集合**の内側に限る。

table定数は元function indexで対応付けるdescriptorであり、意味が同じ別関数を同じと見なす関数等価性を判定しない。public tableの一般的なhost文脈等価性を完全に解くとは主張しない。

## trap終端の利用契約

[protocol版](guard-protocol-results.md)のterminalでは、両側trapの辺でEを比較して呼出し列を終える。上式の後続Gだけをtrueへ置き換える。片側だけtrapならE=falseである。両側正常では従来通り後続へ進む。byte読取りの不正indexも終端で、正しいindexが存在すればその後続条件を保持する。memory容量0ならbyte読取りは全引数で終端になる。

各層が長さn以内の**許された**呼出し列に対応する、という帰納法に変更すれば、固定点と最短反例の論証を適用できる。一回の観測には指定したpost-storeを含むので、terminalを選んでもfull契約でtrap前書込みを無視することにはならない。

さらにterminal/returnsだけの限定命題と簡約は[別の論証](guard-terminal-lemma.md)に分けた。この契約では固定点なしの判定が可能であり、一般版の必要性を過大に主張しない。
