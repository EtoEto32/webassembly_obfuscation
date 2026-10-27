from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
FILES=['research/literature-review.md','research/research-gap.md','research/candidates.md','research/threat-model.md','research/algorithm.md','research/novelty-analysis.md','research/experiments.md','paper-draft.md']
ENTRY="\u53ef\u9006\u6df7\u5408\u30ec\u30b3\u30fc\u30c9\u66f4\u65b0\u306e\u8ffd\u88dc\uff082026-10-19\uff09\uff1a[read/write\u5225\u5c40\u6240\u8a08\u753b\u3068\u53cd\u8a3c]({link})\u3092\u8ffd\u52a0\u3057\u305f\u300248\u6761\u4ef632,256\u547c\u51fa\u3057\uff08\u671f\u5f85trap9,216\uff09\u3067\u4e0d\u4e00\u81f40\u3001Binaryen336\u7167\u5408\u3001\u7e2e\u5c0f\u30e2\u30c7\u30eb202,752\u6bd4\u8f03\u3002N=128\u3067\u5168\u56de\u8def/\u5c40\u6240\u8a08\u753b\u306e\u5b9f\u884c\u6bd48.59\u201320.69\u3001\u5c40\u6240\u8a08\u753b/\u672a\u5909\u63db\u6bd41.54\u201311.57\u3002\u305f\u3060\u3057\u516c\u958b\u30d0\u30a4\u30ca\u30ea\u304b\u3089\u4fc2\u6570\u3092\u62bd\u51fa\u3057\u3001\u7b26\u53f7\u531636\u6761\u4ef6\u306e\u5168snapshot\u3092\u56de\u5fa9\u3057\u305f\u3002\u56de\u5fa9\u6210\u529f\u3060\u3051\u3067\u68c4\u5374\u305b\u305a\u3001\u8a08\u753b\u306b\u3088\u308b\u4fdd\u8b77\u4e0a\u306e\u512a\u4f4d\u304c\u672a\u78ba\u8a8d\u3067\u3042\u308b\u3053\u3068\u3068\u3001\u53ef\u9006\u56de\u8def\u66f8\u63db\u3048\u30fbEOC\u30fbWO2023077167A1\u3068\u306e\u5148\u884c\u6027\u3092\u5206\u3051\u3066\u8a18\u9332\u3057\u305f\u3002\u4e3b\u7279\u8a31\u5019\u88dc\u3068\u3057\u3066\u4e0d\u63a1\u7528\u3002\u4e3b\u76ee\u6a19\u306e\u72ec\u7acb\u3057\u305f\u65b0\u898f\u6027\u30fb\u6709\u52b9\u6027\u306f\u672a\u9054\u3067\u3001\u7814\u7a76\u306f\u7d99\u7d9a\u4e2d\u3002"
for name in FILES:
    p=ROOT/name;s=p.read_text(encoding='utf-8')
    link='cone-patch/README.md' if name.startswith('research/') else 'research/cone-patch/paper-note.md'
    if ']('+link+')' in s:raise RuntimeError('already updated '+name)
    head,tail=s.split('\n',1)
    p.write_text(head+'\n\n'+ENTRY.format(link=link)+'\n\n'+tail.lstrip('\n'),encoding='utf-8')
print('Updated',len(FILES),'research ledgers.')

