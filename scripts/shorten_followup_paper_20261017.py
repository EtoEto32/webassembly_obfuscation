"""Condense inherited work while retaining the completed follow-up evaluation."""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
p = ROOT / 'paper/main.tex'
s = p.read_text(encoding='utf-8')
backup = ROOT / 'paper/revisions/before-eight-page-condensation-20261017'
backup.mkdir(parents=True, exist_ok=True)
for name in ('main.tex', 'main.pdf', 'references.bib'):
    target = backup / name
    if target.exists():
        raise SystemExit('Backup already exists; do not rerun.')
    shutil.copy2(ROOT / 'paper' / name, target)

def between(start, end, replacement):
    global s
    a = s.index(start)
    b = s.index(end, a)
    s = s[:a] + replacement + '\n\n' + s[b:]

between('コード変換の影響を調べるため，', '\\section{関連研究と本研究の貢献}', r'''以下では比較の基準を「基準版」，変換後を「変換版」と呼ぶ．基準版に難読化がないことは保証しない．主な貢献は，入力契約・実行部位・実際のWasmコンパイラを測定結果に対応付け，その結果から正規化の適用範囲を具体的な照合課題で検討する点にある．新しい難読化方式や検出回避能力，実世界での普及率は評価しない．''')

between('\\section{関連研究と本研究の貢献}', '\\section{対象と分析方法}', r'''\section{関連研究と本研究の貢献}
Cryptic Bytesはソース，LLVM中間表現，Wasmでの変換・検出と100秒間のハッシュ速度，生成コードサイズを扱う\cite{harnes2024}．WebAssembly diversification for malware evasionも通常6件・変換120件の約1000秒測定とプール検証を行う\cite{cabrera2023}．MineSweeperはWasmとasm.jsやCPU利用率の速度差を扱う\cite{konoth2018}．したがって，難読化後の採掘速度や生成コードサイズの測定自体を新規性とはしない．

Proof-of-Theftの確認した本文・補足には出力照合と反復ハッシュ速度の組合せはなかったが，配布物にhashrate.jsがあり，過去の測定未実施とは断定しない\cite{sermchaiwong2026}．SWAMPED第IV.D節はLiftoffを用い，ホスト関数を空の関数に置き換えて関数時間を測る\cite{kim2025}．本稿は必要なホスト処理を用意し，全体ハッシュの期待値一致を伴う比較を行う．通常コード・計測コードとの区別にはWasmBench\cite{hilbig2021}・SEISMIC\cite{wang2018seismic}，複雑な式の比較にはMBA-Blast\cite{liumba2021}を踏まえる．既存研究の評価を補い，入力・実行部位・コンパイラ条件と解析支援の適用範囲を結び付ける．''')

