"""Integrate measured controlled comparisons while preserving the existing paper/editor."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/runtime-mining/cross-dataset/swamped'
rows=json.loads((OUT/'controlled-pair-summary.json').read_text())
spec=json.loads((OUT/'controlled-pair-manifest.json').read_text())
report=json.loads((OUT/'controlled-pair-repeated-throughput.json').read_text())
assert report['status']=='complete' and len(report['samples'])==9
labels=['基準版','nop挿入','整数定数分割']
table=['\\hline',r'変換 & H/s中央値 & 最小--最大 & 命令数比 \\', '\\hline']
for label,r in zip(labels,rows):
    table.append(f"{label} & {r['median_hps']:.2f} & {r['min_hps']:.2f}--{r['max_hps']:.2f} & {r['instruction_ratio']:.3f} "+r'\\')
table.append('\\hline')
section=r'''\subsection{同一組立条件によるSWAMPED変換対の評価}
\label{sec:swamped-controlled}
SWAMPEDの公開変換コードの固定コミット\texttt{04e2bcc}を用いて，確認済みの入力標本にnop挿入と整数定数分割を適用した．これは今回生成した変換版であり，既報の変換済み配布標本を再評価したものとは区別する．変換関数の本体を保持し，WAT命令列を渡すアダプタを用いた．位置選択は元コードと同じbeta(1,1)分布を用い，再現用に乱数生成器を固定した．選択比は関数ごとの候補命令の0.1とし，候補がある場合の最低1か所という元実装の規則を保持した．整数定数分割では丸め誤差を混入させないため，浮動定数を含むvariant\_2関数を適用範囲から除いた．

nopはスタック・メモリ・制御を変えない命令であり，定数分割は整数定数$c$を$a+b=c$となる2定数と加算に置き換える．例えばvariant\_0関数の\texttt{i64.const 0}は，\texttt{i64.const -1}，\texttt{i64.const 1}，\texttt{i64.add}へ変わる．関数内の変更位置を保存し，この同値関係と基準版との対応を確認した．nopはNOPFUN関数，定数分割はCONSTFUN関数に適用された．ここでは計測用hookやカウンタ更新を挿入していない．両手法の構造変更は保証されるが，解析の困難さや検出回避の効果を示す実験ではない．

WABT 1.0.42で基準と変換版を同じ方法で組み立てた．基準版のSHA-256は元配布物と完全一致した．3標本とも公表v0入力5件が一致し，importとexportの一覧も変わらなかった．同じホスト処理・メモリ配置・入力・1 workerで，各3秒のウォームアップと30秒以上の3反復を行った．各反復で実行順をずらし，初期化に使う時刻を固定した．全9ブロックで最終出力と，測定後の公表入力5件への出力が一致した．外部通信を無効にしており，プール提出も採掘報酬も発生しない．
\begin{table}[t]
\centering\small
\caption{SWAMPED入力への自生成変換の同条件比較（各30秒以上，3反復）}
\label{tab:swamped-controlled}
\begin{tabular}{lrrr}
TABLE
\end{tabular}
\end{table}
\begin{figure*}[t]
\centering
\includegraphics[width=\textwidth]{../results/runtime-mining/cross-dataset/swamped/controlled-pair-throughput.pdf}
\caption{同条件の基準版に対する静的変化と速度比．エラーバーは反復の最小・最大で，信頼区間ではない．}
\label{fig:swamped-controlled}
\end{figure*}
nop版のサイズ比はNOPSIZE，命令数比はNOPINS，速度中央値比はNOPSPEEDであった．整数定数分割版では，それぞれCONSTSIZE，CONSTINS，CONST SPEEDとなった．一つの入力標本と各手法の一つの乱数設定による測定であり，この変化率を全標本へ一般化しない．追加命令の静的増加が，そのまま同じ割合の性能低下になるとは判断できない．Wasmエンジンによる最適化の関与は考えられるが，生成された機械語を確認していないため，命令が除去されたとは断定しない．

'''
section=section.replace('TABLE','\n'.join(table)).replace('NOPFUN',str(rows[1]['transformed_functions'])).replace('CONSTFUN',str(rows[2]['transformed_functions']))
for marker,value in [('NOPSIZE',rows[1]['size_ratio']),('NOPINS',rows[1]['instruction_ratio']),('NOPSPEED',rows[1]['throughput_ratio']),
                     ('CONSTSIZE',rows[2]['size_ratio']),('CONSTINS',rows[2]['instruction_ratio']),('CONST SPEED',rows[2]['throughput_ratio'])]:
    section=section.replace(marker,f'{value:.3f}')
p=ROOT/'paper/main.tex';s=p.read_text(encoding='utf-8')
if '\\label{sec:swamped-controlled}' not in s:s=s.replace('\\section{考察}',section+'\\section{考察}',1)
s=s.replace('\\section{RQ2：静的解析で調べた難読化によるコードの変化}','\\section{難読化に伴うコード構造・サイズの変化}')
s=s.replace('\\subsection{RQ2への回答}','\\subsection{静的な変化のまとめ}',1)
s=s.replace('\\section{RQ2：ハッシュ計算の正しさと性能の予備評価}','\\section{ハッシュ計算の正しさと性能}')
s=s.replace('同一条件の難読化版との対応はまだ構成していないため，難読化のオーバーヘッドを示す結果には含めない．', 'この測定単独では難読化のオーバーヘッドを示さず，後節で同条件の自生成変換対を別に比較する．')
s=s.replace('ビルド条件をそろえた対照は未完了である．', '元配布の難読化版をビルド条件から再現した対照は未完了である．SWAMPEDの自生成対では同じ組立条件の比較を追加した．')
s=s.replace('外部公開と投稿は本作業に含めない．', '外部公開と投稿は本作業に含めない．今後の実行は大学PCで報酬を発生させないローカル評価に限定し，既存のプール受理記録と追加の公表ベクトル照合を区別する．')
if '\\label{sec:rq2-answer}' not in s:
    answer=r'''\subsection{RQ2への回答}
\label{sec:rq2-answer}
評価した入力の範囲では，計算できた変換版も期待するハッシュ出力を保持した．一方，出力を照合できない配布標本もあり，実行制約と計算結果の不一致を区別した．速度と静的な増加量の関係は一様ではない．xmr-wasmの配布比較では平坦化と置換の増加量・速度低下の順序が一致せず，同一組立条件のSWAMPED自生成対でも，命令数比と速度比を別に確認する必要があった．各標本の変換範囲，最適化，ホスト処理を記録した範囲での結果であり，すべての採掘実装や難読化手法に共通する性能影響を確定したものではない．

'''
    s=s.replace('\\section{考察}',answer+'\\section{考察}',1)
p.write_text(s,encoding='utf-8')
print('Integrated completed SWAMPED controlled comparison and full RQ2 answer')
