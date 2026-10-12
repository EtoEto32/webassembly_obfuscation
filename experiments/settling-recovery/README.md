# 反復キャリーを用いた方式のバイナリからの構造復元

1. **状態: Inconclusive**。既存の棄却候補に対して、設計上の復元議論を実行可能な限定解析へ進めた。独立した新規難読化方式の研究目標は未達成で、作業を継続する。本解析器を新しい難読化アルゴリズムとは扱わない。

2. **達成事項**。元のDAG・manifest・名前付きWATを解析器へ渡さず、3本の保存済みraw Wasmから加算を含む計算DAGを復元し、ループのないWasmを生成した。事後比較では全3出力が保存済みのplainバイナリとバイト一致した。

3. **未達成事項**。新しい原理、SHA-256への新規変換、公平な比較での保護効果は未確立。本試験は特定の既存候補の修正方針を選ぶための反証であり、全体目標を復元器作成へ変更しない。

4. **規則と意味が保存される範囲**。解析器は二重ループの巡回更新を構造照合する。各sweepはn個のhandlerをそれぞれ1回実行し、加算handlerは旧carry Cを用いて

       S = A xor B xor C
       C' = ((A and B) or ((A xor B) and C)) << 1

   と更新する。親が確定した後、carryは32更新以内、Sは追加1更新以内に安定する。普通の純粋handlerは1更新。復元したDAGに T(v)=max T(parent)+cost(v) を割り当て、実際のsweepの回数が全T以上であることを確認する。巡回順はsweepごとに変わってよい。各sweepで全nodeを訪問するため、この上界に順序は不要。

   解析器は初期化が純粋であること、scheduler localとstate/carry localの非重複、全handler番号の連続性、親が入力またはstateであること、復元DAGが非循環であることも検査する。認識できない形は拒否。対応命令は元試作で用いたi32のmul/xor/rotl/lt_u/selectと上述carry。memory/import/trap/effectのあるプログラムは対象外。変換の説明はこの認識できる構文の範囲への帰納的議論であり、機械検証済みの一般Wasm証明ではない。