between('\\section{対象と分析方法}', '\\section{RQ1：確認した難読化の仕組みとデータセットの傾向}', r'''\section{対象と分析方法}
\subsection{対象と既存評価}
既存調査ではCryptic BytesのCryptoNight系列10プログラム・2最適化条件の20,460件を対応付けた．Proof-of-Theftでは計測用Wasabi版等を区別し，webminerpoolhashcnとxmr-wasmの各5件，SWAMPED入力の基準・nop挿入・整数定数分割3件，計13件で出力・速度・構造を評価した．同じSHAの再収録や共有実装を独立標本とみなさない．SHA-256，取得元リビジョン，設定，対応を保存し，WABT 1.0.42で検証・逆アセンブルした．WAT命令数・関数・分岐表・呼出し・セクションサイズを比較する．保存命令数は実行回数ではない．

出力はXMRig v6.18.0の公表v0入力5件（xmr-wasmは対応する3件）と期待値を使う\cite{xmrigvectors}．xmr-wasmではtargetを最大値としnonceが変わらないことも確認する．既存webminerpoolhashcnのcn-pico評価には保存済み受理出力13件も用いた．旧13件の速度は各3反復で，webminerpoolhashcnは1秒ウォームアップ・5秒計時，他は3秒・30秒以上だった．以下の固定コンパイラ測定とは混ぜて集計しない．外部通信・プールへの送信や報酬を伴わないローカル評価である．

\subsection{同条件生成と入力契約の確認}
\label{sec:followup-method}
追加評価は同じ変換処理，乱数種20261016，割合0.1，WABT版で，SWAMPED，xmr-wasm，webminerpoolhashcnの基準・nop・整数定数分割9件を生成した．公開SWAMPED変換コード\texttt{04e2bcc}の本体を保ち，WAT表示用アダプタを用いる．定数$c$を$a+b=c$とする整数式へ置き換え，浮動小数点誤差を避けてvariant\_2を対象外とした．同一条件なのはWasmの再組立てと変換であり，元C/C++のコンパイラ条件をそろえた再ビルドではない．公表117照合と参照由来nonce変更入力216照合の計333照合が一致した．3実装はCryptoNight・OpenAESの共有由来を持つ．

SWAMPEDの入口は第4引数の長さをスタックポインタで上書きし，先頭76バイトを固定幅で読む．3版で長さ引数27条件，短入力・履歴・末尾充填81条件を照合すると，同じ実効76バイトでは一致した．75番目のバイトは出力に影響し，76番目以降は影響しなかった（先頭を0番とする）．別配布webminerpoolhashcnでも14種類の実効入力が一致した．従来の1／8／32バイト入力の履歴依存は保持された末尾で再現でき，旧追加12入力は固定幅入口への差分検証と解釈する．任意長の正当性確認や全入力の同値性証明ではない．

\subsection{コンパイラ別の速度測定}
Windows上のネットワーク無効Linuxコンテナ，Intel Core i9-11900K，Node.js 18.20.4，V8 10.2.154.26-node.37，ワーカー1を用いる．メモリ1 GiB，1 CPU・ゲストCPU 0指定だが，物理CPUの排他的使用ではない．モジュール生成等のホスト側初期化は計時外とし，ハッシュ内部の初期化・解放とホスト呼出しループは含む．

予備72ブロックではLiftoff指定の24ブロックにTurboFanも混在したため，単独条件には使わない．本測定はLiftoff単独指定またはLiftoff無効化に加え，tier-up，dynamic-tiering，lazy-compilationを無効化した．生成9件に公開平坦化版と部位復元3版を加えた13件を，2モード各6巡回，3連続セッションで測る．各ブロックは新規プロセスで5秒以上ウォームアップ後30秒以上計時し，変換版を基準版で前後から挟む．基準同士の対照8組を含む全272ブロックを保持した．出力・終了状態・Wasmコンパイル記録を監査し，136ブロックずつが指定コンパイラだけを使い，計時区間内のWasmコンパイルは0件だった．JavaScript側JITは監査対象外である．

速度は完了ハッシュ数／経過時間（H/s），比は計時中央時刻で補間した前後基準に対して求め，6巡回の幾何平均を示す．18比較の区間は3セッションの平均対数比に対する探索的95\% $t$区間（自由度2）で，多重比較調整はしない．連続セッションの独立性・正規性は未検証で，確認的有意差や実用的同等性を主張しない．''')

between('\\section{RQ1：確認した難読化の仕組みとデータセットの傾向}', '\\section{RQ2：コード構造，出力の正しさ，計算速度}', r'''\section{RQ1：確認した機構と実行部位}
\label{sec:proof-mechanisms}
既存調査では平坦化，仮想化，算術式・定数の変換等を確認した．平坦化は状態値を更新し共通の選択処理へ戻る構造，仮想化は独自の命令列を読み解釈する構造として区別する．分岐表や間接呼出しは通常の暗号処理にもあり，計測コードによって命令数も増える．SEISMICと一致する計数命令を除くと通常版の全147・756関数と一致したA-Star・CreaturePackは，難読化とは別の比較例である．特徴の有無や公開ラベルだけで難読化を判定しない．

xmr-wasm平坦化版ではhash関数とXOR補助関数112・118，初期化等に状態による処理選択を確認した．分岐表を使わない平坦化もあった．関数111の未実行variantブロックで9,428行増え，その他3,609行は名前を対応付けると一致した．命令置換版には整数式の複雑化を確認したが，最大target条件では実行されない式もある．webminerpoolhashcnの5版はMakefileに同じ\texttt{-enable-bcfobf}があり，ラベルから手法を確定できない．公開版のビルド条件が異なる可能性を残す．

追加計数では基準・平坦化・命令置換の3版と公表v0入力3件で，16バイトXORの関数118は1ハッシュ当たり1,179,648回，8バイトXORの関数112は0回だった．基準版の5呼出し箇所は，主ループ内2箇所が各524,288回，同ループの追加ブロック内2箇所が0回，別ループの1箇所が131,072回で，主ループ内は合計1,048,576回である．初期化・解放の関数83・86も各1回呼ばれた．計数版を速度評価に使わず，回数から時間割合は推定しない．

\textbf{RQ1への回答：}ラベル・コード特徴・確認できた機構を区別する必要がある．同じ測定入力でも未実行の変換部位と頻出の補助関数があり，総命令数だけでは実行時負荷を表せない．''')

