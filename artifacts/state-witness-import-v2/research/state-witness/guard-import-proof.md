# 同期void import profileの条件と限界

2026-10-24。手書きの限定論証でありCoq等による機械化証明ではない。[実装前計画](guard-import-plan.md)に加えて、引数・返値のない一回通過loop、定数0のbr_if、定数store8を入力正規化へ加えた。store8は長さ1のfillへ写す。動的address、typed loop、実際に反復するbranch、非void callは拒否する。

## モデル

**write summaryの区別**：初期版の`public`はfootprint内の全公開cellへ毎回共通値を代入する必須効果である。no-opや部分代入も許す「書込み権限」と同じではない。後から追加した`may-public`は全subsetを許し、条件変換は`R ∧ close_all(R)`となる。[限定論証と区別実験](guard-import-may-results.md)。以降の「書く場合」の記述だけから、省略可能なhostへの適用を推論しない。

既知のsegment寿命から次のimportまたはAPI終了までの結果は決定的である。定数bulk操作のtrap有無はstoreの値に依存しない。各区間のstore変換はcopy/constant写像で表せる。左右は別々にtrapしたprefixまで進むため、同じ最終trapでもhost traceの長さが異なり得る。

各importの仮定は、(a) 同期的に正常returnする、(b) 引数・返値なし、(c) 公開storeを読むか否か、(d) 公開storeへ任意の共通値を書くか否か、である。読む場合は呼出し前の公開storeを観測する。書く場合は同じ位置・同じ値を左右へ代入する。位置ごと・呼出しごとに独立した値を取れる。hostは関数を呼び直さず、memory/tableをgrowせず、非公開stateへ届かない。外部I/Oやhost内状態の比較はこのsummaryの範囲外。

## 条件変換

左右のhost名・順序・終了outcomeが違えば、そのAPIの条件はfalse。同じなら終了時の選択された観測を等式で比較し、許される場合に後続寿命対の関係を連言する。区間を逆順に処理する。host境界では、write契約の公開cellの左右変数を同じfresh変数へ置いて普遍量化し、read契約の公開等式を連言する。その後で区間の左右写像を逆代入する。

これらの変換は等式連言の集合内で閉じる。copy/constant逆代入は通常のWPである。共通代入の普遍量化は、同じfresh変数同士の等式だけを消し、それ以外のfresh変数を含む非自明な等式をfalseにする。各domainは少なくとも2値を持ち、byte/tableの異種間copyがないことを使う。有限の寿命対と有限項集合に対する下降反復により、任意の有限API列の一致条件を求める。

この「正確さ」は供給されたhost summaryと限定モデルについてのもの。任意の実hostに対する必要十分条件ではない。summaryが実hostより広い入力集合を許す場合、falseは実hostでの反例の存在を意味しない。実行可能なhost入力を具体化して再生する必要がある。

## 反例と独立検査

条件が失敗する反復層からAPIを選び、別array意味論の否定式をZ3へ渡して内部import入力を求める。local観測差がなければ後続状態へ進む。記録するのはAPI列と各importのcell代入である。新profileの反例について最短性は主張しない。

検査器はcopy写像を用いずStore/Selectで区間を実行し、各host境界のfresh入力をForAllで束縛する。固定点の各層と初期共通storeへの射影を照合する。ただしparserと入力profileは共有しており、Wasm公式意味論からの証明ではない。

## 継続位置

`continuationOffsets`を指定した場合、正規化したexport本体の指定位置からの継続を調べる。これは研究者が与えた位置である。復元器の保存PC、活性stack、実際のsegment flagsとの対応を解析器が証明したとはしない。省略時は元export全体を扱う。途中の寿命差を元entryの先頭から調べると、そのentry自身のdropが差を消すことがあるため、両結果を分けて保存する。

## 有限domainの付記

制御が値に依存せず、copy・constant代入・入力以外の値操作がないため、ある有限反例の不一致な二つの値だけを区別したまま、他の非定数値をまとめられる。sortごとにprogramが作る定数をCとし、C以外から高々二つの代表値を用意する。反例で不一致を観測した二値が定数なら固定し、一方/両方が非定数なら異なる代表へ写す。他の非定数値は任意の代表へ写す。同じ写像を初期storeと全host入力へ適用すると、copy/constant遷移、寿命、trap位置、host名列を保ち、選んだ不一致も保つ。hostによるstoreの読取りは比較対象であり、その結果がguestの制御へ戻らない仮定を使う。

この説明は非機械検証で、一般のequality-test付きprogramや任意register automataへの「2値で十分」という定理ではない。固定した具体初期storeを変更しない判定なら、その初期値も固定する定数へ含める必要がある。実装した比較は全ての共通初期storeを有限domain上で列挙する形である。物理的byte-domainに非定数値が二つ未満しかなければ、存在するものだけを使う。

有限化の原理は[Oxford Concurrency Groupのdata independence解説](https://www.cs.ox.ac.uk/activities/concurrency/research/dataindependence/)で説明される既知の研究領域に属する。[DEQ](https://www.cs.ox.ac.uk/andrzej.murawski/papers/atva19.pdf)も有限alphabetへ展開する単純な比較方法を紹介し、それを超える記号的処理を提案する。本研究は独立した新しいcutoff原理やDEQへの優位を主張しない。
