# -*- coding: utf-8 -*-
import ast
import hashlib
import json
from pathlib import Path
import re

root=Path(__file__).resolve().parents[1]
title='現memoryを使う共有退避の生成（2026-10-23）'
text='''[共有退避の生成器](side-save/README.md)を実装。同じBを保ち、入口保存次元を4→1、32→4、10→1へ削減した。正37,184呼出し・期待trap19,152で一致し、rotate32の実行中央値は同じBのbasis対照より約13.8%短縮。一方temporaryとcode sizeは増え、既存回復器がbasis/side各12条件を元Wasmへ戻した。coded side-informationとの近さから独立した新難読化・特許性は未確立。総メモリ削減とは主張せず、費用改善の補助部品として保持する。'''
for name,extra in {
    'research/experiments.md':' 小モデル6,048問題と追加1,000問題で最小subspace探索と一致。WABT294呼出し、168trap、54本byte再現、3未対応拒否、27process/189batchを保存した。',
    'research/candidates.md':' 原理の異なる主発明候補の件数には追加しない。既知構成の具体化・費用改善と保護強度を分けて評価する。',
    'research/novelty-analysis.md':' [先行技術との対応](side-save/prior-art.md)を記録し、一般の副情報符号化を新規とは主張しない。',
    'research/novelty-status-20261023.md':' 直近の週枠は28%使用・72%残。主発明の研究は継続中。',
}.items():
    f=root/name;old=f.read_text(encoding='utf-8')
    if title in old:raise RuntimeError('already integrated')
    f.write_text(old.rstrip()+'\n\n## '+title+'\n\n'+text+extra+'\n',encoding='utf-8')
for name,note in {
    'research/research-gap.md':'[今回の交換論証](side-save/algorithm.md)は、現memoryが単調に情報を失うcopy列で、任意の選択済み表現Bを維持した線形退避を最小化する。退避減量と全体のtemporary/code size、難読化の解除費用が別の目的関数であることを実測した。保存情報を減らすだけでは解析耐性増を導けない。',
    'research/threat-model.md':'[共有退避版](side-save/algorithm.md)にも以前の公開binary解析器を変更せず適用した。source・seed・B metadataなしにdigestから表現を抽出し全trap区分を検査して回復した。12/12成功を記録する一方、全例が回復したことだけを理由に保存処理の費用改善まで否定しない。保護と性能を別に評価する。',
    'research/literature-review.md':'[coded side-informationの追補](side-save/prior-art.md)。Lee/Dimakis/Heathの2014 preprintの問題定義とTheorem 1、Byrne/Calderiniの2017誌面Abstractを確認。共有送信と各受信者の線形副情報という既知条件が今回の共有退避へ対応する。nestedなWasm copy列への具体化との境界を記録した。',
    'research/algorithm.md':'[現memoryを副情報とする共有退避](side-save/algorithm.md)を補助生成器として追加。D_j=R_j[P_j;V]を検査して全正常/trap出口の補正を生成し、nestedなrow(P_j)に対する後方greedyの限定最小性を論証した。選定済み主方式の新規性が確立したという変更ではない。',
    'paper-draft.md':text.replace('(side-save/','(research/side-save/')+' 全例回復できたという事実と、保存処理の費用改善が成立したという事実を両方記載する。'
}.items():
    f=root/name;old=f.read_text(encoding='utf-8');f.write_text(old.rstrip()+'\n\n## '+title+'\n\n'+note+'\n',encoding='utf-8')
f=root/'README.md';old=f.read_text(encoding='utf-8');entry='2026-10-23追補：'+text.replace('(side-save/','(research/side-save/')+' [実測](results/invention-20261023/side-save-report-v1/report.md)。'
f.write_text(old.replace('\n\n','\n\n'+entry+'\n\n',1),encoding='utf-8')
f=root/'research/novelty-status-20261023.md';old=f.read_text(encoding='utf-8');f.write_text(old.replace('25%使用（約75%残）','28%使用（約72%残）'),encoding='utf-8')
folders=['residue-wrap-v2','residue-wrap-model-v1','residue-wrap-runtime-v1','residue-wrap-audit-v1','residue-wrap-report-v2',
         'side-save-main-v1','side-save-model-v1','side-save-holdout-v1','side-save-runtime-v1','side-save-audit-v1','side-save-report-v1']
count=0
for name in folders:
    folder=root/'results/invention-20261023'/name
    for entry in json.loads((folder/'provenance.json').read_text(encoding='utf-8')):
        if hashlib.sha256((folder/entry['file']).read_bytes()).hexdigest()!=entry['sha256']:raise AssertionError('hash mismatch')
        count+=1
syntax=[];links=0
for folder in ('residue-wrap','side-save'):
    for file in (root/'research'/folder).glob('*.py'):
        ast.parse(file.read_text(encoding='utf-8'));syntax.append(str(file.relative_to(root)))
    for file in (root/'research'/folder).glob('*.md'):
        for target in re.findall(r'\]\(([^)]+)\)',file.read_text(encoding='utf-8')):
            if target.startswith(('https://','http://','#')):continue
            if not (file.parent/target).exists():raise AssertionError('missing link '+target)
            links+=1
result=dict(verified_hashes=count,mismatch=0,python_syntax=syntax,local_links_checked=links,weekly_used_percent=28,weekly_remaining_percent=72,
            unmodified_by_this_work=['paper/main.tex','paper/README.md'],goal_completed=False)
(root/'results/invention-20261023/side-save-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
