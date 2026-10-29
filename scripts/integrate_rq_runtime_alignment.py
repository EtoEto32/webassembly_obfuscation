"""Explain the scope of the joined RQ1/RQ2 evidence in the existing paper."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'results/runtime-mining/cross-dataset'
report=json.loads((base/'rq1-rq2-runtime-evidence.json').read_text())
assert len(report['modules'])==13
p=ROOT/'paper/main.tex';s=p.read_text(encoding='utf-8')
needle='\\subsection{RQ1への回答}'
assert needle in s
paragraph='\\paragraph{RQ2の標本との対応}追加のローカル反復測定の13バイナリ（Proof-of-Theft配布10，SWAMPED入力1，自生成変換2）をSHA-256で照合し，配布設定，確認した機構，適用範囲，計測hookの有無，出力照合と速度の根拠を同じ一覧へまとめた．SWAMPEDの自生成対はnop挿入30関数3089箇所，整数定数分割29関数542箇所で，挿入命令の除去と定数式の復元により命令列全体が基準版に戻ることを確認した．これは元配布の変換版の機構を確認した結果ではない．一方，webminerpoolhashcnの設定不一致，xmr-wasmの分割・偽制御フローの機構未確認は一覧にも残し，出力一致だけで難読化ラベルを確定しない．webminerpoolhashcnの公表v0ベクトル照合と，速度測定で用いたcn-picoの受理済み出力照合はアルゴリズムを分けて記録する．\n\n'
if '\\paragraph{RQ2の標本との対応}' not in s:s=s.replace(needle,paragraph+needle,1)
s=s.replace('今後の実行は大学PCで報酬を発生させないローカル評価に限定し，', '大学PCでの新たな実行は指導教員の許可確認後とし，許可された場合も報酬を発生させないローカル評価に限定する．',1)
p.write_text(s,encoding='utf-8')
with (base/'proof-of-theft/resume-state.txt').open('a',encoding='utf-8') as f:
 f.write('\n追加進捗：link_runtime_rq_evidence.pyでローカル実測13SHAをRQ1機構・範囲・flags・hook・公表出力・速度・静的指標へ結合。rq1-rq2-runtime-evidence.csv/json保存。wmp公表cn/0と速度cn/picoの照合根拠を区別。xmr内部f111の変更存在と平坦化機構未分類を区別。SWAMPED自生成と元配布変換版を区別。原稿RQ1に13標本の対応と自生成機構確認を反映。先生許可まで新規実行控え，利用枠20%使用/80%残。\n')
print('Integrated RQ1/RQ2 artifact alignment; no new hash execution.')
