"""Integrate completed evaluations; preserve the preceding manuscript verbatim."""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
p = ROOT / 'paper/main.tex'
s = p.read_text(encoding='utf-8')
backup = ROOT / 'paper/revisions/before-followup-integration-20261017'
backup.mkdir(parents=True, exist_ok=True)
for name in ('main.tex', 'main.pdf', 'references.bib'):
    dest = backup / name
    if dest.exists():
        raise SystemExit('Backup already exists; do not rerun integration.')
    shutil.copy2(ROOT / 'paper' / name, dest)

def replace(old, new):
    global s
    assert s.count(old) == 1, old[:100]
    s = s.replace(old, new)

abstract = r'''WebAssembly（Wasm）はWebブラウザ上で高速な処理を実現する一方，利用者の同意なく計算資源を使うクリプトジャッキングにも用いられ，難読化による検知の困難化が指摘されている．本研究はコード正規化モジュールの開発に向け，公開された採掘用Wasmの難読化前後の構造，計算結果，実行性能を調査する．既存13件の比較に加え，有効入力を確認し，Wasmコンパイラ条件を固定した272測定ブロックと補助関数の実行回数を照合した．命令数や生成コードサイズの変化だけでは性能を説明できず，実行部位とコンパイラ条件を対応付ける必要があった．これを踏まえて既存の局所正規化と最適化を77条件で比較し，単純変換の整理と既知由来の関数の厳密照合を補助する効果を確認した．複雑な式・状態遷移の処理や最適化後の対応付けには課題が残り，正規化の適用条件と開発上の課題を検討する．'''
start = s.index('\\begin{abstract}') + len('\\begin{abstract}')
end = s.index('\\end{abstract}')
s = s[:start] + '\n' + abstract + '\n' + s[end:]
start = s.index('\\begin{eabstract}') + len('\\begin{eabstract}')
end = s.index('\\end{eabstract}')
s = s[:start] + r'''
WebAssembly enables high-performance computation but is also used for cryptojacking, whose detection can be hindered by obfuscation. Toward a code normalization module, we investigate structure, outputs, and throughput before and after obfuscation in public mining artifacts. We extend an existing 13-artifact comparison with input-contract checks, 272 measurement blocks under fixed Wasm compiler modes, and helper-call counts. Stored instruction counts and generated code sizes alone do not explain throughput. Guided by these observations, we compare existing local simplification rules and optimization in 77 conditions. Local rules recover simple transformations and assist strict matching of known-origin functions, while complex expressions, state transitions, and function tracking after optimization remain challenges. We discuss applicability and development requirements without claiming general deobfuscation or improved detection.
''' + s[end:]
replace('本稿では各Wasmバイナリの難読化の仕組みを調べ，出力の正しさを確認した上で，ハッシュ計算速度との関係を分析する．', '本稿では，解析・検知に適した形式へ変換するコード正規化モジュールの開発に向け，まず難読化の仕組み，出力の正しさ，ハッシュ計算速度を評価する．その結果に基づき，既存の正規化・最適化によって整理できる範囲と，複雑な変換に残る課題を検討する．')
replace('\\item SWAMPEDを同条件で比較し，命令増加と出力保持を確認したが，速度差は測定変動と重なった．', '\\item SWAMPEDの既存比較を保持し，3実装への同条件変換とコンパイラ別測定を追加した．小さい速度差には変動が残り，頻繁に通る補助関数の部位別比較で総命令数との違いを示した．')
replace('\\item 局所正規化と式・状態モデルを予備比較し，23バイナリの6反復で構造の整理と速度改善の違いを示し，解析支援を検討した．', '\\item 局所正規化と式・状態モデルの既存比較，23バイナリの6反復に加え，77条件の出力照合と関数対応付けを評価し，性能評価から正規化の適用条件を検討した．')
replace('本研究は未報告の測定値だけを新規性とせず，', 'Cryptic Bytesのハッシュ速度・生成コードサイズの評価とSWAMPEDの関数時間評価を踏まえ，本研究は未報告の測定値だけを新規性とせず，')
anchor = '\\section{RQ1：確認した難読化の仕組みとデータセットの傾向}'
replace(anchor, r'''\subsection{追加評価の入力契約と測定条件}
\label{sec:followup-method}
既存の13件と23バイナリの結果は，各時点の測定条件のまま保持する．追加評価ではまずSWAMPEDの入口を調査した．第4引数の長さはスタックポインタで上書きされ，先頭76バイトを固定幅で読む．3版での長さ引数27条件，短入力・履歴・末尾充填81条件は，同じ実効76バイトにそろえると一致した．75番目のバイトの変更は出力に影響し，76番目以降は影響しなかった（先頭を0番とする）．別配布webminerpoolhashcnでも14種類の実効入力が一致したが，共有由来のある参照による補助確認である．

同じ変換処理・乱数種20261016・割合0.1・WABT版で，SWAMPED，xmr-wasm，webminerpoolhashcnの基準・nop・整数定数分割の9件を生成した．Wasmの再組立てと変換条件をそろえた比較であり，元のC/C++を同一コンパイラで再ビルドした比較ではない．公表期待値117照合と参照由来のnonce変更入力216照合の計333照合が一致した．3実装にはCryptoNight・OpenAESの共有由来があり，独立した3アルゴリズムとはみなさない．

追加予備測定72ブロックのうち，当初Liftoffを指定した24ブロックはTurboFanも混在したため，単独コンパイラの結果に使わない．本測定では同じNode版のLiftoff単独指定またはLiftoff無効化に加え，tier-up，dynamic-tiering，lazy-compilationを無効にした．各ブロックを新規プロセスとし，5秒以上のウォームアップ後30秒以上測定する．9件に公開平坦化版と部位復元3版を加えた13件を2モード各6巡回，3連続セッションで測定した．近接基準を変換版の前後に配置し，基準同士の対照8組を含む全272ブロックを保持した．各ブロックの出力・終了状態・Wasmコンパイル記録を監査し，136ブロックずつが指定したコンパイラだけを使い，計時区間内のWasmコンパイルは0件だった．JavaScript側JITをすべて除外した監査ではない．

速度比は計時中央時刻で前後の基準速度を補間し，6巡回の比の幾何平均で示す．18比較の個別区間は3セッションの平均対数比に対する探索的95\% $t$区間（自由度2）で，多重比較調整はしない．連続セッションの独立性・正規性は未検証であり，確認的有意差や実用的同等性を主張しない．ネットワーク無効コンテナで1 CPU，ゲストCPU 0，メモリ1 GiBを指定したが，物理CPUの排他的使用ではない．完全なフラグ・入力・巡回順・生ログは再現資料に記録した．

''' + anchor)
replace('関数111から補助関数118への2箇所の呼び出しはメインループ内にあるが，初期化などはループの外にある．実行時の呼び出し回数や，各処理が実行時間に占める割合は測定していない．', '追加計数では，基準・平坦化・命令置換の3版と公表v0入力3件で，16バイトXORの関数118は1ハッシュ当たり1,179,648回，8バイトXORの関数112は0回だった．基準版の関数118への5呼出し箇所のうち，主ループ内2箇所が各524,288回，同ループの追加ブロック内2箇所が0回，別ループの1箇所が131,072回だった．主ループ内の合計は1,048,576回である．関数83・86の初期化・解放も各1回呼ばれ，ハッシュ計時に含まれる．計数版は速度測定に用いず，呼出し回数から実行時間の割合は推定しない．')
anchor = '\\subsection{RQ2への回答}'
replace(anchor, r'''\subsection{コンパイラ別の追加性能評価と部位別比較}
\label{sec:followup-performance}
表\ref{tab:followup-performance}に同条件生成6変換版の結果を示す．各実装自身の基準に対する比であり，実装間の絶対速度を比較しない．nop挿入による保存命令数の増加は約9～10\%だが，TurboFanの報告する生成コードサイズは基準と同じだった．同サイズは機械語の同一性や負荷0を証明しない．生成コードサイズは実行しない関数も含むコンパイル結果の合計で，割当メモリ量や実行命令数とは異なる．
\begin{table}[t]
\centering\small
\caption{追加生成版の基準比．LFはLiftoff，TFはTurboFan．速度比は6巡回の幾何平均．}
\label{tab:followup-performance}
\setlength{\tabcolsep}{2.6pt}
\begin{tabular}{llrrr}
\hline
実装 & 変換 & 命令数比 & LF速度比 & TF速度比 \\
\hline
SWAMPED & nop & 1.0973 & 0.9837 & 1.0035 \\
 & 定数分割 & 1.0341 & 0.9077 & 1.0121 \\
xmr-wasm & nop & 1.0977 & 0.9988 & 0.9859 \\
 & 定数分割 & 1.0136 & 1.0014 & 0.9897 \\
webminerpool & nop & 1.0914 & 0.9908 & 1.0228 \\
 & 定数分割 & 1.0162 & 1.0019 & 1.0202 \\
\hline
\end{tabular}
\end{table}
SWAMPED定数分割のLiftoff速度比は6巡回すべてで1未満（0.8511～0.9554），幾何平均0.9077だったが，TurboFanでは0.9273～1.0743となった．生成コードサイズ比もそれぞれ1.0486と1.0009で異なった．他の実装にも共通する低下とは結論しない．基準の前後比自体に0.8438～1.2029の変動が残り，数\%の差を変換効果と断定しない．

同じxmr-wasm平坦化モジュールのXOR関数本体だけを元の処理へ手動復元し，他の関数と署名を保った対照も作成した．16バイトXORだけの復元では命令数が91個（約0.05\%），生成コードサイズが約0.06～0.07\%減った一方，速度比はLiftoffで1.4692，TurboFanで1.3857だった．6巡回の範囲も各1.3819～1.5327，1.3227～1.4690となった．未実行の8バイトXORだけの復元では0.9922，1.0148，両方では1.4426，1.3450だった．局所の影響は加算できるとは限らない．各復元版の公表3入力は一致したが，手動の部位比較であり自動正規化の成功例には数えない．
\begin{figure*}[t]
\centering
\includegraphics[width=0.86\textwidth]{../results/followup-evaluation-20261016/figures/confirmatory-speed-ratios.png}
\caption{追加評価のコンパイラ別速度比．各点は6巡回，中心と区間は幾何平均と探索的な個別95\%区間．前3パネルは各実装の基準，右下は同一平坦化版が基準である．区間の多重比較調整はしていない．}
\label{fig:followup-speed}
\end{figure*}
この結果は，保存された命令数だけでなく実行回数とコンパイラ条件を確認して，正規化の対象と評価指標を選ぶ必要性を示す．高速化と解析のための構造整理は別に評価する．

''' + anchor)
replace('実装に共通する傾向や手法単独の効果は未確定で，条件の異なる実装間の速度順位は付けない．', '追加評価でも3実装に共通する速度効果は確定できなかった．一方，同じ平坦化版の頻出部位を復元した対照では小さい総命令数差に対して大きい速度差があり，実行部位とコンパイラ条件の照合が必要だった．条件の異なる実装間の速度順位は付けない．')
replace('\\section{考察と限界}', '\\section{性能評価を踏まえたコード正規化の検討}')
replace('\\subsection{変換機構に基づく解析支援手法の検討}', '\\subsection{既存の局所正規化・読み取り支援の評価}')
replace('基準の1／8／32バイト入力は再利用履歴により出力が異なり，原因は未特定である．追加分は除外せず，新規コンテキスト同士と同履歴・同順序の基準と比較した．独立期待値による正しさの確認は公表5入力に限る．', '当時は基準の1／8／32バイト入力の履歴依存を未解明として，同履歴・同順序の基準と比較した．今回，固定76バイト読出しと残存末尾でこの差を再現できた（第\\ref{sec:followup-method}節）．従来の追加12入力はこの入口への差分検証であり，指定長の任意メッセージに対する正しさの確認ではない．公表76バイト5入力の既存結果は保持する．')
anchor = '\\subsection{測定の解釈と限界}'
replace(anchor, r'''\subsection{追加77条件の出力保持と関数対応付け}
\label{sec:followup-normalization}
性能評価で確認した単純変換と複雑な補助関数の違いを踏まえ，生成9件と公開平坦化・命令置換2件の計11入力で，既存の局所規則を変更せずに評価した．未処理，nop除去，整数定数畳み込み，両規則，Binaryen 133局所pass，O2，O3の7処理，計77条件で，出力は42種類のSHAとなった．基準にも同じ処理を適用し，許可するWasm機能をそろえた．O3はCryptic Bytesの比較を踏まえて加えたが，先行研究の固定コミットとBinaryen 133は異なり完全再現ではない．全条件がWABT検証を通過し，exportされた関数型・資源型と制限を保持した．型の一致は意味保存の証明ではない．

有効76バイト入力の新規状態・順方向・逆方向で計2,793照合（公表945，参照由来1,848）が一致した．最初の大バッチは1 GiB上限でメモリ不足終了したため，途中照合を完了扱いせず，成功済み条件を保持して残りを入力ごとに分割した．別枠の全77条件の再実行でも2,793照合が一致したが，主評価の標本数へ加えない．新たな正規化後速度測定は行わず，前節の一貫した速度改善を確認できなかった結果を引き継ぐ．

解析課題として，生成6対照の全640定義関数と，公開複雑版の確認済みXOR補助関数4件を，同処理した3基準モジュールの関数集合から探した．標準WATの構文指紋を厳密比較し，関数名・番号・型参照番号・呼出し先番号・由来ラベルは照合特徴から除く．型参照は型の構造へ置き換え，局所宣言・命令・その他の即値は残す．最適化後の採点用由来名は補助コピーにだけ付与し，全77条件で実出力と非カスタムセクションの内容が等しいことを確認した．複雑版は既知2関数ずつに限定し，全関数の対応を番号から推定しない．命令置換版の補助関数も有限テストで追加確認し，通常・平坦化・命令置換の3版で計2,094呼出しが一致した．全モジュールの同値性証明ではない．
\begin{table}[t]
\centering\small
\caption{既知由来644関数の厳密照合．複数は正解を含む複数候補，追跡不能は最適化後の由来を追えない対象．分母を固定する．}
\label{tab:followup-matching}
\setlength{\tabcolsep}{3pt}
\begin{tabular}{lrrrr}
\hline
処理 & 正しい一意 & 複数 & 未照合 & 追跡不能 \\
\hline
未処理 & 27 & 22 & 595 & 0 \\
nop除去 & 295 & 71 & 278 & 0 \\
整数定数畳み込み & 268 & 55 & 321 & 0 \\
両規則 & 536 & 104 & 4 & 0 \\
Binaryen局所 & 294 & 68 & 282 & 0 \\
Binaryen O2 & 274 & 18 & 65 & 287 \\
Binaryen O3 & 249 & 22 & 73 & 300 \\
\hline
\end{tabular}
\end{table}
全4,508問い合わせの結果を表\ref{tab:followup-matching}に示す．両規則での正しい一意照合は536／644（83.2\%）だった．生成対照では，SWAMPEDの2版が各30／30，xmr-wasmが各171／221，webminerpoolhashcnが各67／69で，残る104件は正解を含む複数候補だった．呼出し先番号等の除去も曖昧さの要因となる．複雑版の4関数は全処理で未照合だった．誤った一意照合は観測されなかったが，一般的な精度や誤検知率を示す評価ではない．

O2・O3で由来を追えた対象だけなら一意照合は274／357，249／344となるが，表では追跡不能287件・300件を分母に残した．削除・統合・インライン化と追跡喪失は完全には区別できない．モジュール全体の厳密照合も，生成6対照と複雑2版に対して未処理0／8，両規則6／8，局所pass3／8，O2・O3各2／8だった．これは元の構文と関数境界を保つ処理に有利な課題であり，既知由来の共有実装内での結果に限る．未照合は意味の相違や最適化失敗を示さず，未知系統への適用や人間の解析時間・検知改善も測っていない．処理・出力・WABT検証等を含む1入力1回の前処理時間の中央値は両規則484.3 ms，局所pass202.1 ms，O2 681.7 ms，O3 1,017.2 msであり，反復された速度優位性の評価ではない．

\subsection{正規化モジュールの適用条件と開発課題}
追加性能評価では命令数削減と速度改善を同一視できず，頻出部位と未実行部位を区別する必要があった．これを踏まえた比較では，単純変換への局所正規化は有限入力の出力を保ち，既知由来の厳密照合を補助する候補となった．複雑な式・状態遷移を同じ構文形へ戻せた証拠は得られず，既存の式比較・状態モデルと併用して検討する．不可能と結論するものではない．

開発には，まずホストと有効入力を確定し，整数幅・型・副作用・メモリ・分岐を考慮して書換え範囲を限定する必要がある．原本・生成物・規則と適用位置を保持し，正規化で失われる特徴を元の解析にも渡せるようにする．関数の由来を追えない対象と複数候補を隠さず，呼出し文脈等による絞込みを検討する．有用性は命令削減や高速化だけで判断せず，出力保持，構造の整理，具体的な解析課題，処理負担を分けて評価する．汎用的な平坦化解除と検知改善は今後の課題である．

''' + anchor)
replace('速度差の原因検証には実行経路・回数，JIT，生成機械語の確認が必要である．', '追加評価では実行回数とWasmコンパイラを確認したが，機械語内容や処理別の時間割合まで確定していない．生成コードサイズの一致を機械語の一致とは扱わない．')
replace('公開版のビルド条件は統一できず，追加6反復もSWAMPED入力1件の派生に限る．', '公開版のビルド条件は統一できない．既存の正規化後6反復はSWAMPED入力1件の派生に限り，今回の3実装の同条件変換も共有由来と単一ホスト・Node版の制約を持つ．')
start = s.index('\\section{まとめ}')
end = s.index('\\bibliographystyle', start)
s = s[:start] + r'''\section{まとめ}
公開採掘用Wasmの難読化の機構・構造を調べ，既存13件の出力・速度と追加272ブロックのコンパイラ別性能を実行部位に対応付けた．保存命令数や生成コードサイズの総量だけでは性能を説明できず，有効入力と実行箇所の確認が必要だった．この結果を踏まえ，既存の23バイナリ・6反復と式・状態モデルの成果を引き継ぎ，77条件の正規化・最適化と厳密照合を比較した．局所規則は単純変換の整理と既知由来の対応付けを補助したが，複雑な式・状態遷移，最適化後の由来追跡，複数候補への対処が残る．原本・適用記録を保持し，読み取り支援と併用する正規化モジュールを検討する．結論は対象標本と有限入力に限り，汎用的難読化解除，全入力の同値性，検知改善の達成は示さない．
''' + s[end:]
p.write_text(s, encoding='utf-8')
print('Integrated completed follow-up; prior source/PDF/bibliography preserved:', backup)
