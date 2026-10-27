# -*- coding: utf-8 -*-
from pathlib import Path
import prototype as q
marker='並行演算グラフの追補（2026-10-19）'
paragraph='''並行演算グラフの追補（2026-10-19）：[共有memoryとatomicの早期反証](concurrent-frontier/README.md)を実Wasm変換器・実worker・方式既知の回復器へ実装した。主36target＋24回復、101,376呼出し、追加31target・72,912呼出し、WABT240呼出しで不一致0。24/24の主VM条件は依存順の展開で元と同じSSA式へ回復。108 fresh processでatomicの逐次VM比は実行約1.25〜2.07倍、解析約0.94〜1.08倍で、並行化の追加保護効果を未確認。2/4workerに複数担当者の実行を確認したが、全合法順の列挙は解析に不要だった。SCの小モデルと誤変換反例、4非対応拒否、36target＋24回復のbyte再現を保存。host待機、測定wrapper、循環fixtureの実装不備は修正し耐性に数えない。既存thread/Petri-net論文とUS11403372B2に対する独立した新規性も弱く主案に不採用。新しい発明3案には数えず、特許を目指す主目標は未達、goalはactive。'''
files=['research/STATUS.md','research/literature-review.md','research/research-gap.md','research/candidates.md','research/threat-model.md','research/algorithm.md','research/novelty-analysis.md','research/experiments.md','research/patent/README.md','paper-draft.md']
for name in files:
    path=q.ROOT/name;text=path.read_text(encoding='utf-8')
    if marker in text:continue
    p=paragraph
    if name=='research/patent/README.md':p=p.replace('(concurrent-frontier/README.md)','(../concurrent-frontier/README.md)')
    if name=='paper-draft.md':p=p.replace('(concurrent-frontier/README.md)','(research/concurrent-frontier/paper-note.md)')
    first,sep,rest=text.partition('\n');path.write_text(first+'\n\n'+p+'\n'+sep+rest,encoding='utf-8')
print('Updated additive research ledgers; tracked README/paper sources left untouched.')
