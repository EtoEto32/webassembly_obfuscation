# 例外参照を使う条件の遅延解釈：事前計画

2026-10-19。前ターンはdifference-boundaryの実装・反証・監査を完了したためprogress。今回は別原理を検査する。暗号化、絶対に解析できないという目標、検出回避は扱わない。

## 3方向の比較（新発明3件という認定ではない）

|候補|具体規則|差を検査する点|最も簡単な解除／Reject理由|
|---|---|---|---|
|A 構造化領域のタグ共用|分岐先ブロックをtry_tableのcatch先に変え、入れ子で衝突しないtagを共有する|タグと行先の一対一対応をなくす|最も近い一致handlerを探索するだけでbr depthへ戻る。Wasmのlabelそのものと同じ情報なので選定しない|
|B 例外参照packetの遅延解釈|入力の条件を一度だけtagにし、catch_all_refでexnrefに保持。複数のconsumerがthrow_refで再利用して別々の値を選ぶ|条件値を通常のi32ローカルに保持せず、生成と利用を分離。通常の最適化が消すか、方式既知のsum型解析の費用が増えるか|tagをboolへ写すsummaryで通常selectへ戻る可能性。例外利用自体は既知。今回の選定は反証可能性の高さによる|
|C stack-switch continuationの相互参照|再開先と受け渡し値を継続オブジェクトへ持たせる|分岐とcall stackの回復を同時に必要にする仮説|CPS/defunctionalization既知。対応エンジン・正当性条件・具体選択規則が未確定。未完成の方向を発明とは数えない|

## 固定する仮説

Bを限定実Wasm変換器へ実装する。直線のi32計算の中で、同じ純粋な条件で複数selectを行う箇所を選ぶ。条件を最初の利用前にexception packetへ変換し、以降のselectは同じpacketを異なるhandlerで解釈する。各handlerは二つの実値を引数に取り、tag0なら一方、tag1なら他方を返す。消費点ごとにtagの解釈を入れ替え、元selectの真偽側を対応して交換する。新しい名前や機能の移植だけを新規性とはしない。

元条件はi32.eqz等によるtotalな値であり、共有は不変な入力引数と定数からなる同一式に限定する。引数は関数内で更新できるので、変換はSSA記号式を追跡して同一性を確認する。変換対象は単一関数、i32のみ、直線のlocal代入・算術・select。memoryとtrap可能な算術は当初対象外。安全な投機移動を暗黙に仮定しない。

比較：plain / helper（通常selectを共通関数化）/ fresh（select毎にpacket生成）/ shared（条件式同一のpacket共有）。raw/O3、複数カーネル、fan-outの拡大。候補の核心はshared、freshはアブレーション。helperは自作対照であり、既存製品を再現したものではない。

保護課題：tag・handler・値の対応を解き、通常i32 selectによる等価実装を再生成する。解析者はバイナリと方式を知り、元ソース、生成seed、正解JSONを受け取らない。命令数だけを耐性と呼ばない。通常最適化残存だけでは成功にしない。

成功条件：正当性・複数条件での最適化後の残存に加え、適応的解析に対してhelperより費用に見合う追加効果を観測し、既知例外難読化との差を説明する。方式既知の局所summaryで線形時間に解除され、費用優位も弱いなら主方式に不採用。復元成功率だけでなく実行・解析費用を比較する。

検証：境界・乱数・同一instance反復、WABT interpreter、誤tag対照、対象外拒否、変換再現、ソースhash保存。性能：warmup後反復、fresh process、中央値と範囲、binary bytes、RSS、変換時間。例外object数は実装からの理論数としてRSSと区別。有限テストを全入力証明とはしない。

最も近い先行資料はWasm EH proposal/spec、Dolz/Parra 2008の例外opaque predicate、Batchelder/Hendren 2007のJava例外構造難読化、US7243340B2の例外handler内実行。本文確認範囲はprior-art.mdへ追記する。特許成立・権利範囲の結論は出さない。
