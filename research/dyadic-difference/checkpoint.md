# 到達点と次の判断

2026-10-22。前turnのreverse-observerは監査・資料保存を完了したprogress。今回は差分だけの実行という別方向を実装し、静的回復への修正と公開問い合わせによる再反証まで進めた。主発明の確立は未達で、goalはactive。

- dyadic-difference-v1：36条件、正30/unique正20、247,830呼出し一致、bad6反例。静的回復12、8条件は元と異なる係数の等価関数。81pins。
- performance-v1：36process/252batch、短batch0。delta/naive比0.989/1.023/0.773。77pins。
- audit-v1：36本byte再現、helper56,448、WABT240、小環960設定196,416入力、追加拒否3、静的回復60反復。342pins。session49645はexit0確認済み。
- guarded-v1：正36/unique正20、297,396呼出し。全18条件を各34公開問い合わせで回復。静的回復6拒否を保護成功に数えない。条件外の反例も保存。94pins。
- guarded-performance-v1：36process/252batch、短batch0。guarded/plain比101.051/97.973/63.342。77pins。
- guarded-audit-v1：36本byte再現、WABT288、元/差分/guardedの問い合わせtranscript一致。220pins。
- high-degree-v1：1再帰式の深さ5/12/20、raw/O3と回復。12条件49,260呼出し、WABT96。6条件を各34queryで回復し次数32/30/30。70pins。
- report-v1：上記7directoryの全pinsを検証しfacts/comparisonを生成。3pins。

主producerのpolynomial degree capとperformanceのvariant選択は修正版で拡張した。初版のsource snapshotを上書きせず、byte再生成は各監査に保存。全processはexit0確認済みで現在の待機対象なし。

次の方向を選ぶ条件：一変数の整数係数多項式mod2^32は次数を増しても34点の回復対象になる。このclassに留まる差分・off-path noise・係数変更を新しい独立案として再開しない。多変数・非多項式へ移すだけでも新規性は生じず、具体的な生成規則と既存解析への費用差が必要。先の有限環残差方式の限定した構成候補は保持し、今回の失敗と混同しない。
