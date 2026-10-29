import argparse,json,statistics
from pathlib import Path
import prototype as p

def main(data,performance,out):
    data,performance,out=map(Path,(data,performance,out));out.mkdir(parents=True,exist_ok=False)
    m=json.loads((data/'manifest.json').read_text());runtime=json.loads((performance/'summary.json').read_text());analysis=json.loads((performance/'analysis.json').read_text());byid={r['id']:r for r in runtime};aa={r['id']:r for r in analysis};rows=[]
    for n in (8,16,32):
      for f in range(3):
        row=dict(n=n,family=f)
        for mode in ('plain','single','pair-zero','pair-noise','pair-recode'):
            key=f'n{n}-f{f}-{mode}-o3';r=byid[key]
            for col in ('ns','bytes','rss_kib'):row[mode+'_'+col]=r[col]
            row[mode+'_process_spread']=max(r['process_medians_ns'])/min(r['process_medians_ns'])
            if mode!='plain':
                runs=aa[key]['runs']
                for col in ('read_ms','recovery_ms'):row[mode+'_'+col]=statistics.median(x[col] for x in runs)
                row[mode+'_total_ms']=statistics.median(x['read_ms']+x['recovery_ms'] for x in runs)
        for a,b in [('single','plain'),('pair-recode','plain'),('pair-recode','single'),('pair-recode','pair-noise'),('pair-noise','pair-zero')]:
            for col in ('ns','bytes','read_ms','recovery_ms','total_ms'):
                if a+'_'+col in row and b+'_'+col in row:row[a+'/'+b+'_'+col]=row[a+'_'+col]/row[b+'_'+col]
        rows.append(row)
    ranges={key:[min(r[key] for r in rows),statistics.median(r[key] for r in rows),max(r[key] for r in rows)] for key in rows[0] if key not in ('n','family')}
    ranges['transform_ms']={mode:[min(r['transform']['transform_ms'] for r in m['rows'] if r['mode']==mode and not r['opt']),max(r['transform']['transform_ms'] for r in m['rows'] if r['mode']==mode and not r['opt'])] for mode in ('plain','single','pair-zero','pair-noise','pair-recode')}
    p.q.save(out/'comparison.json',rows);p.q.save(out/'ranges.json',ranges)
    cols=['n','family','plain_ns','single_ns','pair-zero_ns','pair-noise_ns','pair-recode_ns','single_recovery_ms','pair-recode_recovery_ms','pair-recode_bytes']
    lines=['| '+' | '.join(cols)+' |','|'+'---|'*len(cols)]+['| '+' | '.join(str(round(r[c],4)) if isinstance(r[c],float) else str(r[c]) for c in cols)+' |' for r in rows]
    (out/'table.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in ranges.items() if '/' in k or k in ('pair-recode_recovery_ms','pair-recode_read_ms','pair-recode_rss_kib','transform_ms')},indent=2))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('data');a.add_argument('performance');a.add_argument('output');v=a.parse_args();main(v.data,v.performance,v.output)
