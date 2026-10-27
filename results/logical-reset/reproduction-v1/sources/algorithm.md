# J：論理容量・セグメント寿命の連動変換

2026-10-24。新規性を検証中の試作。実装は[prototype.py](prototype.py)。先に固定した[plan.md](plan.md)と、実装後の限定を分けて読む。

## 目的と範囲

終了したリクエストの後で、同一のWasm instanceを宣言初期化直後のguest可視状態へ戻す。状態漏洩を防ぐ対象は、次のguestが数値APIから観測する値とtrapである。暗号化・難読化・実行中の移行を目的にしない。

入力は閉じたcore module、private bounded memory32一つ（最大256ページ）、任意のprivate bounded funcref table一つ（最大4096要素）、定数で初期化する数値globalと数値関数signatureに限定する。WABTでfoldした式のうち実装のallowlistに入る命令を扱う。全てのcore Wasmを処理できる変換器ではない。

imports、start、memory/table/global export、参照を渡すsignature、shared memory、memory64、SIMD、GC、EH、continuation等は対応外。元binaryと変換binaryをvalidateする。受理範囲の広さと、受理した全programの意味保存は別の検証課題である。

## 状態の関係

元instanceの状態を `S=(M,T,G,D,E)` とする。変換後は物理memory/table `Mp,Tp` と、private numeric globalに置く論理容量 `lm,lt`、各segmentの有効長 `ld[i],le[i]` を持つ。

- `|M| = 65536*lm <= |Mp|`、`|T| = lt <= |Tp|`。
- `M = Mp[0:|M|]`、table内の関数参照は元関数と変換後関数の対応で比較する。
- 元の数値global値は対応するglobal値と一致する。
- passive segmentのpayloadは物理的に保持し、元のlive/dropped状態を有効長で表す。
- active/declarative segmentの元の有効長は0のまま。active初期像の再適用専用に別のpassive segmentを加える。

original関数・global・segmentのindexを変えず、補助要素を後置する。元codeの参照先は新しいreset関数やprivate globalを指さない。閉じたmoduleの構造とstatic indexが、この限定実装におけるmetadata保護の根拠になる。難読化でmetadataを隠す保証ではない。

## 疑似コード

```text
transform(module):
    validate input; reject unsupported interfaces, features and expressions
    append logical capacities and segment lengths as private globals
    append passive shadows of active initial memory/table images
    rewrite every original memory/table operation and call_indirect index
    append reset export; validate output

access(address, length, logical_capacity):
    evaluate original operands exactly once, in original order
    if u64(address) + u64(length) > logical_capacity: trap
    perform original operation on physical storage

segment_init(segment, destination, source, length):
    evaluate all original operands
    check destination range against logical capacity
    check u64(source)+u64(length) <= logical_segment_length[segment]
    perform original init

segment_drop(segment):
    logical_segment_length[segment] = 0

grow(delta, init_value):
    old = logical_capacity
    if u64(old)+u64(delta) > declared_maximum: return -1
    new = old+delta
    if new > physical_capacity and physical_grow(new-physical_capacity) fails:
        return -1
    initialize [old,new) to zero / supplied table value
    logical_capacity = new
    return old

reset():  # trusted host, no guest activation remains
    zero initial memory prefix; null initial table prefix
    restore original numeric globals
    restore logical capacities and initial segment lengths
    replay active images from private passive shadows, in original order
```

scalar accessでは`address + static_offset + width`を64bitで検査する。copyは送信側・受信側をともに検査する。0長でも範囲検査は省略しない。storeの値を求める式がglobalを書き換えてからtrapする場合、その評価を検査より前に置く。call_indirectの引数評価とindex評価を保ち、indexだけを補助関数へ通す。reset内の復元操作は論理guardの対象にしない。

## 意味保存の理由と未証明部分

上記状態関係を帰納不変条件の候補とする。通常accessは同じprefixに作用し、範囲外では効果前にtrapする。growは新たに見える領域を必ず初期化するため、前epochの物理的残留を露出しない。drop/initは有効長により空segmentの0長境界まで再現する。resetはdeclared初期像へ状態関係を戻す。

これは証明のスケッチであり、変換器全体の機械証明ではない。allocation成功条件を合わせた有限実行を対象とし、実装資源不足によるgrow失敗・stack exhaustion・実行打切りの同一性は主張しない。追加helperでstack消費は変わり得る。浮動小数の非決定的NaN payload等を網羅検証したわけでもない。

trapの文言・種類番号は`unreachable` guardで変わる。JSの関数object identity、物理容量、RSS、時間、cache、hostが読む残留byteを同一にする方式ではない。悪意あるhost、外部resource、shared memory、再入、suspended computationは脅威モデル外。guest停止が前提なので、任意の非停止guestをresetで強制終了できるという保証もない。

## コスト

各対象命令に範囲検査とhelper callを加える。O3によりinline・簡約される場合がある。resetは初期memory/tableの大きさと初期像に比例する。成長済み物理容量とpassive payloadを保持するため、reset後の論理サイズを減らしても物理memoryは解放しない。保持上限を明記せずに省メモリ化とは呼ばない。
