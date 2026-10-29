# 到達点

2026-10-22。このgoal turnはprogress：新たな一次文献本文を読み、実Wasm変換・回復・反例・測定・監査を実行した。直前の状況報告turnはno progressと分類した。

最終[検証記録](../../results/invention-20261022/conditional-causality-verification-v1.json)：5directory・605ファイルのhash、現在sourceとの一致、Python/JS構文、集計、2性能版のbinary30本の一致、独立LCS計算によるschedule最短長、資料リンクを確認済み。

主目標の独立した新規性と保護効果は未達。条件別の循環する共有演算は不採用。既知schedule合成との対応と公開predecessor表の回復が理由で、入力条件数・seedだけを増やさない。energyの係数調整にも戻らない。

完了済み：

- `conditional-causality-v1`：30条件、126,000通常呼出し、12,288初期状態probe、12回復、3短schedule負例、1trap helper拒否。
- `conditional-causality-performance-v1`：session75354、exit0。較正上限による61短batchのため主比較に不採用。
- `conditional-causality-performance-v2`：session18968、exit0。45process/315batch、短batch0。再起動・継続poll不要。
- `conditional-causality-audit-v1`：96 helper SMT、24記号合成順、30 byte再現、WABT120呼出し、実行器改変3拒否。
- `conditional-causality-report-v1`：[comparison.md](../../results/invention-20261022/conditional-causality-report-v1/comparison.md)。回復O3は6本とも元O3とbyte一致。

現在liveなprocessはない。既存`paper/main.tex`と`paper/README.md`は触っていない。公開・push・課金なし。

次は、今回の共有回路を新しい発明へ読み替えず、公開された少数の条件への分解を越える機構とWasm固有の意味規則との関係を再検討する。実装済み方向の再測定だけで目標達成としない。
