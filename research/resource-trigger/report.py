import argparse,json,statistics
from pathlib import Path
import prototype as p
def span(xs):
    xs=list(xs);return [min(xs),max(xs)]
def main(data,perf,out):
    data,perf,out=map(Path,(data,perf,out));out.mkdir(parents=True,exist_ok=False)
    m=json.loads((data/'manifest.json').read_text());rt=json.loads((perf/'summary.json').read_text());an=json.loads((perf/'analysis.json').read_text());check=json.loads((data/'check.json').read_text())['summary'];rows=[]
    for n in sorted(set(r['n'] for r in m['rows'])):
      for fam in range(3):
        rr={r['mode']:r for r in rt if r['n']==n and r['family']==fam};aa={r['mode']:r for r in an if r['opt'] and r['n']==n and r['family']==fam};dd={r['mode']:r for r in m['rows'] if r['opt'] and r['n']==n and r['family']==fam}
        row=dict(n=n,family=fam)
        for mode in ('core','plain','direct','immediate','deferred'):row[mode+'_ns']=rr[mode]['ns']
        for mode in ('plain','direct','immediate','deferred'):
            row[mode+'_recovery_ms']=statistics.median(aa[mode]['recovery_ms']);row[mode+'_read_ms']=statistics.median(aa[mode]['read_ms']);row[mode+'_total_ms']=statistics.median(x+y for x,y in zip(aa[mode]['read_ms'],aa[mode]['recovery_ms']))
            row[mode+'_component_bytes']=dd[mode]['component_bytes'];row[mode+'_runtime_files_bytes']=sum(v for k,v in dd[mode]['transpile']['files'].items() if k.endswith(('.js','.wasm')))
        for base in ('plain','direct','immediate'):
            for metric in ('ns','recovery_ms','total_ms','component_bytes','runtime_files_bytes'):row['deferred_over_'+base+'_'+metric]=row['deferred_'+metric]/row[base+'_'+metric]
        row['plain_over_core_ns']=row['plain_ns']/row['core_ns'];rows.append(row)
    ratio_keys=[k for k in rows[0] if '_over_' in k]
    summary=dict(check=check,conditions=len(m['rows']),optimization='internal core only, Jco/Binaryen 130.0.0',ranges={k:span(r[k] for r in rows) for k in ratio_keys},deferred_recovery_ms=span(r['deferred_recovery_ms'] for r in rows),deferred_reader_ms=span(r['deferred_read_ms'] for r in rows),deferred_transform_ms=span(r['transform']['transform_ms'] for r in m['rows'] if not r['opt'] and r['mode']=='deferred'),deferred_transpile_ms=span(r['transpile']['transpile_ms'] for r in m['rows'] if r['opt'] and r['mode']=='deferred'),deferred_rss_kib=span(r['peak_rss_kib'] for r in rt if r['mode']=='deferred'),deferred_heap_bytes=span(r['heap_used_bytes'] for r in rt if r['mode']=='deferred'),max_process_median_ratio=max(max(r['process_medians_ns'])/min(r['process_medians_ns']) for r in rt),all_refusals=all(r['status']=='refused' for r in m['refusals']),o3_deferred_allocations=[r['recovery']['allocations'] for r in m['rows'] if r['opt'] and r['mode']=='deferred'])
    p.q.save(out/'comparison.json',rows);p.q.save(out/'summary.json',summary)
    lines=['# Resource trigger実測比較','','各値はO3後。実行時間は3 fresh processそれぞれ9 batchの中央値を取り、その中央値。解析本体は5回の中央値。msとnsを直接割った保護強度は計算しない。','','|N|族|plain ns|direct ns|immediate ns|deferred ns|deferred/direct 実行比|deferred/direct 解析本体比|deferred/immediate 解析本体比|','|---|---|---|---|---|---|---|---|---|']
    for r in rows:lines.append('|'+ '|'.join(str(r[k]) if k in ('n','family') else f'{r[k]:.3f}' for k in ('n','family','plain_ns','direct_ns','immediate_ns','deferred_ns','deferred_over_direct_ns','deferred_over_direct_recovery_ms','deferred_over_immediate_recovery_ms'))+'|')
    (out/'comparison.md').write_text('\n'.join(lines)+'\n',encoding='utf-8');print(json.dumps(summary,indent=2))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('data');a.add_argument('performance');a.add_argument('output');v=a.parse_args();main(v.data,v.performance,v.output)
