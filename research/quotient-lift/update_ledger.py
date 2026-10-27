"""Prepend a dated evidence note; never replace the research history."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
note='状態被覆の追補（2026-10-19）：[状態複製と商の回復費用](quotient-lift/README.md)を実Wasmへ実装。40主条件＋静的32/公開学習40 clone、112本・231,280呼出し・30,688 trapで不一致0。WABT672呼出し・2,688 memory probeも一致、再現112本byte一致。全状態解析費用は増えたが、95継続語の代表解析では最大33物理状態で全32条件を回復し、公開I/O学習のquery transcriptは複製数を変えても同一だった。長い例外語を見逃す負の対照も保存。既知の状態分割との技術差が弱く主案には不採用。新規で有効な主発明・特許性の確立は未達、goalはactive。\n\n'
for relative in ['research/STATUS.md','research/literature-review.md','research/research-gap.md','research/candidates.md','research/threat-model.md','research/algorithm.md','research/novelty-analysis.md','research/experiments.md','research/patent/README.md','paper-draft.md']:
    path=ROOT/relative;text=path.read_text(encoding='utf-8')
    if '状態被覆の追補（2026-10-19）' in text:continue
    addition=note
    if relative.startswith('research/patent/'):addition=note.replace('(quotient-lift/README.md)','(../quotient-lift/README.md)')
    elif relative=='paper-draft.md':addition=note.replace('(quotient-lift/README.md)','(research/quotient-lift/README.md)')
    head,sep,tail=text.partition('\n');path.write_text(head+'\n\n'+addition+tail if sep else text+'\n\n'+addition,encoding='utf-8')
