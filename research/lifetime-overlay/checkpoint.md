# 到達点

2026-10-22。前のgoal turnは新規性の現状説明だけでno progress。本turnは新しい配置仮説の選別、実Wasm変換・回復の実装、最適化後の未対応修正、正当性と費用の実験を行ったprogress。主発明の確立は未達、goalはactive。

- `lifetime-overlay-v1`：正27条件707,328呼出し。raw9回復、O3のlocal.tee9未対応。保持するが主結果には使わない。
- `lifetime-overlay-v2`：正36条件（byte異なる23本）、943,104呼出し、不一致0/予期しないtrap0。全18回復、bad3反例。
- `lifetime-overlay-performance-v1`：12条件の正当性を再確認、36 fresh process/252batch、10ms未満0。session46277のexit0確認済み。
- `lifetime-overlay-audit-v1`：主結果と性能pinsを確認。正36本byte再現、WABT144呼出し、6対象外拒否、4評価順/符号拡張ケース288呼出し、90回復timing。exit0。
- `lifetime-overlay-report-v1`：上記主結果/性能/監査pinsからfactsと比較表を作成。exit0。

後から配置のpage上限を明示する安全条件を追加した。既存36本は監査で同じbyteを再生成できた。過去source snapshotは上書きしていない。現在のlive processはない。

今回の結論：アドレスを固定した型の矛盾は増やせるが、生存区間を使う配置は既知のstack coloringと近く、到達定義を追えば短時間で回復できる。分岐16個が65,536経路を作るという数を解析の下界に使ってはならない。新しい独立発明として加算しない。

次の選別条件：定数アドレス・全幅store/load・入口状態に依存しない生存区間だけの配置変更は、typed reaching definitionsへ戻せるクラスとして扱う。単にbranchを深くする、セルを増やす、幅を変えるという修正は新原理と数えない。動的addressや呼出し間状態へ進む場合も、その追加が本来の計算に結び付くことと、alias要約・状態要約に対する費用を先に検討する。有限環残差方式の限定した構成候補の評価は、この失敗とは分けて保持する。
