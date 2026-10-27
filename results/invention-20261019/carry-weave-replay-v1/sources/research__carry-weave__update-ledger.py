from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
FILES=['research/literature-review.md','research/research-gap.md','research/candidates.md','research/threat-model.md','research/algorithm.md','research/novelty-analysis.md','research/experiments.md','paper-draft.md','research/patent/README.md']
ENTRY='分割carry-saveの追補（2026-10-19）：[マスク分割片のSIMD混載と総和の回復]({link})を実装した。主90条件・574,830呼出し、追加40条件・255,480呼出しで不一致0。Binaryen1,260照合、縮小モデル124,828比較、誤carry9反例、180本の主byte再現を保存。全130条件から元項を回復。分割なしCSA比で解析本体約1.76–2.06、実行約1.35–1.59の費用増加はあるが、総和の保存則を逆に辿れば探索せず戻せる。CSA・MBA・既存圧縮木研究との独立した差が弱く、主特許候補には不採用。zero-paddingの4件は回復器の不足として修正し、耐性に数えない。主目標の新規性・有効性の確立は未達で、研究を継続中。'
for name in FILES:
    p=ROOT/name;s=p.read_text(encoding='utf-8')
    link='../carry-weave/README.md' if name=='research/patent/README.md' else ('carry-weave/README.md' if name.startswith('research/') else 'research/carry-weave/paper-note.md')
    if ']('+link+')' in s:raise RuntimeError('already updated '+name)
    head,tail=s.split('\n',1);p.write_text(head+'\n\n'+ENTRY.format(link=link)+'\n\n'+tail.lstrip('\n'),encoding='utf-8')
print('Updated',len(FILES),'research ledgers.')
