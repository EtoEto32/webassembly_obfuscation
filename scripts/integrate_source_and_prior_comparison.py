"""Reflect source correspondence and audited prior evaluation differences, without new runtime experiments."""
import csv
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'results/runtime-mining/cross-dataset'
audit=json.loads((BASE/'proof-of-theft/xmr-source-correspondence.json').read_text())
assert len(audit['modules'])==5 and all(r['source_tree_identical_to_reference'] and r['source_file_count']==46 for r in audit['modules'])
prior=json.loads((BASE/'prior-work/evaluation-coverage.json').read_text())
rows=[]
for r in prior['reviewed_sources']:
    rows.append(dict(study=r['name'],primary_source=r['source'],reported_hash_rate=r.get('hash_rate_evaluated'),
                     reported_execution_time=r.get('execution_time_evaluated'),evidence=r['evidence'],
                     evaluation_role=r['current_role']))
with (BASE/'prior-work/evaluation-comparison.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
p=ROOT/'paper/main.tex';s=p.read_text(encoding='utf-8')
needle='xmr-wasmでは平坦化，命令置換，分割，偽制御フローのディレクトリ名に対応するフラグを確認した．'
if 'C/C++とヘッダ46ファイル' not in s:
    s=s.replace(needle,needle+'さらに5標本のディレクトリに同梱されたC/C++とヘッダ46ファイルを相対パスとSHA-256で照合すると，すべて通常版と一致した．従って配布ソース上は同じ実装を基にする対応を確認できる．ただし同梱ソースと実際の生成時のソースが同じだったか，コンパイラや既存のオブジェクトファイルも同じだったかまでは確定していない．',1)
if '\\label{tab:prior-performance}' not in s:
    table=r'''
\begin{table*}[t]
\centering\small
\caption{確認した先行評価と本研究の位置付け．未確認は調査した本文・補足・公開資料で報告を特定できないことを指し，世界で未評価という意味ではない．}
\label{tab:prior-performance}
\begin{tabular}{p{0.22\textwidth}p{0.36\textwidth}p{0.34\textwidth}}
\hline
研究 & 確認した既存の評価 & 本研究で扱う範囲 \\
\hline
Cryptic Bytes\cite{harnes2024} & 難読化後のハッシュ速度（100秒） & 既存評価済みの比較対象．静的機構と構造変化を照合．\\
WebAssembly diversification\cite{cabrera2023} & 通常版6・変換版120，約1000秒とプールによる検証 & 評価設計の参照．現在の追加実測は公表入力とローカル評価．\\
MineSweeper\cite{konoth2018} & 表10のWasm/asm.jsとCPU利用率による採掘速度 & 評価済みの参照資料．配布物全件の難読化効果とは区別．\\
Proof-of-Theft\cite{sermchaiwong2026} & 第6節のグラフ・検出評価．出力と反復hashes/sの対比較報告は未確認 & 配布標本2実装の出力・速度・機構を追加照合．hashrate.jsの存在も記録．\\
SWAMPED\cite{kim2025} & 第IV.D節の空のimportを使った実行時間評価 & 必要なホスト処理を復元した完全なハッシュ計算と，自生成変換対を評価．\\
MinerRay & 第6.4節の検出用グラフ構築・走査の時間とメモリ評価 & 採掘速度とは区別した調査対象．本稿の追加実測は未実施．\\
\hline
\end{tabular}
\end{table*}
'''
    s=s.replace('\\section{対象と分析方法}',table+'\n\\section{対象と分析方法}',1)
s=s.replace('既存の変換済みファイルを使った分析であり，新しい難読化アルゴリズムは提案しない．', '既存の変換済みファイルと，公開変換コードから生成した対照を用いる．新しい難読化アルゴリズムは提案しない．')
s=s.replace('複数実装を横断した長時間の反復評価は進行中である．', '複数の配布実装で反復測定を行ったが，実装間の系譜と長時間の安定性の確認は未完了である．')
# Preserve the measured controlled result in the conclusion, rather than a stale blanket claim.
old='結果は今回の入力・標本・条件に限られ，長時間評価とビルド条件をそろえた対照は継続中である．'
new='SWAMPEDの入力標本に公開変換コードから生成した同条件の対照では，nopと整数定数分割の命令数比は1.097と1.034，速度中央値比は0.960と0.973であった．反復範囲は重なり，小差を確定的な効果としない．結果は今回の入力・標本・条件に限られ，元配布の難読化版を再現する統一ビルドと長時間の安定性の確認は未完了である．'
s=s.replace(old,new)
p.write_text(s,encoding='utf-8')
print('Saved prior comparison CSV and integrated source correspondence, comparison table and conclusion')
