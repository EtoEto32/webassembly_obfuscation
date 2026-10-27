import argparse,hashlib,json,shutil
from pathlib import Path

def run(main,audit,output):
    main=Path(main).resolve();audit=Path(audit).resolve();out=Path(output).resolve();out.mkdir(parents=True,exist_ok=False)
    verification={}
    for root in (main,audit):
        pins=json.loads((root/'pins.json').read_text())
        for f,h in pins.items():assert hashlib.sha256((root/f).read_bytes()).hexdigest()==h,(root,f)
        verification[root.name]=len(pins)
    load=lambda root,name:json.loads((root/name).read_text())
    checks=load(main,'correctness.json')['results'];parallel=load(main,'parallel.json')['results'];perf=load(main,'performance.json');av=load(audit,'audit.json')
    ratios=[]
    for profile in ('low','high','both','wide'):
        d={r['mode']:r for r in perf['summaries'] if r['profile']==profile}
        ratios.append(dict(profile=profile,auto_over_plain=d['auto']['median_ns']/d['plain']['median_ns'],auto_over_identity=d['auto']['median_ns']/d['identity']['median_ns']))
    facts=dict(conditions=len(checks),calls=sum(r['calls'] for r in checks),expected_traps=sum(r['traps'] for r in checks),full_memory_snapshots=sum(r['full_memory_snapshots'] for r in checks),
        parallel_updates=sum(r['tickets']['operations'] for r in parallel),wait_notify_cases=sum(len(r['waits']) for r in parallel),
        recovered_conditions=len(checks),recovery_store_calls_per_binary=4,replayed=len(av['replay']),wabt_calls=sum(len(r['actual']) for r in av['wabt']),
        benchmark_check=av['bench'],runtime_processes=len(perf['runtime']),ratios=ratios,goal_complete=False,
        decision='correctness condition and negative result; no established independent novelty or additional protection')
    for name,v in [('facts.json',facts),('verification.json',verification)]: (out/name).write_text(json.dumps(v,indent=2),encoding='utf8')
    shutil.copy2(__file__,out/'source-report.py')
    print(json.dumps(dict(verified=verification,facts=facts)))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('main');ap.add_argument('audit');ap.add_argument('output');a=ap.parse_args();run(a.main,a.audit,a.output)
