# H: 待機集合を使う共有メモリの実体分割

2026-10-24。予算会計Fとは異なる原理の候補。新規性未確認。Nodeでshared WebAssembly.MemoryをstructuredCloneするとmemory/bufferの===は共にfalseだが、片方のwaitAsyncをもう片方のnotifyで起こせることを1条件で確認した後に、この評価計画を固定した。

課題: 信頼境界に渡された複数のshared memory wrapperが同じbyteを共有するかを、値の変更・native pointer・送信元の申告IDに頼らず識別する。用途は「二つのimportがデータ上で非aliasである」等の前提をguest起動前に検査すること。異なるMemory objectのindex統合を許可するものではない。grow semanticsやlimitsの同一性までは証明しない。

仮説: 同一byte offsetへ各wrapperからwaiterを一つずつ登録し、一つの代表にnotify-allを行うと、その共有実体のwaiterだけが解決する。notifyが返す件数と解決集合を照合してから次の代表へ進むことで、n登録+k通知でk個の同値類を回復できる。固定した短時間内に解決しなかったことを非aliasの証拠にしない。timeout/件数不一致はinconclusiveとして拒否する。

前提: trusted JS intrinsics、全wrapperはhost管理下、対象offsetへの外部wait/notify/writeがない静止期間、同じ実体の同じoffset、4B以上のshared memory。待機queueは変更するため「完全に副作用がない」とは言わない。任意の敵対的workerが動き続ける状況は対象外。作業は新規の小容量memoryとbenign Wasmに限定する。

比較: ===、正しいhost登録ID、各組のwaiter照合、提案の一括分割。host登録IDが正しく保存できるならそれが強い対照であり、本案が勝ると仮定しない。内容が等しい独立memoryも区別する。

正当性: n=1..6の全集合分割、各ラッパーを別々にclone、全byteのbefore/after hash照合。n=8/16/32/64は固定seedの追加分割。実2memory Wasmのstore/loadを使って分離guardの判定を確認する。零長、不適切offset、非shared、混入waiterを別に検査。後続ではworker経由のcloneとgrowthも試す。

性能: O(n)待機登録/O(k)通知という呼出し数とwall timeを区別し、nと同値類数を変えて反復する。RSSはprocess全体。期待する効果は===(ラッパー同一性)の誤判定回避とpairwise検査の削減。実装前から高速化や特許性を成功と決めない。

先行性の懸念: Shared Data Block+offsetでwaiter queueを識別することはECMAScriptの既存仕様である。単一pairの検査は仕様から直接導ける。一括分割とnon-alias受付への接続が当業者に自明なら主案不採用とする。
