import argparse,csv,json,statistics
from pathlib import Path
import prototype as p
def main(data,perf,out):
    data,perf,out=map(Path,(data,perf,out));out.mkdir(parents=True,exist_ok=False);rows=json.loads((perf/'summary.json').read_text());pairs=[]
    for r in rows:
        if r['mode']!='mixed':continue
        pick=lambda mode:next(x for x in rows if x['mode']==mode and all(x[k]==r[k] for k in ('n','kind','rounds')))
        v=pick('vector');s=pick('scalar');plain=pick('plain')
        pairs.append(dict(n=r['n'],kind=r['kind'],rounds=r['rounds'],mixed_ns=r['ns'],vector_ns=v['ns'],scalar_ns=s['ns'],plain_ns=plain['ns'],mixed_over_plain=r['ns']/plain['ns'],mixed_over_vector=r['ns']/v['ns'],scalar_over_mixed=s['ns']/r['ns'],mixed_bytes=r['bytes'],vector_bytes=v['bytes'],plain_bytes=plain['bytes']))
    p.save(out/'pairs.json',pairs)
    with (out/'pairs.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(pairs[0]));w.writeheader();w.writerows(pairs)
    attacks=[]
    for r in json.loads((perf/'analysis.json').read_text()):attacks.append({k:r[k] for k in ('file','n','kind','mode','opt')}|dict(read_ms=statistics.median(x['read_ms'] for x in r['runs']),extract_ms=statistics.median(x['extract_ms'] for x in r['runs'])))
    ratios=[]
    for r in attacks:
        if r['mode']!='mixed':continue
        v=next(x for x in attacks if x['mode']=='vector' and all(x[k]==r[k] for k in ('n','kind','opt')))
        ratios.append(dict(n=r['n'],kind=r['kind'],opt=r['opt'],extraction_ratio=r['extract_ms']/v['extract_ms'],total_ratio=(r['read_ms']+r['extract_ms'])/(v['read_ms']+v['extract_ms'])))
    p.save(out/'attacks.json',attacks);p.save(out/'attack-ratios.json',ratios)
    span=lambda vs:[min(vs),max(vs)]
    manifest=json.loads((data/'manifest.json').read_text());census=[]
    for r in manifest:
        if r['mode'] not in ('vector','mixed'):continue
        census.append(dict(file=r['file'],bitselects=sum(e[0]=='v128.bitselect' for e in p.walk(p.read(data/r['file']))),expected=r['n']//4))
    assert all(r['bitselects']==r['expected'] for r in census);p.save(out/'census.json',census)
    summary=dict(mixed_over_plain=span([r['mixed_over_plain'] for r in pairs]),mixed_over_vector=span([r['mixed_over_vector'] for r in pairs]),scalar_over_mixed=span([r['scalar_over_mixed'] for r in pairs]),steady=[r for r in pairs if r['rounds']==256],attack_extract_ms=span([r['extract_ms'] for r in attacks]),attack_reader_ms=span([r['read_ms'] for r in attacks]),attack_mixed_over_vector=span([r['extraction_ratio'] for r in ratios]),attack_total_ratio=span([r['total_ratio'] for r in ratios]),transform_ms=span([r['transform_ms'] for r in manifest if r['mode']=='mixed']),rss_kib=span([r['peak_rss_kib'] for r in rows]),process_max_over_min=span([max(r['process_medians_ns'])/min(r['process_medians_ns']) for r in rows]))
    p.save(out/'summary.json',summary);print(json.dumps(summary))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('data');a.add_argument('performance');a.add_argument('output');v=a.parse_args();main(v.data,v.performance,v.output)
