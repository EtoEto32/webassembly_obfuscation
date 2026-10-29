# 到達点と次の選別条件

2026-10-22。前turnのlifetime-overlayは実装・回復・費用測定を完了したprogress。本turnも、持続状態の非単射表現を設計・実装し、公開I/O回復・前提検査・反例・測定まで進めたprogress。主発明の確立は未達。goalはactive。

- `torsion-state-v1`：正48条件（byte異なる27本）、807,024 step、6,816 reset、不一致0/予期しないtrap0。全24条件をreset1回＋step16回で回復。bad3反例。exit0。
- `torsion-state-performance-v1`：15条件×3 fresh process×7batch=315batch。10ms未満0。session73623のexit0確認済み。各targetを別途oracle再確認。
- `torsion-state-audit-v1`：上記pins確認、48本byte再現、全24binaryの線形・零初期/reset・状態数・更新後状態による観測を確認。WABT384 step。solver5,184系。核/観測条件2拒否。非線形例外・上限超過遅延の反例。上限17の修正で遅延系を34応答から回復し4,096呼出し一致。exit0。
- `torsion-state-report-v1`：3directoryのpinsを確認しfacts/comparisonを生成。exit0。現在のlive processはない。

本案は新しい独立発明として数えない。零因子と非単射状態は実際に含むが、入出力が既知上限の低次元線形系である限り、短い公開履歴からの回復が成立した。元の全状態の復元と、等価な小さい計算の回復を区別する。

次に避ける方向：この入出力クラスのまま状態を増やす、非線形な零項を足す、DやUの生成だけを複雑化しても、クラスのpromiseを知る解析者に対する16応答の結果を改善しない。次数上限を隠すことだけにも依存しない。実際の出力に必要な非線形計算や動的aliasへ進む場合は、既存の符号化と単なる型/命令変更からの差を先に検査する。既存の有限環残差構成候補は別途保持する。
