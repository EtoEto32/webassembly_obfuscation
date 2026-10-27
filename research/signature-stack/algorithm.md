# Pのアルゴリズムと保証の範囲

## 研究課題と攻撃モデル

第三者からWasm moduleを受け付けるhostにおいて、**検証そのものの資源消費**を減らす。攻撃者は合法・不合法の任意binaryを与え、方式も知っている。hostのcompiler/validator、intern pool、OSは信頼する。実行時fuel、悪性挙動の検出、暗号化、解析不能化を目的にしない。実験はすべてローカルの有限・小規模入力で行った。

保護条件は「対応範囲の標準の受理判定を変えず、反復する型列の物理展開を減らす」。新しい型安全性の意味論を導入するわけではない。

## 表現

型列を内容でinternし、pool[id]にimmutableなnumeric型の列を置く。hash衝突だけで等値とはしない。HashMapはキー全体の等値を確認する。operand stackはchunk列 `(id, lo, hi)` の連結であり、論理長を別に保持する。実装ではloは0で、末尾popによりhiが縮む。Bottomはunreachableの型多相性を表す内部記号である。

```text
push_signature(id):
    append chunk(id, 0, length(pool[id])) if nonempty

check_suffix(expected_id, current_frame):
    n = length(pool[expected_id])
    available = logical_length - current_frame.height
    if available < n and not current_frame.unreachable: reject
    compare the last min(n, available) actual cells with expected suffix
    for each overlapping chunk:
        if same intern id and same endpoint: accept this overlap in O(1)
        else compare numeric values, accepting actual Bottom for any expected type
    absent prefix is implicit Bottom only in unreachable frame

pop_signature(id):
    check_suffix(id)
    truncate min(signature length, available cells)
```

enter block/loop/ifではparameter列をpopし、新しいframeのheightを記録し、宣言parameter列をpushする。ifのconditionは先にi32としてpopする。endではresult列を検査し、余分な値を拒否してframeを閉じ、宣言result列をpushする。implicit elseはnumeric型列でparamsとresultsの一致を必要とする。loopへの分岐はparameter列、他のlabelへの分岐はresult列を使う。

`br_if`の非分岐側には**宣言された型列**をpushし直す。unreachableだからBottomをそのまま残す実装では一致しない場合がある。`br_table`は全targetのarity一致を求めるが、型列自体の一律一致は求めない。Bottomで満たせる異なる型列の分岐先を受理するため、各targetを実際のsuffixと比較する。

## 正当性のための不変条件（証明方針）

1. 全chunkを展開した列が、通常のWasm検証アルゴリズムのoperand stackと等しい。
2. frame heightとunreachable flagが通常版と等しく、popがframe底を越えない。
3. pool内の型列は不変で、同一idは同一の列を指す。

push/pop/truncateは展開写像と可換である。同一id・同一終端のsliceの要素一致はpool不変性から従う。それ以外の比較は通常の要素照合へ戻る。unreachableの欠けたprefixをBottomとして扱う点を加え、各control transitionで不変条件を保つ、という帰納法が証明方針となる。

これは**機械検証済み証明ではない**。metadata委譲、parserの異常系、resource limitとの関係、全命令についての完備性は別途検証が要る。GC参照型のsubtypingでは単なるnumeric等値への帰着は使えない。

## 比較対象と反証

`flat`はcompact u8配列とslice比較を用いる。遅い要素別実装を意図的に対照にしていない。`cached`はflat bufferを保持し、論理pop後も1個のsignature certificateを再利用する。範囲を上書きしたときはcertificateを失効する。連続する同一signatureではこれでも展開・照合を省ける。

幅Wの同一signatureをR回通す特定系列ではsegmentの準備・検証費用をO(W+R)にできる。しかしcachedも同じ系列では同じ性質を持つ。前半A・後半Bを別のcallから受け取り、全体Vと照合する系列では、segmentにもO(W×R)の比較対象セルが残る。一般のbinaryに対してO(bytes)を証明したものではない。Wasm実装がarity上限を固定する場合、元方式もその上限を定数としたO(bytes)になり得る。

segmentはsingletonにもchunkを作るため、最初にW個のconstantを積む場合は最大W個のchunkとcapacityを確保する。したがって実装全体のstack memory削減も保証しない。