5. **先行研究・新規性**。2026-10-12に[Structural analysis attack on asynchronous obfuscated circuits](https://www.jstage.jst.go.jp/article/elex/21/11/21_21.20240107/_article)の出版社掲載要旨と書誌情報を再確認した。2024年、Wang・Xiong・Huang。信号遷移グラフとパイプライン構造による鍵候補削減とSATを扱う。本試験は鍵のないソフトウェアの既知キャリーの漸化式を扱い、論文の手法や実験を再現したものではない。今回も本文全体を読んだとは扱わない。新たな文献検索ではなく、旧記録の直接リンクを再確認した。

   | 比較項目 | 本試験の判断 |
   | --- | --- |
   | 数学的な原理 | 通常の全加算器と有限反復の安定性 |
   | 表現体系 | 元の値とキャリーの補助値が残る既存試作 |
   | 状態変換 | 安定した後の加算へ置換可能 |
   | 依存関係 | バイナリのlocal参照から元のDAGが抽出できた |
   | 困難性 | 不要な反復回数では構造復元を妨げられなかった |
   | 一般化 | rawの特定構文族に限定。O2や一般async方式は未評価 |

6. **再利用成果**。`tmp/settling-carry/`のraw3本・inputs・manifestと独立したBigInt参照実装を利用。バイナリは旧manifestのハッシュと照合し、現在のランタイムでも出力確認できたため、この評価で分類A。以前のtiming記録は再測定せず本試験の実測に混ぜない。`experiments/sha256-cobra-check/check.py`からWABT出力のS式parserのみimportして使用し、CoBRA/Docker処理は呼ばない。parserコードハッシュを各certificateへ保存。原稿と以前の実験は変更していない。

7. **実装・正確性**。Python3.12.14、WABT1.0.42、Node24.15.0 / V8 13.6.233.17-node.48。各1,267入力（既存243境界+1,024固定乱数）で、元Wasm・復元Wasmを独立したBigInt参照実装と照合。不一致0。3,801入力組、7,602 Wasm対oracle比較。入力データ一式・manifestのSHA256、全出力、各バイナリハッシュを保存した。有限個の入力によるテストと上記意味保存の議論は別である。

   対照としてshiftを2に変更、sweep上限を1に変更、stateへ自己依存を追加した3本を実際にWasmへcompile/validateし、すべて解析器が所定の理由で受理を拒否した。これは誤受理ゼロの一般保証でも、その3本すべての出力が常に誤るという主張でもない。

8. **攻撃結果と比較**。方式を知る静的解析者。入力はバイナリのみ、元の値やトレースの問い合わせは0。コードからスケジューラ構文を認識するため、方式を知らない状態での解析ではない。別プロセスのrecover.pyは元のDAG・manifest・normalバイナリを読まないが、OS権限でそれらを隔離した実験ではない。実装を読んでアクセス範囲を確認できる。verify.cjsのみが正解のDAGと比較する。3/3を復元し、保存済みのplain版とのバイト一致も事後に確認。元の変数名・ソースコード復元とは区別する。

9. **費用・最適化**。

   | 対象 | 入力bytes | 復元bytes | 検出したキャリーを用いた加算 | 入力sweep数 |
   | --- | ---: | ---: | ---: | ---: |
   | mixed | 293 | 76 | 2 | 68 |
   | cross | 315 | 76 | 3 | 100 |
   | select | 326 | 85 | 2 | 69 |

   元の試作のO2版は今回未試験。速度の比較・統計的な解析時間比較は実施しない。各解析コマンドは観測上1秒未満、ただしこれを性能優位の指標としない。事前予算3本・対照3本・各コマンド60秒・作業25分。

10. **改善サイクルへの判断**。前回の「元のDAGが露出している」という説明を、raw binaryからの抽出結果で裏付けた。sweep順の乱数化・反復数増加だけでは、この解析の入力となるhandler本体と親参照が変わらない。次案はそれらを変える具体的な規則が必要。一般の循環計算や未知符号化の復元まで示したとはしない。新規性がないまま本方式をSHAへ拡張しない。

11. **実生成Before/After**。`artifacts/{mixed,cross,select}/input.wat` が実際の入力バイナリの逆アセンブル、`recovered.wat` が解析器の生成物、`recovered.pretty.wat` は生成バイナリを再逆アセンブルした表示用、`recovery.diff` は差分。certificateにhandlerの元AST、復元式、トポロジカル順序、上界、入力/出力ハッシュを保存。

   mixedの最初のhandler（表示用抜粋）は次へ置換される。変数番号はバイナリ由来。

       Before: local6 = (local0 xor local1) xor local7
               local7 = ((local0 and local1) or ((local0 xor local1) and local7)) << 1
       After:  local6 = local0 + local1  (mod 2^32)

   Afterを元ループ内で一箇所だけ実行する変換ではない。全体の安定性上界を検査したうえで、全handlerをDAG順に一度だけ計算し直す。

12. **成果物と再現**。リポジトリルートから、まだ存在しない出力ディレクトリを指定する。

       .\.tools\runtime-analysis-py312\Scripts\python.exe experiments/settling-recovery/recover.py tmp/settling-carry/mixed.carry.wasm experiments/settling-recovery/fresh/mixed

   cross/selectも同様。元のartifacts出力は上書きしない。verify.cjs/controls.pyを再実行する場合は、本ディレクトリのコピーをexperiments直下に作り、コピー内artifactsを含めずに3本をartifacts/{name}へ再生成して実行する。既存入力データ一式・manifestとparserへの相対参照を保持する。`artifacts/verification.json`、`artifacts/controls/results.json`、`artifacts/plain-comparison.json`が結果。対照の変更WAT/Wasmと拒否stderrも保存。

13. **限界と未解決事項**。認識する構文の変更、最適化によるlocal.tee化、複雑な命令融合、未知の演算符号化、メモリ状態には対応していない。未対応であることを解析への耐性として評価しない。全体目標に必要な独立した原理と解析上の改善は依然不足する。この結果が除外するのは、露出したDAGをそのままに反復実行を増やす具体方針である。
