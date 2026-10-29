import argparse,hashlib,json,shutil,statistics
from pathlib import Path

def run(main,audit,output):
    main=Path(main).resolve();audit=Path(audit).resolve();out=Path(output).resolve();out.mkdir(parents=True,exist_ok=False);verification={}
    for root in (main,audit):
        pins=json.loads((root/'pins.json').read_text())
        for f,h in pins.items():assert hashlib.sha256((root/f).read_bytes()).hexdigest()==h,(root,f)
        verification[root.name]=len(pins)
    load=lambda root,f:json.loads((root/f).read_text())
    c=load(main,'checks.json');r=load(main,'runtime.json');a=load(audit,'audit.json');ratios=[]
    for name in ('access','compat','features'):
        d={x['adapter'] if '.validator.' in x['file'] else 'recovered' if '.recovered.' in x['file'] else 'plain':x['median_ns'] for x in r['summaries'] if x['file'].startswith(name+'.')}
        ratios.append(dict(name=name,validator_over_plain=d['validator']/d['plain'],validator_over_recognizer=d['validator']/d['recognizer'],recovered_over_plain=d['recovered']/d['plain']))
    facts=dict(conditions=len(c['results']),calls=sum(x['calls'] for x in c['results']),positive=sum(x['positive'] for x in c['results']),negative=sum(x['negative'] for x in c['results']),query_cases=len(c['queries']),valid_queries=sum(x['actual'] for x in c['queries']),replayed=len(a['replay']),wabt_calls=sum(len(x['actual']) for x in a['interpreter']),smt_unsat=len(a['smt']),analysis_repeats=len(a['analysis_repeats']),runtime_processes=len(r['runtime']),ratios=ratios,goal_complete=False,decision='not adopted: public validator summary recovers all protected conditions; no established independent novelty or protection advantage')
    for name,value in [('facts.json',facts),('verification.json',verification)]: (out/name).write_text(json.dumps(value,indent=2),encoding='utf8')
    shutil.copy2(__file__,out/'source-report.py');print(json.dumps(dict(verified=verification,facts=facts)))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('main');ap.add_argument('audit');ap.add_argument('output');a=ap.parse_args();run(a.main,a.audit,a.output)
