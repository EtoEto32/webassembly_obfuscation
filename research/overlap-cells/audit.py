import argparse,json,re
from pathlib import Path
import prototype as p
HERE=Path(__file__).resolve().parent
BASE=p.ROOT/'results/invention-20261019'
def read(f):return json.loads((BASE/f).read_text(encoding='utf-8'))
def main(output):
    out=Path(output);out.mkdir(parents=True,exist_ok=False);checks=[];files=[]
    def check(label,ok):checks.append(dict(check=label,passed=bool(ok)))
    for folder,count,calls,rec in [('overlap-cells-v1',90,550116,72),('overlap-cells-controls-v1',30,204876,24)]:
        m=read(folder+'/manifest.json');c=read(folder+'/checks.json');s=c['summary'];check(folder+' counts',len(m['rows'])==len(c['rows'])==count and s['calls']==calls);check(folder+' correctness',s['passed'] and s['mismatches']==s['traps']==0);check(folder+' recoveries',sum(r['canonical_match'] is True for r in m['rows'])==rec);check(folder+' refusals',len(m['refusals'])==3 and all(r['status']=='refused' for r in m['refusals']));check(folder+' negatives',len(c['negative'])==(9 if count==90 else 3) and all(r['detected'] for r in c['negative']))
        for r in m['rows']:
            for k,h in [('file','sha256'),('recovered','recovered_sha256')]:
                if not r[k]:continue
                f=BASE/folder/r[k];check(folder+'/'+r[k],p.q.digest(f)==r[h]);files.append(dict(path=str(f.relative_to(p.ROOT)),sha256=p.q.digest(f)))
            if r['recovered']:check('canonical '+r['id'],p.q.digest(BASE/folder/r['recovered'])==p.q.digest(BASE/folder/r['canonical']))
            if r['mode'] in ('pair-noise','pair-recode'):check('support '+r['id'],all(s['support_components']==4 and s['all_table_components']==1 for s in r['attack']['support']))
    v=read('overlap-cells-verify-v1/summary.json');check('independent VM',v==dict(files=171,checks=1197,passed=True))
    replay=read('overlap-cells-replay-v1/records.json');check('180 byte reproductions',len(replay)==180 and all(r['identical'] and r['actual']==r['expected']==p.q.digest(BASE/'overlap-cells-v1'/r['file'])==p.q.digest(BASE/'overlap-cells-replay-v1'/r['file']) for r in replay))
    perf=read('overlap-cells-performance-v2/protocol.json');rt=read('overlap-cells-performance-v2/runtime.json');aa=read('overlap-cells-performance-v2/analysis.json')
    check('runtime reuse',rt==read('overlap-cells-performance-v1/runtime.json') and perf['new_runtime_processes']==0 and perf['runtime_reuse']['instrumented_byte_matches']==45)
    check('135 runtime processes',len(rt)==135 and all(r['warmup']==100000 and r['batch']==20000 and len(r['ns'])==9 for r in rt))
    check('360 diagnostic-free analyses',len(aa)==72 and sum(len(r['runs']) for r in aa)==360 and perf['diagnostics'] is False and all('all_table_components' not in s for r in aa for a in r['runs'] for s in a['support']))
    check('current source',perf['prototype_sha256']==p.q.digest(HERE/'prototype.py') and perf['bench_sha256']==p.q.digest(HERE/'bench.cjs'))
    check('matching performance checksums',all(len({r['checksum'] for r in rt if r['n']==n and r['family']==f})==1 for n in (8,16,32) for f in range(3)))
    report=read('overlap-cells-report-v2/comparison.json');summ={r['id']:r for r in read('overlap-cells-performance-v2/summary.json')};check('nine comparisons',len(report)==9)
    for r in report:
        for mode in ('plain','single','pair-zero','pair-noise','pair-recode'):check('runtime '+str((r['n'],r['family'],mode)),r[mode+'_ns']==summ[f'n{r["n"]}-f{r["family"]}-{mode}-o3']['ns'])
    links=[]
    for f in HERE.glob('*.md'):
        s=re.sub(r'```[\s\S]*?```','',f.read_text(encoding='utf-8'));s=re.sub(r'`[^`]*`','',s)
        for link in re.findall(r'(?<!\w)\[[^\]]+\]\(([^)]+)\)',s):
            if link.startswith(('https://','http://','#')):continue
            exists=(f.parent/link.split('#')[0]).resolve().exists();links.append(dict(source=f.name,target=link,exists=exists));check('link '+link,exists)
    for f in [*HERE.glob('*.py'),*HERE.glob('*.cjs'),*HERE.glob('*.md'),p.ROOT/'research/isotope-swizzle/prototype.py',p.ROOT/'research/connectivity-elimination/prototype.py']:files.append(dict(path=str(f.relative_to(p.ROOT)),sha256=p.q.digest(f)))
    p.q.save(out/'checks.json',checks);p.q.save(out/'files.json',files);p.q.save(out/'links.json',links);summary=dict(passed=all(c['passed'] for c in checks),checks=len(checks),failed=[c['check'] for c in checks if not c['passed']],goal_complete=False);p.q.save(out/'summary.json',summary);print(summary)
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('output');v=a.parse_args();main(v.output)
