# Bの健全性条件と証明すべき範囲

この文書は前提付きの紙上論証であり、Coq等による実装の検証ではない。既知のframe性と静的効果解析を利用する。[Iris-Wasm](https://doi.org/10.1145/3591265)はWasmとhostの相互呼出しを扱う機械検証済み論理をすでに提供する。本試作をそれより強い検証基盤とはしない。

## 抽象値

`effects.py`の各localは、入口引数・i32定数・add/sub/andから成る式か、unknownを持つ。式があるならその評価値は、その解析経路に対応する実行状態のlocal値に等しい。unknownは全i32を表す。memory loadとglobal.getはunknownにする。値がunknownでも、それを固定アドレスへstoreする範囲は計算できる。

storeのアドレス式は値式より先に評価する。`local.tee`等が値式中でlocalを変えても、storeアドレスにはその前に確定した式を用いる。アドレス又はbulk長がunknownなら、関数全体を全コピーへ退避する。未知命令を副作用なしとして無視しない。

## 構造化制御

解析状態はlocal環境と制御移送先の組。`br_if`は落下する経路と分岐する経路の両方を残し、それぞれ別のlocal環境を渡す。block/ifを抜けるとbranch depthを一つ減らす。関数returnとtrapはその経路を終了する。条件が実行時には成立しない経路も残すため過大評価はある。

これにより、分岐でlocalへの代入が飛ばされても、その代入後の値を分岐先へ誤って伝えない。block内のstoreだけを列挙して、localを一本の環境で更新する実装では、この性質は成立しない。

直接呼出しは実引数の抽象式をcalleeのlocalへ代入して解析する。calleeのlocal変更をcallerへ反映しない。calleeが常にtrapする場合でも現在の実装はcaller継続を解析することがあり、余分な範囲を加える。過大評価だが未退避のwriteは生まない。再帰・loop・indirect call・値を返すcall・未知host importは全コピーへ退避する。

探索上限は256経路、20,000解析step。上限超過は全コピー。パースやWasm validationの失敗は実行許可に変換しない。巨大moduleの入力サイズ制限はまだ実装していない。

## prefixの書込み上界

受理した命令に関する構造帰納法で、各実行経路のstore/fill/copyの書込み範囲は、解析した経路のいずれかの範囲に含まれる。trap命令以前のstoreは消去しない。通常終了だけでなく、任意の有限prefixに対して同じ包含が必要である。

i32式の周回はmod 2^32、memargのoffsetは非周回として扱う。区間計算はJavaScriptの整数を正確に表せる範囲内（memory32のアドレスと長さ、offsetの和）で行う。範囲がmemory外へ伸びても、Rとの交差だけを保存する。これによって不要なbyteを保存する場合はあるが、trapによる全rollbackを仮定しない。

この論証には、WABTの正しいvalidation/正規化、parserと解析器の正しい実装、実行するbinaryと証拠対象の一致が必要。現状はテストで支持するだけで、これらをすべて証明したとはしない。

## 旧値view

Rは再入前に検証・固定し、S=R∩Wを保存する。実行前をM0、callback後をM1とすると、S内は保存値M0を使う。R\Sでは書込みがないためM1=M0。したがって旧値viewはR全体でM0と等しい。

この等式の使用期間が重要である。R\Sを元memoryから読む方式では、**callback終了からconsumer終了まで別のwriterを許可しない**。別callbackや共有writerが動けば、この証明は使えない。任意の期間保持するviewが必要なら、consumerに渡す前に全体をmaterializeするか、追加の書込み監視・保存を行う必要がある。現試作は同期consumerまでの契約のみ。

記憶量の主張は保存payloadについてであり、JS object、解析木、実行環境全体のRSSは別。全量materialize版には復帰後のR全体の確保・コピーが加わる。

## 検証の対応

- `compiler-v1/v2`: 同じ48 binary・同じ6,528入力。old-value viewを実行前の独立コピーと比較。
- `effects-audit-v1`: 128 binary、8,960入力、308 trap。memory全域の観測可能な変更が上界に入ることを照合。等値storeは動的比較から見えない。
- `audit-v1`: 小さな有限メモリの集合モデルで186,624照合。解析器実装自体の証明ではない。
- `consumer-v1`: 別processで4方式を比較し、測定外の元値checksumと方式間checksumを照合。byte単位の正当性検査は前記試験で別に行っている。
- `library-v1`: 第三者hash-wasm 4.12.0の48条件・1,680入力。元binaryとwrapperの挙動、旧stateのview、観測した変更の上界を確認。保存量の改善は0。
- `checker-audit-v1`: folded WATを使わずcode sectionを読む別のstack解析で98部分要約を確認。式の構造的包含による保守的な検査であり、意味論的な同値判定や機械検証済みの小さなproof kernelではない。

`byte-checker.py`を直接呼ぶ場合は、**同じbyte列を標準validatorで先に検証すること**がAPIの前提である。`check-certificate.py`はこの順序を実行し、単一memoryと入口signatureを照合する。parserを変えた二重実装により共通の実装ミスの一部を検出しやすくなるが、両実装が同じ誤った意味論を採用する可能性は残る。hostの排他期間は別の実行時前提である。