# Keep the original xmr runtime table as a compact anchor to inherited results.
tab_start = s.index('\\begin{table}[t]', s.index('\\label{sec:xmr-runtime}'))
tab_end = s.index('\\end{table}', tab_start) + len('\\end{table}')
old_table = s[tab_start:tab_end]
between('\\section{RQ2：コード構造，出力の正しさ，計算速度}', '\\subsection{コンパイラ別の追加性能評価と部位別比較}', r'''\section{RQ2：難読化前後の出力・構造・性能}
\subsection{既存評価の主要結果}
Cryptic Bytes 20,460件の静的比較では，未最適化の命令数比の中央値はTigress encodearithmetic 2.515，LLVM subobf 1.461，平坦化はLLVM 1.098・Tigress 1.394だった．手法・最適化条件で増加量が異なり，サイズや命令数だけで効果を順位付けできない．旧13件の出力は対応する公表入力と一致した．xmr-wasmでは表\ref{tab:xmr-runtime}の平坦化と命令置換の速度比が0.678・0.738となり，命令増加の順序と逆だった．ただし配布版のビルド条件は統一できず，偽の制御フロー版だけに明示された\texttt{-O2}の効果も分離できない．
''' + old_table + r'''
SWAMPEDの旧3反復ではnop・定数分割の命令数比1.097・1.034に対し速度中央値比は0.960・0.973だった．各巡回の比は1をまたぎ，基準自体も27.09～32.73 H/sに変動したため，小さい差を変換効果と断定しなかった．以下では同条件変換と実際のコンパイラ記録で補う．''')

between('\\subsection{既存の局所正規化・読み取り支援の評価}', '\\subsection{追加77条件の出力保持と関数対応付け}', r'''\subsection{既存評価と正規化の位置付け}
性能評価では命令削減と高速化が対応せず，頻出部位を復元した手動対照も自動正規化の成功例ではない．そこで，構造の整理，出力保持，具体的な解析課題を分けて正規化を検討する．既存の関数内nop除去と，連続整数定数のadd/sub/mul/and/or/xor畳み込みを用いる．32・64ビットの剰余を扱い，副作用・分岐を挟む式は変更せず，基準版・SHA・変換位置ログを判定に使わない．通常の局所簡約であり，新規アルゴリズムとは主張しない．

既存144静的条件と23バイナリ各6反復（計138回測定）では単純変換を整理でき，公表入力の出力を保持したが，一貫した速度改善は確認できなかった．通常コードの式も簡約されるため，規則適用を悪性判定に使えない．複雑な置換の読み取り支援では計183式・19,398有限入力を独立整数評価器と照合したが，多入力式は対象外だった．限定したXOR状態モデルの照合も自動平坦化解除ではない．MINOS公開重みの画素尺度を変えると144条件中21条件の予測が変わり，訓練重複・学習尺度が未確定のため検知改善を主張しない．以下はこれらの成果を引き継いだ追加比較である．''')

between('\\subsection{測定の解釈と限界}', '\\section{まとめ}', r'''\subsection{限界と再現性}
対象は共有由来を持つCryptoNight系列に偏り，単一ホスト・Node版での評価である．同一SHAや644関数を独立標本とみなさず，未知系統へ一般化しない．公開版の過去のビルド条件は統一できず，追加変換もC/C++の同一条件ビルドではない．Wasmコンパイル監査はJavaScript側JITやコード配置，処理別時間割合を確定するものではない．基準の変動と連続3セッションによる探索的区間を残す．

出力一致は有限の有効入力での結果で，全入力・初期メモリ・ホスト副作用の同値性証明ではない．機構の確認も選定箇所に限り，見落とし率や一般的な検知性能は評価していない．解析・執筆にはCodexを用い，式・状態・引数対応は独立した人手検証が必要である．SHA，版，生成条件，対応，生ログ，失敗と修正，測定順序，集計コードを保存した．旧成果と詳細な条件・内訳は研究記録に残し，短縮で未実測の候補を結果へ加えない．''')
p.write_text(s, encoding='utf-8')
print('Condensed legacy sections; detailed manuscript preserved:', backup)
