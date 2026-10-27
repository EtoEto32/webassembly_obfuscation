# -*- coding: utf-8 -*-
"""Prepend dated progress without replacing prior research or unrelated files."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
tag='零長副作用述語化の追補（2026-10-19）'
note=(tag+'：[追加memoryを使わないbulk述語化](zero-extent/README.md)を実Wasmへ実装。'
      '48主条件＋48回復、239,616呼出し・177,785 trapで値/trap/全memoryの不一致0。'
      'WABT384 writer・7,296 memory probeも一致し、再現で96本のbyte一致を確認。'
      '4つの誤変換を反例で検出。方式既知の解析はlengthから効果条件を露出でき、'
      'O3 mixedのflat比で実行約1.73–8.56倍・解析約1.68–4.90倍。'
      '費用増加を無視しないが、EP1947584B1/MERIT/GCCとの具体差が弱いため主案には不採用。'
      '新規で有効な主発明・特許性の確立は未達、goalはactive。')
paths=['research/STATUS.md','research/literature-review.md','research/research-gap.md',
       'research/candidates.md','research/threat-model.md','research/algorithm.md',
       'research/novelty-analysis.md','research/experiments.md','research/patent/README.md','paper-draft.md']
for rel in paths:
    path=ROOT/rel;text=path.read_text(encoding='utf-8')
    if tag in text:continue
    addition=note
    if rel=='paper-draft.md':addition=note.replace('(zero-extent/','(research/zero-extent/')
    if rel=='research/patent/README.md':addition=note.replace('(zero-extent/','(../zero-extent/')
    head,sep,tail=text.partition('\n');path.write_text(head+'\n\n'+addition+'\n'+sep+tail,encoding='utf-8')
print('Updated research ledgers; pre-existing README/paper sources untouched.')
