"""Add the verified primary MinerRay citation and distinguish detector timing."""
import json
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'paper/references.bib';s=p.read_text(encoding='utf-8')
entry=r'''
@inproceedings{romano2020minerray,
  author = {Romano, Alan and Zheng, Yunhui and Wang, Weihang},
  title = {{MinerRay}: Semantics-Aware Analysis for Ever-Evolving Cryptojacking Detection},
  booktitle = {Proceedings of the 35th IEEE/ACM International Conference on Automated Software Engineering},
  publisher = {ACM},
  year = {2020},
  doi = {10.1145/3324884.3416580},
  note = {\url{https://weihang-wang.github.io/papers/ASE2020-MinerRay.pdf}}
}
'''
if '@inproceedings{romano2020minerray,' not in s:s+='\n'+entry
p.write_text(s,encoding='utf-8')
p=ROOT/'paper/main.tex';s=p.read_text(encoding='utf-8')
s=s.replace('MinerRay & 第6.4節の検出用グラフ構築・走査の時間とメモリ評価', 'MinerRay\\cite{romano2020minerray} & 第6.4節の検出用グラフ構築・走査の時間とメモリ評価',1)
needle='本研究では，これらの公開標本の出力検証と実測を静的構造変化と結び付ける．'
addition='MinerRayの第6.4節と表5の時間は検出用グラフの構築と走査に要する時間であり，採掘関数のhashes/sとは比較できない\\cite{romano2020minerray}．'
assert needle in s
if addition not in s:s=s.replace(needle,addition+needle,1)
p.write_text(s,encoding='utf-8')
keys=set(re.findall(r'@\w+\s*\{\s*([^,]+)',(ROOT/'paper/references.bib').read_text(encoding='utf-8')))
used={k.strip() for group in re.findall(r'\\cite\{([^}]+)\}',s) for k in group.split(',')}
assert not used-keys,used-keys
evidence=dict(study='MinerRay',reviewed_date_jst='2026-10-08',
  primary_source='https://weihang-wang.github.io/papers/ASE2020-MinerRay.pdf',
  doi='10.1145/3324884.3416580',authors=['Alan Romano','Yunhui Zheng','Weihang Wang'],
  sections_reviewed=['Front-page bibliographic reference','6.4 Performance and Memory Overhead','Table 5'],
  reported_measurement=dict(kind='Detector control-flow graph construction and scan',graph_construction_ms=427.78,scanning_ms=1398.60,memory_mb=37.23),
  interpretation='This timing is not mining hash throughput. Absence of a paired hashing result in this reviewed section does not establish worldwide non-evaluation.',
  all_current_citation_keys_resolve=True)
(ROOT/'results/runtime-mining/cross-dataset/prior-work/minerray-primary-review.json').write_text(json.dumps(evidence,indent=2)+'\n')
with (ROOT/'results/runtime-mining/cross-dataset/proof-of-theft/resume-state.txt').open('a',encoding='utf-8') as f:
 f.write('\n先行研究点検：MinerRay著者版PDF冒頭の書誌・第6.4節・表5を再確認。Romano/Zheng/Wang2020 DOI10.1145/3324884.3416580をreferences.bibへ追加，比較表と本文に引用。427.78ms graph/1398.60ms scanは検出器の時間でhashes/sと直接比較不可。minerray-primary-review.json保存，全cite keyソース上解決確認。新規採掘なし。\n')
print('Verified primary reference integrated; all citation keys resolve.')
