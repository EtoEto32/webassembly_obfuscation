# 到達点

相互作用改良の最終確認：[energy-interactions-verification-v1.json](../../results/invention-20261022/energy-interactions-verification-v1.json)。616ファイルのhash、現在の実測source、集計値、修正版の最小selector引数数を検査済み。次turnでenergyの係数や局所文法上限を再び変えるだけの候補を増やさない。

2026-10-22相互作用改良：[interactions-analysis.md](interactions-analysis.md)。前turnはprogress。今回はメモリ案の近接先行構成を確認後、energyの符号付き相互作用を全状態制約で合成。初期版の同値energyでの選択の弱点を発見し、全2引数selectorを排除する条件へ修正した。両版の全12条件が未変更の最小化消去で回復。主・性能・監査は各exit0、性能session18438/26502も終了確認済み。live handleなし。この方向は3設計段階で不採用。主目標は未達でactive。

改良の最終確認：[energy-relaxed-verification-v1.json](../../results/invention-20261022/energy-relaxed-verification-v1.json)。5directoryの596ファイルhash、実測source一致、Python5/JS2構文、集計値・資料リンクを検査済み。既存のpaper/main.tex、paper/README.mdの無関係な変更は触っていない。研究全体の完了扱いはしていない。

2026-10-22追加：直前の状況説明turnはno progress。今回は[全体収束を使う改良](relaxed-analysis.md)を実装してprogress。`energy-relaxed-v1`（session26966 exit0）、`energy-relaxed-coupled-v1`、`energy-relaxed-audit-v1`、`energy-relaxed-performance-v1`、`energy-relaxed-report-v1`は全てexit0。live handleなし。70条件・180,420通常呼出し、2,922,496全初期値probe、28回復、248消去SMT、70 byte再現、WABT280呼出し。局所逆向きでも正答する例を得たが、消去攻撃で回復でき、元版比約172倍。主発明には不採用でgoalはactive。重み合成の変種を次の独立案に数えない。

2026-10-22。前turnの新規性回答はno progress。本turnは新しい候補の具体化・先行調査・実Wasm生成・正当性・攻撃・費用・反例を実施したprogress。主目標は未達、goalはactive。

- `energy-descent-v1`: exit0。正42条件136,444呼出し一致、18回復、等重み6条件すべて誤答。
- `energy-descent-performance-v1`: session3313のexit0を確認。45process/315batch、短すぎるbatch0。
- `energy-descent-audit-v1`: exit0。48 byte再現、WABT168、局所規則336、全初期値小例、改変評価器・不適用source拒否。
- `energy-descent-report-v1`: encoding宣言修正後exit0。3結果directoryのpinsを検証、性能用Wasmとwrapperも別途確認。現在live handleなし。

主発明には採用しない。任意状態で一座標更新を必ず元ゲートへ向ける条件を使う限り、その更新の意味を解析側にも与える。次案で重み・極性・単項式の数を変えるだけの変種を数えない。全体の正当性から局所更新が直ちに一意にならない構成が必要だが、単に複数状態をまとめるだけでは既存の符号化・block coordinate descentに近いため、次はその具体的差を先に調べる。
