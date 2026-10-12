"""Reuse saved instruction evidence as controls for the refreshed RQ1."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/'results/rq-validation'
ledger_path=DIR/'review-ledger.json'
ledger=json.loads(ledger_path.read_text())
by_id={r['finding_id']:r for r in ledger}
removed=json.loads((DIR/'instrumentation-removal-check.json').read_text())
assert len(removed)==2
assert all(r['matched_after_removing_increments']==r['origin_functions'] and not r['unmatched'] for r in removed)
normal=by_id['V03']['evidence']['ops']
assert any(r['op']=='br_table' for r in normal)
assert not any(r['op']=='loop' or '.store' in r['op'] for r in normal)
flat=by_id['V04']['evidence']
def ops(rows):return [(r['op'],r['args']) for r in rows if r['op']!='local']
payload=ops(flat['origin']['ops'])[:-1]
transformed=ops(flat['variant']['ops'])
assert any(transformed[i:i+len(payload)]==payload for i in range(len(transformed)))
assert any(transformed[i:i+2]==[('i32.const','0'),('local.set','3')] for i in range(len(transformed)-1))
assert any(transformed[i:i+3]==[('i32.const','1'),('local.set','3'),('br','1')] for i in range(len(transformed)-2))
seq=by_id['V12']
assert seq['original_function_candidates']==[11,45]
assert any(r['op']=='i32.store' and r['args']=='2 8' for r in seq['evidence']['variant']['ops'])
report=dict(source_ledger_sha256=hashlib.sha256(ledger_path.read_bytes()).hexdigest(),
            reused_findings=[{k:r[k] for k in ('finding_id','program','mechanism','reasoning')}
                             for r in [by_id[i] for i in ['V01','V02','V03','V04','V12']]],
            saved_instruction_checks=dict(instrumentation_restored_functions=[r['origin_functions'] for r in removed],
                ordinary_branch_table_without_loop_or_store=True,base64_original_payload_contiguous=True,
                base64_state_zero_then_one_and_back_branch=True,seqtk_counterpart_ambiguity_preserved=True),
            scope='Existing saved instruction records only; no new hash/miner execution, no independently labeled full-corpus classification accuracy.')
(DIR/'refreshed-rq1-controls-audit.json').write_text(json.dumps(report,indent=2)+'\n')
p=ROOT/'paper/main.tex';s=p.read_text(encoding='utf-8')
old='以前の予備解析も，分析方法が妥当かを確かめるために利用した．WasmMalでは，malwareに分類された121件，benignに分類された3件に，SEISMICの計測用関数と一致する関数があった．また，一般用途のA-StarとCreaturePackでは，カウンタを更新する命令列を取り除くと，通常版の全147関数，全756関数と命令列が一致した．これらは，計測用に追加された命令を難読化による変化と取り違えないための補助的な根拠であり，独立した研究課題とはしない．'
replacement='通常処理と計測コードの対照には，旧予備解析の命令位置と変換前後の対応が残る例を再利用する．その結果と採掘標本への適用範囲は第\\ref{sec:rq1-controls}節に示す．'
assert old in s
s=s.replace(old,replacement,1)
section='''\\subsection{通常処理と研究用計測による対照}
\\label{sec:rq1-controls}
WasmMalでは，malwareに分類された121件，benignに分類された3件に，SEISMICの計測用関数と一致する関数があった．一般用途のA-StarとCreaturePackでは，カウンタ更新の命令列を取り除くと，元の全147関数，全756関数と命令列が一致した．命令数の増加だけでは難読化と計測を区別できない具体例であり，RQ2ではWasabiのhookを持つ標本を混ぜずに測定する根拠になる．ただしWasabiとSEISMICが同じ計測機構であるとは扱わない．

CreaturePackの関数400では，引数が指す位置から読んだ値と74のANDを分岐表の選択値に用い，各分岐は8，16，0，10を返す．関数には状態を書き換えるストアもループもなく，シンボル名も数値の基数選択を支持する．これに対してWASMixerのbase64-cliの関数515では，元の3ストアを含む命令列を保持しながら，状態0でその処理へ分岐し，状態1へ更新してループへ戻り，次の選択で終了する．この対照は分岐表の存在より状態の生成・更新・戻り先を確認する必要を示す．

別のseqtk対照でも，状態0からcalloc(1,28)を呼び，結果を保存して状態1へ更新し，選択処理へ戻ってから結果を返す経路を確認した．元の関数11と45が同じ処理を持つため，唯一の対応関数は確定しない．これらは一般用途の選択例による局所的な対照であり，採掘標本の確認件数や，全件分類の精度を表さない．

'''
needle='\\subsection{状態変数を用いる制御フロー平坦化}'
assert needle in s
s=s.replace(needle,section+needle,1)
p.write_text(s,encoding='utf-8')
resume=ROOT/'results/runtime-mining/cross-dataset/proof-of-theft/resume-state.txt'
with resume.open('a',encoding='utf-8') as f:
 f.write('\nRQ1旧対照の統合：review-ledgerのV01/02/03/04/12とinstrumentation-removal-checkを再照合。A-Star147/CreaturePack756全復元，CreaturePack400のbr_tableにloop/storeなし，base64-cli515の元payload連続保持とstate0→1→backbranch，seqtk11/45対応曖昧性を保存。refreshed-rq1-controls-audit.jsonとintegrate_reviewed_rq1_controls.py。paper/main.texへ通常処理/計測の対照節を追加し方法の旧説明を参照に置換。採掘標本の機構確認件数/精度には数えない。新規ハッシュ実行なし。\n')
print('Reviewed saved control evidence and integrated it into RQ1 with explicit scope.')
