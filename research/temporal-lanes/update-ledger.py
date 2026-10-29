from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
FILES=['research/literature-review.md','research/research-gap.md','research/candidates.md','research/threat-model.md','research/algorithm.md','research/novelty-analysis.md','research/experiments.md','paper-draft.md','research/patent/README.md']
ENTRY='時間差SIMDの追補（2026-10-19）：[異なる論理時刻のlane混載と反証]({link})を追加した。主72条件、34,560呼出し（期待trap2,160）で不一致0。Binaryen756照合、縮小モデル263,376比較、誤mask9反例、216本のbyte再現を保存。mixed/未変換の実行比1.228–3.732、mixed/自然配置の回復本体比0.894–1.089。主回復36/36に加え、phase値を使わず依存鎖からも36/36を元binaryへ回復した。時間変更・SLPの先行性と、追加保護効果が未確認であることを分けて記録し、主特許候補には不採用。readerのstack処理・shuffle重複処理による中断は耐性に数えない。主目標の独立した新規性・有効性は未達で、研究は継続中。'
for name in FILES:
    p=ROOT/name;s=p.read_text(encoding='utf-8')
    link='../temporal-lanes/README.md' if name=='research/patent/README.md' else ('temporal-lanes/README.md' if name.startswith('research/') else 'research/temporal-lanes/paper-note.md')
    if ']('+link+')' in s:raise RuntimeError('already updated '+name)
    head,tail=s.split('\n',1)
    p.write_text(head+'\n\n'+ENTRY.format(link=link)+'\n\n'+tail.lstrip('\n'),encoding='utf-8')
print('Updated',len(FILES),'research ledgers.')
