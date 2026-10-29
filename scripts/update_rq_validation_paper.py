# -*- coding: utf-8 -*-
"""Integrate measured validation results into the existing paper, in place."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'paper/main.tex'
s=p.read_text(encoding='utf-8')
if r'\label{sec:additional-validation}' in s:
    raise SystemExit('Additional validation already integrated; edit current source instead.')
s=s.replace('全体の特徴抽出に加え，選定した35種類のバイナリについて個別の静的解析記録を作成し，変換前後の命令列，値の流れ，公開された計測コードを照合した．',
 '予備調査35種類に加え，元のプログラムが異なる対照20ファイルと探索用8ファイルを選び，変換前後の命令列と値の流れを照合した．追加検証では，A-StarとCreaturePackの計測更新列を除くと，元の全147関数と全756関数の命令列がそれぞれ一致した．base64-cliとseqtkでは，状態を介した処理と通常版の処理との対応を確認した．一方，探索用8ファイルの確認箇所では平坦化を確定できず，入力や型に応じた通常処理という説明が残った．')
s=s.replace('Corpus-wide feature extraction is combined with individual static analysis records for 35 distinct binaries, comparisons of paired programs, and inspection of value flows and public instrumentation code.',
 'Following a 35-binary pilot, we examine 20 paired-control files from eight different programs and eight exploratory corpus files. Removing instrumentation increments restores all 147 original functions in A-Star and all 756 in CreaturePack at the decoded-instruction level. State-dispatch payloads are matched to original computations in base64-cli and seqtk. Flattening remains unconfirmed at the inspected sites in the eight exploratory files, where input- or type-dependent processing remains an alternative explanation.')
s=s.replace('既存の予備実験に基づく実証的な分析として位置付け，','予備調査で整理した判断根拠を別のプログラムで検証する実証的な分析として位置付け，')
s=s.replace('個別に解析した記録は計35種類のバイナリファイルについて作成したが，すべての関数を詳しく調べたわけではない．','予備調査では35種類のバイナリを個別解析し，追加検証では別の28種類を解析した．いずれもすべての関数の意味を詳しく調べたわけではない．')
method=r'''
\subsection{追加検証の対象と評価単位}
\label{sec:additional-validation}
予備調査の結果を確認するため，乱数シード20261009で追加対象を固定した．WASMixerの既調査2本を除く名前付き基本アルゴリズムから3本，残るrealworldプログラムからbase64-cli，Cryptic Bytesのユーティリティ6本から2本，SEISMICの非採掘プログラムの対照を用意できる4本から2本を選んだ．選ばれたのはrandom，sumrec，decimaltohex，base64-cli，needleman\_wunsch，seqtk，A-Star，CreaturePackで，通常版と変換版を合わせて20ファイルである．予備調査で判断根拠の作成に使ったプログラムは含まない．ただし共通ライブラリの関数まで独立ではない．

別に，WasmMalのmalwareとSWAMPEDの実験用ファイルから，ループ内分岐表の有無で各2件，計8件を抽出した．予備調査35種類との同一SHA-256は除いたが，生成親が不明なため，これらは独立したプログラムによる検証とはせず探索用とした．全28入力のハッシュを照合し，選定枠と選定結果を保存した．

評価単位は確認した関数・変換箇所である．追加対象の選定後，短い関数を優先して命令列を追った．探索用資料では分岐表を持つ最短の関数と，該当する場合はループ内分岐表を持つ最短の関数を確認した．したがって関数の無作為標本ではない．対照の機械的比較は全対象関数に行ったが，意味の確認範囲と区別した．

分岐表などの存在だけを候補抽出とし，値の由来，状態更新，通常版との対応を確認した後の判断と比較した．不明なものを強制的に難読化・非難読化に分けなかった．比較コードは，予備調査の名前変更2組と4,051箇所の計測更新列を再現し，更新先が異なる列と加算値が1でない列を除外する対照で確認してから用いた．独立した正解ラベルによる分類精度の測定ではない．

'''
s=s.replace(r'\section{RQ1　通常処理・研究用計測コードとの区別}',method+r'\section{RQ1　通常処理・研究用計測コードとの区別}')
rq1=r'''
\subsection{別プログラムによる追加検証}
A-Starの計測版には2,756箇所，CreaturePackの計測版には8,526箇所の単位増分の更新列があった．同じglobalを読み，1を加えて書き戻す4命令を比較用の命令列から除くと，通常版の全147関数，全756関数が，命令・数値オペランド・ローカル宣言の比較でそれぞれ一致した．さらに各計測版には，上位・下位の値を返す計10関数と5変数をリセットする1関数が追加されていた．これは反復命令の存在だけより強い，計測処理としての根拠である．実行可能ファイルから計測を除去して動作を評価したものではない．

更新対象はA-Starではglobal 0--4，CreaturePackでは17--21であり，予備調査の11--15とは異なった．既知の番号や関数の完全一致に依存する照合だけでは，このような別実装への一般化は保証されない．本検証では同じ変数への読出し・加算・書戻しという関係と，通常版との対応を確認した．

通常処理の追加例として，CreaturePackの関数400は，引数で指定された位置から読み出した値と74のANDを分岐の選択値とし，8，16，0，10のいずれかを返す．関数名も数値入力の基数選択を示しており，この関数には状態を書き戻すループがない．分岐表があるという理由だけで平坦化と解釈すべきではない．

一方，base64-cliの関数515では，通常版の3回の書込みを保ちながら，local 3を0から1へ更新して分岐表へ戻る構造を確認した．通常処理の分岐表とこの変換例を区別できた根拠は，表の大きさではなく，状態の役割と元の処理との対応だった．

\subsection{誤認・見逃し・判別不能の扱い}
追加した3本のmemoryOB版ではXORが存在したが，鍵に相当するglobalは0から変化せず，非ゼロ鍵の暗号化という解釈は支持されなかった．計測の更新列を単なる難読化の冗長命令と解釈することも，通常版との一致によって退けられた．これらは候補抽出から判断に進む際の誤認例であり，実装済み分類器の誤検知率を測ったものではない．

seqtkでは，変換版と同じ関数番号の通常版を比較すると処理の対応を見落とす．別番号の2関数を候補として見つけ，状態0，1の順で実行する処理列を取り出すと，ローカル変数の対応付けの下で双方と一致した．一意の関数対応は決められない．needleman\_wunschでも状態を更新する構造は確認したが，元の関数との対応は確定できなかった．この区別を残し，確認済みの対照と同列には扱わない．

'''
s=s.replace(r'\subsection{RQ1への回答}',rq1+r'\subsection{RQ1への回答}')
rq2=r'''
\subsection{追加対象で確認した手法と未確定の事例}
base64-cliの関数6では，通常版の\texttt{call 708}が，定数709を使う間接呼出しに変わった．elementの709番は関数708を指しており，呼出し先を保った間接化を確認した．名前変更の3組では，randomとsumrecの全53関数，decimaltohexの全52関数が復号後の命令列では一致し，名前が変わった．

メモリ操作では，同じ3プログラムの確認箇所で，オフセット56の直接読込みが補助関数呼出しと32ビットへの変換に置き換わった．補助関数はアドレス範囲と幅で処理を分けていた．global 1の初期値は0で，書込みもimport/exportもなかったため，このXORを非ゼロ鍵の暗号化とみなさなかった．これらは共通ランタイムの処理であり，3種類の独立した方式を発見したことを意味しない．

Cryptic Bytesのseqtkでは，変換版の関数43がスタック上の状態を0，1と更新する．状態0で引数1と28を渡して関数263を呼び，結果を保存し，状態1で返す．状態管理を除く処理列は，ローカル変数を対応付けると通常版の関数11および45と一致した．2つの通常版関数は同一の命令列であり，対応の一意性は未確定である．

探索用のWasmMal・SWAMPED計8ファイルでは，確認した分岐表の選択値に，引数の型，入力バイト，メモリから読み出した値の加工が使われていた．符号拡張したバイトの0と37で処理を分ける例や，入力バイトから46を引く例では，文字列・数値の解析という説明が残った．これらの確認箇所では平坦化を確定しなかった．ファイル全体に難読化がないという結果ではない．

\begin{table*}[tb]
\caption{追加解析における資料別の手法・構造と確認根拠}
\ecaption{Mechanisms, structures, and evidence in the additional analysis.}
\label{tab:validation-mechanisms}
\centering\small
\begin{tabular}{p{29mm}p{37mm}p{77mm}}
\hline
資料／対象 & 確認した手法・構造 & 根拠と範囲 \\
\hline
WASMixer／base64-cli & 平坦化，呼出し間接化 & 関数515の状態0，1と元の書込み列の対応．関数6のテーブル参照先が元の関数708と一致．\\
WASMixer／基本3本 & 名前変更，メモリ操作の補助関数化 & 復号後の全関数の一致と名前の差．選定した読込み箇所と補助関数を照合．非ゼロ鍵の暗号化は未確認．\\
Cryptic Bytes／seqtk & 平坦化 & 状態をたどった処理列が通常版の2関数と一致．一意の対応は未確定．\\
Cryptic Bytes／needleman\_wunsch & 状態分岐構造 & 状態の初期化・読出し・更新・復帰を確認．元の関数との対応は未確定．\\
SEISMIC／非採掘2本 & 計測コード & 更新列を除くと元の全関数と一致．読出し10関数とリセット1関数を確認．難読化の確認例には数えない．\\
WasmMal・SWAMPED／探索8件 & 入力・型に依存する分岐 & 選択値を追跡したが，確認箇所で平坦化は確定せず．通常処理という説明が残る．\\
\hline
\end{tabular}
\end{table*}

表\ref{tab:validation-mechanisms}は選定対象の結果であり，手法の利用率ではない．SEISMICの確認対象にはWasmBench・WasmMalにも同一バイト列で収録されたものがあり，探索対象にも複数資料間の重複がある．同じ根拠を独立した複数の利用事例として数えない．

'''
s=s.replace(r'\subsection{RQ2への回答}',rq2+r'\subsection{RQ2への回答}')
s=s.replace('MineSweeper，SWAMPED，Proof-of-Theft，WasmBenchについては特徴分布の比較に含めたものの，各ファイルの難読化手法を網羅的に確定したわけではない．','追加検証では，別の対照でこれらの機構を確認する一方，WasmMal・SWAMPEDの探索対象では確認箇所の平坦化を確定できなかった．MineSweeper，Proof-of-Theft，WasmBenchも特徴分布の比較に含めたが，各資料の手法を網羅的に確定したわけではない．')
s=s.replace(r'\subsection{予備実験から主張できる範囲}',r'''\subsection{追加検証から得られた意味}
計測処理の照合が採掘以外の2プログラムでも成立したことから，更新対象の番号ではなく値の関係を確認する方法の有用性を事例として示せた．名前変更とメモリ操作の対照も追加したが，共通ランタイムを含むため，ファイル数だけで一般性を主張しない．探索用8件で平坦化を確定できなかった結果は，分岐表の存在から手法を決めることの限界を示す．一方，未確認の箇所の見逃しを評価していないため，難読化を高精度に識別できたとは結論しない．

\subsection{予備実験から主張できる範囲}''')
s=s.replace('したがって，表に示したのはコードの特徴を持つファイルの割合であり，平坦化や暗号化を確認した件数ではない．','特徴分布表はコードの特徴を持つファイルの割合であり，追加解析の手法表は確認箇所の結果である．両者を混同しない．')
s=s.replace(r'\section{まとめ}',r'''追加実験の選定条件は\texttt{rq-validation-selection.json}，入力検証は\texttt{input-verification.json}，機械的比較は\texttt{paired-comparisons.json}と\texttt{instrumentation-removal-check.json}，判断根拠と命令列は\texttt{review-ledger.json}に保存した．再実行用の測定・照合スクリプトも保存した．今後の人間によるレビューでは，状態の遷移先，seqtkのローカル変数対応，探索例の通常処理という代替説明を独立に確認する必要がある．

\section{まとめ}''')
s=s.replace('今後は個別解析の対象を拡大し，人間による独立レビューを加えて，手法ごとの確認範囲と判断の信頼性を検証する．','追加検証では，計測更新列を除くと別用途の2プログラムの全関数が通常版と一致すること，平坦化の状態を追うと通常版の処理に対応することを確認した．同時に，一意に対応付けられない例と，探索対象で手法を確定できない例も残した．今後は人間による独立レビューと未確認箇所の解析を進め，判断の信頼性と適用範囲を検証する．')
p.write_text(s,encoding='utf-8')
print('Updated existing paper/main.tex')
