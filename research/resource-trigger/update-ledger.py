from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
FILES=['research/literature-review.md','research/research-gap.md','research/candidates.md','research/threat-model.md','research/algorithm.md','research/novelty-analysis.md','research/experiments.md','paper-draft.md','research/patent/README.md']
ENTRY='resource破棄の追補（2026-10-19）：[Component Modelの所有handleによる計算移動]({link})を実coreからcomponentへ変換する形で実装した。主72条件・318,240呼出し、追加32条件・141,440呼出しで不一致0。主元/回復coreのBinaryen567照合、誤破棄順9反例、非対応5拒否、主144本のbyte再現を保存。104条件を公開canon結線・handle・内部slotの記号追跡で回復した。deferred/directは解析本体約1.10–1.29倍、実行約0.99–1.41倍だが、deferred/immediateは解析約0.95–1.09、実行約0.95–1.05で、生成順変更の追加効果は未確認。Jcoのrep bit30の不一致はslot番号を渡す設計へ修正し、失敗ログも保持した。実行形式の境界移動・標準destructorとの独立した差が弱く、主特許候補には不採用。新規で有効な主発明の確立は未達、研究を継続中。'
for name in FILES:
    p=ROOT/name;s=p.read_text(encoding='utf-8');link='../resource-trigger/README.md' if name=='research/patent/README.md' else ('resource-trigger/README.md' if name.startswith('research/') else 'research/resource-trigger/paper-note.md')
    if ']('+link+')' in s:raise RuntimeError('already updated '+name)
    head,tail=s.split('\n',1);p.write_text(head+'\n\n'+ENTRY.format(link=link)+'\n\n'+tail.lstrip('\n'),encoding='utf-8')
print('Updated',len(FILES),'research ledgers.')
