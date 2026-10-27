# 非破壊の状態識別と復元検査

本方式は検査用instrumentationである。状態を書き換えて復元を実現するJとは異なり、復元結果の比較に必要な観測を生成する。0長initや生bit再解釈そのものは既知である。

## 対象と観測契約

閉じたcore module、numeric function signatures / globals、memory32を最大1個、funcref tableを最大4個、function-index elementを扱う。imports/start/GC/共有memory等は未対応。state exportは検査hostが管理し、観測中に別のhost/guestは変更しない。元のstateへ外部function referenceを挿入しない。実行後の観測はmemory 256 pages、table 4096 entriesを上限とし、超過は拒否する。maxのない宣言も受け付けるが、実行後の大きさをこの上限で検査する。

full profileは追加exportを使い、memory bytes、table関数参照、numeric globalsのraw bitsを読む。これはprivate stateの露出を増やすため本番保護機構には使わない。numeric profileはJの入力制限に合わせたもの。tableはnullか否かしか分からず、完全なstate observerではない。

## 生成規則

```
Generate(module, profile):
    validate(module); reject unsupported forms and reserved exports
    remember original function/global/segment indices
    for memory: append size, byte-read, end-bound observers
    for each table: append length, nullness, end-bound observers
    if full: export original functions, tables and memory to trusted test host
    for numeric global g: append integer-bit-pattern getter
    for data/element segment s with a compatible destination:
        append init(destination=0, source=1, length=0)
    emit binary and descriptor; validate output

Observe(instance, descriptor):
    read lengths and enforce research allocation budget
    copy memory bytes; read raw global bits
    map table references to canonical export alias classes (or null)
    record normal-return/trap for segment probes and end-bound probes
    return structured descriptor (no lossy hash)

CheckRestore(reference, restored):
    compare descriptors and report differing state categories
    distinguish introspection differences from original-interface differences
    when needed search bounded original-API suffixes for a behavioral witness
```

元function indexは変えず、observerを末尾へ追加する。関数参照はプロセスのpointer値でなく、そのinstanceのcanonical exportsとのJS identityで照合する。最適化後に複数exportが同じfunctionを指す場合は全indexの集合を保持する。最後のindexで上書きしない。異なるbinary間の任意の関数対応を発見するアルゴリズムではない。

## 非破壊性

memory.initの範囲条件は `src + n <= segment_length` と `dst + n <= memory_length`。`dst=0, src=1, n=0` なら、宛先が0pageでも宛先条件は満たされ、非空segmentが有効なら成功、drop後はtrapする。転送byte数は0なので、どちらの場合もguestのmemory/segmentを変更しない。table.initにも同じ論証を適用できる。trapはhostで捕捉し、以後のguest状態を比較する。

空segmentのdrop前後は同じ空内容なので識別しない。active/declarative segmentもinstantiation後は空である。使用可能なmemory/tableがない場合には対応initが元moduleでも型付けできず、このprobeを生成しない。

end-bound probeはmemory/tableの論理長直後を読み、境界検査の欠落を診断する。memory32の最大容量でpage数をshiftするとwrapするため、その場合だけstatic offsetとbaseの和が2^32となるloadを使う。実験のallocation budgetでは最大容量を実割当していない。

## 一致が意味する範囲

同じmodule、停止中の空stack、閉じた参照、同じ資源枯渇の扱いという限定モデルなら、全memory bytes/長さ、table参照/長さ、numeric globalsのbits、segment有効性が一致すると、以後のstore操作の意味も一致する。immutableなsegment内容・関数本体・maxは同じmoduleから固定されるためである。NaN非決定性がある命令は可能な結果集合を対応させる。機械検証済みの定理ではなく、仕様に基づく論証である。

この十分条件は必要条件ではない。元APIがsegmentを再使用しないなら、drop状態が違っても元APIの挙動が同じ場合がある。またJのようにコードやstate representationを変えたものは、descriptor一致だけで以後の全命令の実装が正しいと証明できない。original-interface suffixの実行反例、限定modelのstate一致、未確認の同値性を分ける。

失敗条件はimportsやshared stateを勝手に閉じたものとみなすこと、活性stackを無視すること、外部参照を自前functionへ誤対応すること、opt前後で同じindexだと思い込むこと、observer追加でのみ得た差を漏えいと断定すること、またtrap費用を無視することである。

追加の実測条件：別のcheckpoint変換を通すと、observerのexport wrapperが再開metadataを変更する場合がある。元binary上の非破壊性を、変換後の物理metadata全体へ拡張しない。Weaveではsnapshot取得後の観測専用複製とresume専用複製を分けた。また、再実行を許す復元契約では、中断時のstate差が後続処理で解消し得る。[中断点生成の実験](cut-results.md)では実際にこの例を確認した。中断直後のdescriptor不一致だけで元APIの不正を結論しない。

さらに[元APIからの分類](context-results.md)では、差を読む前のdropという十分条件と、有限の元API遷移閉包を別に実装した。前者は保守的で、差を読んでも冪等な書込みと後続trapで同じ外部結果となる例を保留する。後者はその例も分類した。元programのguest storeへ射影したモデルであり、変換器の制御metadataは証明対象へ含めない。
