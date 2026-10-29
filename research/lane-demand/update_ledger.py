# -*- coding: utf-8 -*-
"""Add evidence to research ledgers, retaining existing historical content."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
marker = '入力依存SIMDレーン移送の追補（2026-10-19）'
note = marker + '：[4つの仮入力と動的レーン移送](lane-demand/README.md)を実Wasmへ実装。主56本・240,128呼出し、追加60本・257,280呼出し、WABT336呼出しで不一致0。回復24式のscalarモデルはSMTで元式と同値、主v2/v3の56本はbyte一致。通常O3後も移送は残るが、方式既知の解析では親子frameの差が相殺され、24/24条件を1レーン需要からscalarへ回復できた。動的版の有限な解析費用増は測定したものの、独立した新規性と十分な追加保護効果は未確立で主案に不採用。既存のSIMD VM・vector化・demanded-elements解析を近い先行技術として記録。独創的な新候補の数には加えない。位置を動かすだけでなく、必要な値を安く分離できない機構が次の検証課題。新規で有効な主発明・特許性の確立は未達、goalはactive。\n\n'
for relative in ['research/STATUS.md', 'research/literature-review.md',
                 'research/research-gap.md', 'research/candidates.md',
                 'research/threat-model.md', 'research/algorithm.md',
                 'research/novelty-analysis.md', 'research/experiments.md',
                 'research/patent/README.md', 'paper-draft.md']:
    path = ROOT / relative
    text = path.read_text(encoding='utf-8')
    if marker in text:
        continue
    addition = note
    if relative.startswith('research/patent/'):
        addition = note.replace('(lane-demand/README.md)', '(../lane-demand/README.md)')
    elif relative == 'paper-draft.md':
        addition = note.replace('(lane-demand/README.md)', '(research/lane-demand/README.md)')
    head, sep, tail = text.partition('\n')
    path.write_text(head + '\n\n' + addition + tail if sep else text + '\n\n' + addition,
                    encoding='utf-8')
