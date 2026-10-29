"""Add the new evidence without replacing prior research or tracked README edits."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
note='Relaxed SIMDの追補（2026-10-19）：[仕様上の選択をmaskへ運ぶ限定案](relaxed-carrier/README.md)を実Wasmへ実装。主48本・249,456呼出し、適応的解析等の追加54本・280,638呼出し、WABT計612呼出しで不一致0。主再実行48本byte一致。通常最適化には残るが、方式既知の共通解析ではdynamic maskと近い費用で6組すべてbyte一致の回復先へ戻った。直接maskを返す負の対照で、一般同値変換ではないことも確認。既知Boolean maskingとの技術差と追加の保護優位性が弱く主案には不採用、独創的新候補の数には加えない。新規で有効な主発明・特許性の確立は未達、goalはactive。\n\n'
for relative in ['research/STATUS.md','research/literature-review.md','research/research-gap.md','research/candidates.md','research/threat-model.md','research/algorithm.md','research/novelty-analysis.md','research/experiments.md','research/patent/README.md','paper-draft.md']:
    path=ROOT/relative;text=path.read_text(encoding='utf-8')
    if 'Relaxed SIMDの追補（2026-10-19）' in text:continue
    addition=note
    if relative.startswith('research/patent/'):addition=note.replace('(relaxed-carrier/README.md)','(../relaxed-carrier/README.md)')
    elif relative=='paper-draft.md':addition=note.replace('(relaxed-carrier/README.md)','(research/relaxed-carrier/README.md)')
    head,sep,tail=text.partition('\n');path.write_text(head+'\n\n'+addition+tail if sep else text+'\n\n'+addition,encoding='utf-8')
