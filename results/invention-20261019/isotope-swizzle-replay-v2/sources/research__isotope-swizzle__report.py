import argparse,csv,json,statistics
from pathlib import Path
import prototype as q
def main(data,perf,out):
    data=Path(data);perf=Path(perf);out=Path(out);out.mkdir(parents=True,exist_ok=False);rs=json.loads((perf/'summary.json').read_text());manifest=json.loads((data/'manifest.json').read_text());pairs=[]
    for t in rs:
        if t['mode']!='table':continue
        same=lambda r:r['kernel']==t['kernel'] and r['opt']==t['opt'] and r['seed']==t['seed']
        d=next(r for r in rs if same(r) and r['mode']=='decode');r=next(r for r in rs if same(r) and r['mode']=='recovered');p=next(r for r in rs if r['kernel']==t['kernel'] and r['opt']==t['opt'] and r['mode']=='plain')
        pairs.append(dict(file=t['file'],opt=t['opt'],table_ns=t['ns'],decode_ns=d['ns'],plain_ns=p['ns'],recovered_ns=r['ns'],runtime_vs_decode=t['ns']/d['ns'],runtime_vs_plain=t['ns']/p['ns'],runtime_vs_recovered=t['ns']/r['ns'],bytes_vs_decode=t['bytes']/d['bytes'],bytes_vs_plain=t['bytes']/p['bytes'],normalize_ms=t['normalize_rewrite_ms'],read_ms=t['read_ms'],total_analysis_vs_decode=(t['read_ms']+t['normalize_rewrite_ms'])/(d['read_ms']+d['normalize_rewrite_ms']),normalize_vs_decode=t['normalize_rewrite_ms']/d['normalize_rewrite_ms']))
    q.save(out/'pairs.json',pairs)
    with (out/'pairs.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(pairs[0]));w.writeheader();w.writerows(pairs)
    span=lambda a:[min(a),max(a)]
    by={}
    for opt in ('raw','O3'):
        rows=[r for r in pairs if r['opt']==opt];by[opt]={k:span([r[k] for r in rows]) for k in rows[0] if k not in ('file','opt')}
    t=[r for r in manifest if r['mode']=='table'];by['table_transform_ms']=span([r['transform_ms'] for r in t]);by['table_build_ms']=span([r['build_ms'] for r in t]);by['process_peak_rss_kib']=span([r['peak_rss_kib'] for r in rs]);by['logical_linear_memory_bytes']=0
    q.save(out/'summary.json',by);print(json.dumps(by))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('data');p.add_argument('performance');p.add_argument('output');v=p.parse_args();main(v.data,v.performance,v.output)
