# 継続用チェックポイント

2026-10-23。主候補不採用という判定まで完了。研究全体の目標達成ではない。

結果は`results/invention-20261023/span-mask-{main,io,peel,runtime,audit,report}-v1`。全実行終了。主50対象158,558呼出し。全数学習12/12。逆shear5/6、残りpolicy24-dependentはBDD node上限で、全数学習では回復済み。実行45process315batch、10ms未満0。報告作成時に532保存pinsを確認。

借用メモリ案は`catalytic-memory-gate-v2`と`catalytic-memory-audit-v1`。v1のreader不備は保存・除外。18対象76,374呼出し、6/6回復、誤ったtrap処理2件を検出。独立WABT72呼出し＋72memory照合。全実行終了。

追加検索は[next-gates.md](next-gates.md)。動的配置の現案も近い特許があり未実装。全数学習を遅くするためだけに入力数を増やす、混合seedを増やす、変換名を変える、という変更を別発明に数えない。

変更を保存しているがcommit/push/公開/出願はしていない。既存の`paper/main.tex`と`paper/README.md`には手を加えていない。週単位使用率3%は確認できたが厳密なトークン残高は不明。再開時は完了した測定を再実行せず、現在の新規性評価と先行技術の境界から続ける。
