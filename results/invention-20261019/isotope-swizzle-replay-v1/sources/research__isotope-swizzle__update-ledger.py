from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
files=['research/literature-review.md','research/research-gap.md','research/candidates.md','research/threat-model.md','research/algorithm.md','research/novelty-analysis.md','research/experiments.md','paper-draft.md']
for name in files:
    p=ROOT/name;s=p.read_text(encoding='utf-8');link='isotope-swizzle/README.md' if name.startswith('research/') else 'research/isotope-swizzle/paper-note.md'
    entry=f'SIMD符号化表の追補（2026-10-19）：[全単射を合成した表と群の回復]({link})を実装・反証した。主30条件、708,480呼出しで不一致0、Binaryen480照合も一致。表12条件の全24表を元seedなしで回復。O3 table/decode実行比2.47–4.71、サイズ比3.72–5.72、回復本体0.79–3.39ms。解析費用の増加はあるが、局所的な群正規化で分割でき、Chowらの符号化表とSIMD表参照への直接の先行性も強い。主特許候補として不採用。実装不備・非対応を耐性に数えず、独立した新規性と有効性を備える主目標は未達、goalはactive。\n\n'
    if 'SIMD符号化表の追補（2026-10-19）' in s:raise RuntimeError('already updated '+name)
    head,tail=s.split('\n',1);p.write_text(head+'\n\n'+entry+tail.lstrip('\n'),encoding='utf-8')
print('Updated',len(files),'research ledgers; tracked README and paper sources unchanged.')
