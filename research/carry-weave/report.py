import argparse,csv,json,statistics
from pathlib import Path
import prototype as p
def main(data,perf,out):
    data,perf,out=map(Path,(data,perf,out));out.mkdir(parents=True,exist_ok=False);native=json.loads((perf/'summary.json').read_text());a=json.loads((perf/'analysis.json').read_text());rows=[]
    for r in native:
        if r['mode']!='splitcsa':continue
        pick=lambda mode:next(x for x in native if x['mode']==mode and (x['n'],x['kind'])==(r['n'],r['kind']))
        plain,packed,csa,splitadd=map(pick,('plain','packed','csa','splitadd'))
        rows.append(dict(n=r['n'],kind=r['kind'],plain_ns=plain['ns'],packed_ns=packed['ns'],csa_ns=csa['ns'],splitadd_ns=splitadd['ns'],splitcsa_ns=r['ns'],over_plain=r['ns']/plain['ns'],over_csa=r['ns']/csa['ns'],over_splitadd=r['ns']/splitadd['ns'],plain_bytes=plain['bytes'],splitcsa_bytes=r['bytes']))
    p.save(out/'pairs.json',rows)
    with (out/'pairs.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    attacks=[]
    for r in a:attacks.append({k:r[k] for k in ('file','n','kind','mode','opt')}|dict(read_ms=statistics.median(x['read_ms'] for x in r['runs']),recover_ms=statistics.median(x['recover_ms'] for x in r['runs']),nodes=r['runs'][0]['nodes']))
    ratios=[]
    for r in attacks:
        if r['mode']!='splitcsa':continue
        pick=lambda mode:next(x for x in attacks if x['mode']==mode and (x['n'],x['kind'],x['opt'])==(r['n'],r['kind'],r['opt']))
        plain,csa,splitadd=map(pick,('plain','csa','splitadd'))
        ratios.append(dict(n=r['n'],kind=r['kind'],opt=r['opt'],over_plain=r['recover_ms']/plain['recover_ms'],over_csa=r['recover_ms']/csa['recover_ms'],over_splitadd=r['recover_ms']/splitadd['recover_ms'],total_over_csa=(r['read_ms']+r['recover_ms'])/(csa['read_ms']+csa['recover_ms'])))
    p.save(out/'attacks.json',attacks);p.save(out/'attack-ratios.json',ratios)
    span=lambda a:[min(a),max(a)];manifest=json.loads((data/'manifest.json').read_text());mixed=[r for r in attacks if r['mode']=='splitcsa']
    summary=dict(runtime_over_plain=span([r['over_plain'] for r in rows]),runtime_over_csa=span([r['over_csa'] for r in rows]),runtime_over_splitadd=span([r['over_splitadd'] for r in rows]),recovery_over_plain=span([r['over_plain'] for r in ratios]),recovery_over_csa=span([r['over_csa'] for r in ratios]),recovery_over_splitadd=span([r['over_splitadd'] for r in ratios]),total_recovery_over_csa=span([r['total_over_csa'] for r in ratios]),recovery_ms=span([r['recover_ms'] for r in mixed]),reader_ms=span([r['read_ms'] for r in mixed]),transform_ms=span([r['transform_ms'] for r in manifest if r['mode']=='splitcsa']),rss_kib=span([r['rss_kib'] for r in native]),process_max_over_min=span([max(r['process_medians_ns'])/min(r['process_medians_ns']) for r in native]))
    p.save(out/'summary.json',summary);print(json.dumps(summary))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('data');a.add_argument('performance');a.add_argument('output');v=a.parse_args();main(v.data,v.performance,v.output)
