from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
FILES=['research/literature-review.md','research/research-gap.md','research/candidates.md','research/threat-model.md','research/algorithm.md','research/novelty-analysis.md','research/experiments.md','paper-draft.md','research/patent/README.md']
ENTRY='重複cell表現の追補（実験2026-10-19、記録2026-10-21）：[隣接pairの整合supportによる回復]({link})を実Wasm変換・回復器へ実装した。主・追加120条件、754,992呼出し、別VM1,197照合で不一致0、12負例、180本のbyte再現を保存。全96符号化条件は独立cell表へ回復した。診断処理を除いた最終計測でsingle比は解析本体約2.11–3.05倍、reader込み約1.02–1.40倍、実行約1.16–1.40倍、binary約2.62–2.87倍。費用増加はあるが、偽値・再符号化の追加優位性は未確認。符号化表、無効領域処理、common information分解の先行性を確認し、主特許候補には未採用。独立した新規性・有用な保護効果の主目標は未達。'
for name in FILES:
    f=ROOT/name;s=f.read_text(encoding='utf-8');link='../overlap-cells/README.md' if name=='research/patent/README.md' else ('overlap-cells/README.md' if name.startswith('research/') else 'research/overlap-cells/paper-note.md')
    if ']('+link+')' in s:raise RuntimeError('already updated '+name)
    head,tail=s.split('\n',1);f.write_text(head+'\n\n'+ENTRY.format(link=link)+'\n\n'+tail.lstrip('\n'),encoding='utf-8')
print('Updated',len(FILES),'ledgers')
