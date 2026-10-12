"""Check references in authored review decisions and render per-case notes.

Reference existence is not scientific validation of a verdict or independent
human review. Decisions are authored after inspecting code, never inferred here.
"""
import csv
import json
import re
from acquire import ROOT


def audit_ledger(ledger_file):
    base=ROOT/'results/cases'
    ledger=json.loads(ledger_file.read_text(encoding='utf-8'))
    stage=ledger_file.stem.removeprefix('review-decisions-')
    plan=json.loads((ROOT/ledger['selection_file']).read_text(encoding='utf-8'))
    selected={r['sha256']:r for r in plan['selected']}
    index=[]; seen=set()
    for review in ledger['reviews']:
        sha=review['sha256']
        if sha in seen: raise ValueError('Duplicate reviewed SHA')
        seen.add(sha)
        selection=selected[sha]
        folder=base/sha
        packet=json.loads((folder/'packet.json').read_text(encoding='utf-8'))
        dis=(folder/'disassembly.txt').read_text(encoding='utf-8')
        offsets={int(s,16) for s in re.findall(r'^\s*([0-9a-f]+)(?::|\s+func\[)',dis,re.M)}
        funcs={int(s) for s in re.findall(r'func\[(\d+)\]',dis)}
        for o in review['offsets']:
            if int(o,16) not in offsets: raise ValueError('Missing offset '+sha+' '+o)
        if not set(review['functions'])<=funcs: raise ValueError('Missing reviewed function')
        text=['# 個別静的解析 '+sha[:12], '',
              'レビュー日: '+ledger['review_date_jst'], '',
              'レビュー担当: '+ledger['reviewer'], '',
              '判定: '+review['verdict'], '',
              '抽出層: '+selection['stratum']+f"（抽出枠 {selection['frame_size']} 件、選定 {selection['selected_in_stratum']} 件）", '',
              '確認関数: '+', '.join(map(str,review['functions'])), '',
              '確認オフセット: '+', '.join(review['offsets']), '',
              'オフセットの対象: '+packet.get('offset_scope','original binary'), '',
              '## 観測と解釈', '']
        text += ['- '+finding for finding in review['findings']]
        text += ['', '## 別の説明・限界', '', review['alternative_explanations'], '', ledger['scope'], '']
        if review.get('source_evidence'): text += ['一次資料: '+review['source_evidence'], '']
        (folder/('review-'+stage+'.md')).write_text('\n'.join(text),encoding='utf-8')
        index.append({'sha256':sha,'stratum':selection['stratum'],'verdict':review['verdict'],
                      'reviewer':ledger['reviewer'],'stage':stage,'review_path':f'results/cases/{sha}/review-{stage}.md',
                      'reference_checks':'offsets_and_function_indices_exist; verdict_not_automatically_validated'})
    return index,{'stage':stage,'selected':len(selected),'reviewed':len(index),'pending':len(selected)-len(index)}


def main():
    base=ROOT/'results/cases'; index=[];stages=[]
    for ledger in sorted(base.glob('review-decisions-stage*.json')):
        entries,status=audit_ledger(ledger);index.extend(entries);stages.append(status)
    with (base/'review-index.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(index[0])); writer.writeheader();writer.writerows(index)
    summary={'stages':stages,'individually_reviewed_unique':len({r['sha256'] for r in index}),
             'review_records':len(index),'independent_human_review':False}
    (base/'review-status.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary))


if __name__=='__main__': main()
