import argparse,json,re
from pathlib import Path
import prototype as p
HERE=Path(__file__).resolve().parent
BASE=p.ROOT/'results/invention-20261019'
def read(name):return json.loads((BASE/name).read_text(encoding='utf-8'))
def main(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False);checks=[];files=[]
    p.q.save(out/'summary.json',dict(status='in_progress',passed=False))
    def check(name,condition):
        checks.append(dict(check=name,passed=bool(condition)))
    for folder,count in [('resource-trigger-v3',72),('resource-trigger-controls-v1',32)]:
        m=read(folder+'/manifest.json');c=read(folder+'/check.json');check(folder+' count',len(m['rows'])==count and len(c['rows'])==count);check(folder+' correctness',c['summary']['passed'] and c['summary']['mismatches']==0 and c['summary']['traps']==0 and c['summary']['calls']==count*1105*4)
        for r in m['rows']:
            for key,hashkey in [('component','sha256'),('recovered','recovered_sha256')]:
                f=BASE/folder/r[key];files.append(dict(path=str(f.relative_to(p.ROOT)),sha256=p.q.digest(f)));check(r['id']+' '+key,p.q.digest(f)==r[hashkey])
        if 'refusals' in m:check('refusals',len(m['refusals'])==5 and all(r['status']=='refused' for r in m['refusals']))
    c=read('resource-trigger-v3/check.json');check('nine negative witnesses',len(c['negative'])==9 and all(r['witness'] for r in c['negative']))
    v=read('resource-trigger-verify-v1/summary.json');check('independent core checks',v['all_pass'] and v['checks']==567)
    rp=read('resource-trigger-replay-v1/records.json');check('144 replay files',len(rp)==144 and all(r['identical'] and r['expected']==r['actual']==p.q.digest(BASE/'resource-trigger-replay-v1'/r['file'])==p.q.digest(BASE/'resource-trigger-v3'/r['file']) for r in rp))
    perf=read('resource-trigger-performance-v2/protocol.json');rt=read('resource-trigger-performance-v2/runtime.json');an=read('resource-trigger-performance-v2/analysis.json')
    check('runtime protocol',len(rt)==135 and perf['fresh_processes']==135 and all(r['warmup']==50000 and r['batch']==(200000 if r['kind']=='core' else 10000) and len(r['ns'])==9 for r in rt))
    check('current extractor and benchmark',perf['extractor_sha256']==p.q.digest(HERE/'prototype.py') and perf['bench_sha256']==p.q.digest(HERE/'bench.cjs'))
    check('360 analysis samples',len(an)==72 and sum(len(r['recovery_ms']) for r in an)==360)
    check('reuse identical analysis',an==read('resource-trigger-performance-v1/analysis.json'))
    rows=read('resource-trigger-report-v3/comparison.json');byid={r['id']:r for r in read('resource-trigger-performance-v2/summary.json')}
    check('nine final comparisons',len(rows)==9)
    for row in rows:
        for mode in ('plain','direct','immediate','deferred'):
            check('report runtime '+str((row['n'],row['family'],mode)),row[mode+'_ns']==byid[f'n{row["n"]}-f{row["family"]}-{mode}-o3']['ns'])
    diag=read('resource-trigger-runtime-probe-v1/probe.json');check('Jco rep minimal counterexample',diag['mismatches']==2 and any(r['y']==0x40000000 and r['actual']==0 for r in diag['rows']))
    links=[]
    for f in HERE.glob('*.md'):
        text=re.sub(r'```[\s\S]*?```','',f.read_text(encoding='utf-8'))
        text=re.sub(r'`[^`]*`','',text)
        for link in re.findall(r'\[[^\]]+\]\(([^)]+)\)',text):
            if link.startswith(('https://','http://','#')):continue
            target=(f.parent/link.split('#')[0]).resolve();links.append(dict(source=f.name,target=link,exists=target.exists()));check('local link '+link,target.exists())
    for f in [*HERE.glob('*.py'),*HERE.glob('*.cjs'),*HERE.glob('*.md'),*HERE.glob('dependencies/*.json'),p.ROOT/'research/isotope-swizzle/prototype.py',p.ROOT/'research/connectivity-elimination/prototype.py']:
        files.append(dict(path=str(f.relative_to(p.ROOT)),sha256=p.q.digest(f)))
    p.q.save(out/'checks.json',checks);p.q.save(out/'files.json',files);p.q.save(out/'links.json',links)
    summary=dict(passed=all(x['passed'] for x in checks),checks=len(checks),failed=[x['check'] for x in checks if not x['passed']],main_conditions=72,control_conditions=32,positive_calls=459680,resource_conditions=52,core_checks=567,reproduced_binaries=144,negative_witnesses=9,fresh_runtime_processes=135,analysis_samples=360,links=len(links),goal_complete=False)
    p.q.save(out/'summary.json',summary);print(json.dumps(summary,indent=2))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('output');v=a.parse_args();main(v.output)
