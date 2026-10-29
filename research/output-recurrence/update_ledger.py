# -*- coding: utf-8 -*-
"""Prepend this gate's evidence, preserving historical notes and tracked files."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
marker = '出力履歴による状態消去の追補（2026-10-19）'
note = marker + '：[内部状態yを消す限定Wasm変換](output-recurrence/README.md)を実装。主32本・66,080呼出し、追加9本・18,585呼出し、WABT224呼出しで不一致0、主再実行32本byte一致。異なる元状態から同じ変換binaryになる3組を生成したが、8/8条件でw=b*yを持つ短い等価実装を回復し、共通検査器の24条件も同じcanonical binaryへ戻った。高次多項式への拡張でも商状態は閉じることを導出・97,380組で検査し、rotateは31条件でその閉性を壊す反例を保存。状態実現の既知原理との差と追加保護効果が弱く主案には不採用。独創的な新候補の数には加えない。新規で有効な主発明・特許性の確立は未達、goalはactive。\n\n'
for relative in ['research/STATUS.md', 'research/literature-review.md', 'research/research-gap.md', 'research/candidates.md', 'research/threat-model.md', 'research/algorithm.md', 'research/novelty-analysis.md', 'research/experiments.md', 'research/patent/README.md', 'paper-draft.md']:
    path = ROOT / relative
    text = path.read_text(encoding='utf-8')
    if marker in text:
        continue
    addition = note
    if relative.startswith('research/patent/'):
        addition = note.replace('(output-recurrence/README.md)', '(../output-recurrence/README.md)')
    elif relative == 'paper-draft.md':
        addition = note.replace('(output-recurrence/README.md)', '(research/output-recurrence/README.md)')
    head, sep, tail = text.partition('\n')
    path.write_text(head + '\n\n' + addition + tail if sep else text + '\n\n' + addition, encoding='utf-8')
