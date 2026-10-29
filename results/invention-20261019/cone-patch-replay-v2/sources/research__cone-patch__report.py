import argparse,csv,json,statistics
from pathlib import Path
import prototype as p
def main(data,perf,exposure,out):
    data,perf,exposure,out=map(Path,(data,perf,exposure,out));out.mkdir(parents=True,exist_ok=False);rows=json.loads((perf/'summary.json').read_text());pairs=[]
    for r in rows:
        if r['mode']!='patch':continue
        same=lambda x:x['n']==r['n'] and x['depth']==r['depth'] and x['kernel']==r['kernel']
        f=next(x for x in rows if same(x) and x['mode']=='full');na=next(x for x in rows if same(x) and x['mode']=='footprint');pl=next(x for x in rows if same(x) and x['mode']=='plain')
        pairs.append(dict(n=r['n'],depth=r['depth'],kernel=r['kernel'],patch_ns=r['ns'],full_ns=f['ns'],plain_ns=pl['ns'],full_over_patch=f['ns']/r['ns'],footprint_over_patch=na['ns']/r['ns'],patch_over_plain=r['ns']/pl['ns'],patch_bytes=r['bytes'],full_bytes=f['bytes'],bytes_patch_over_full=r['bytes']/f['bytes']))
    p.save(out/'pairs.json',pairs)
    with (out/'pairs.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(pairs[0]));w.writeheader();w.writerows(pairs)
    analysis=json.loads((perf/'analysis.json').read_text());attacks=[]
    for r in analysis:attacks.append(dict(file=r['file'],read_ms=statistics.median(x['read_ms'] for x in r['runs']),extract_ms=statistics.median(x['extract_ms'] for x in r['runs']),decode_ms=statistics.median(x['decode_ms'] for x in r['runs'])))
    p.save(out/'attack.json',attacks);manifest=json.loads((data/'manifest.json').read_text());census=[]
    for r in manifest:census.append(dict(file=r['file'],vector_multiplies=sum(e[0]=='i32x4.mul' for e in p.walk(p.read(data/r['file']))),expected=2*sum(x['selected'] for x in r['plans'])))
    assert all(r['vector_multiplies']==r['expected'] for r in census);p.save(out/'census.json',census)
    span=lambda xs:[min(xs),max(xs)]
    summary=dict(full_over_patch=span([r['full_over_patch'] for r in pairs]),footprint_over_patch=span([r['footprint_over_patch'] for r in pairs]),patch_over_plain=span([r['patch_over_plain'] for r in pairs]),large=[r for r in pairs if r['n']==128],attack_extract_ms=span([r['extract_ms'] for r in attacks]),attack_decode_ms=span([r['decode_ms'] for r in attacks]),transform_ms=span([r['transform_ms'] for r in manifest if r['mode']=='patch']),rss_kib=span([r['peak_rss_kib'] for r in rows]),exposure=[r for r in json.loads((exposure/'exposure.json').read_text()) if r['n']==128 and r['mode']=='patch'])
    p.save(out/'summary.json',summary);print(json.dumps(summary))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('data');a.add_argument('performance');a.add_argument('exposure');a.add_argument('output');v=a.parse_args();main(v.data,v.performance,v.exposure,v.output)
