# Aの第2設計: 同じ限定処理計画から認可依存と実行を導く

2026-10-24、実装前。fence-negatives-v1が示した「権限注釈と実処理の食い違い」を対象とする。Aの設計修正であり4つ目の発明候補とは数えない。

WITと限定recipeから、一度だけ平坦な処理計画を作る。recipeはread/write、既読値参照、list反復、option分岐だけを持つ。read/write opcodeが必要権限を決めるため、独立のread/write権限注釈は入力にしない。計画に現れたresourceをborrow中にhost実体へ解決し、同じopcode列からticket依存と同期executorを構成する。受付に任意JS callbackを渡すAPIは公開しない。

仮説: 限定DSLの範囲では、誤注釈の余地と検査後の送信先再読取りを排除し、既存Aと同じ判定・効果を実現できる。業務処理そのものが正しいか、信頼するbackendが別の効果を持たないかは保証しない。readをwriteと書き違えれば、write権限を要求するか拒否されるが、業務上の誤りを理解して直すことはできない。

同じ実Component raw/opt、9要求×2alias×8失効事象でファイル内容と受付を独立oracleに比較する。追加で、不正recipe（未知opcode、未定義read結果、不正resource path、独立permission属性等）、外部callback、計画の観測コピーの書換え、二重受付を試す。代替として正しい手書き方式を維持し、弱い注釈ミスの対照だけに勝って新規性と結論しない。

意味保存条件: recipeが元の同期I/O順序・対象・値を表し、全ての効果が計画opcodeとして現れ、入力を固定し、executorと失効が同一thread上で直列化される。read結果に基づいて新しいresourceを選ぶ処理、ネットワーク、stream、例外回復、一般loop、非同期backendは対象外。

先行性への懸念: capability言語・effect system・小さなDSLのインタプリタ・生成された安全wrapperと近い。SHILL (OSDI 2014)等の一般原理を発明要素として数えない。WITのborrow寿命、具体的な処理計画、操作別世代検査の接続に非自明な差が残るかは別途調査する。
