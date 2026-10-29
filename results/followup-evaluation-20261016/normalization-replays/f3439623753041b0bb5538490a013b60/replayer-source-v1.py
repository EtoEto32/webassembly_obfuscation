"""Replay current normalized artifacts in fresh seven-label bounded batches.

Default prepares and verifies plans only. --execute runs the already-authorized
offline correctness checks, preserving every existing result and OOM record.
"""
import argparse
import json
import os
import subprocess
import sys
import uuid
from datetime import datetime,timezone
from pathlib import Path
from evaluate_followup_normalization import ROOT,OUT,sha,read_plan


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--execute',action='store_true');args=parser.parse_args()
    pp,protocol=read_plan();sp=OUT/'normalization-static.json';static=json.loads(sp.read_text(encoding='utf-8'))
    assert static['status']=='static-validation-complete' and len(static['records'])==77
    parent=OUT/'normalization-replays'
    for p in parent.glob('*/status.json'):
        previous=json.loads(p.read_text(encoding='utf-8'))
        if previous['status'].startswith('running-'):raise RuntimeError('Inspect existing replay handle/process before starting another')
    work=parent/uuid.uuid4().hex;(work/'plans').mkdir(parents=True)
    base=json.loads((OUT/'controlled-check-plan.json').read_text(encoding='utf-8'));plans=[]
    for item in protocol['inputs']:
        plan=json.loads(json.dumps(base));family=item['family'];selected=[r for r in static['records'] if r['input_id']==item['id']];assert len(selected)==7
        needed={'host-original.cjs','glue-loader.cjs','webminerpoolhashcn.wasm','webminerpoolhashcn.js','controlled.cjs'}
        if family=='xmr-wasm':needed.add('xmr-wasm.js')
        plan['assets']=[a for a in plan['assets'] if a['name'] in needed];assert {a['name'] for a in plan['assets']}==needed
        cases=[]
        for r in selected:
            assert sha(ROOT/r['path'])==r['sha256'];identifier=r['input_id']+'--'+r['method'];name=identifier+'.wasm'
            plan['assets'].append(dict(name=name,path=r['path'],sha256=r['sha256']))
            cases.append(dict(id=identifier,family=family,file=name,sha256=r['sha256'],glue=family+'.js' if family!='swamped' else None))
        plan['controlled'].update(artifacts=cases,normalization_applied=True,normalization_plan_sha256=sha(pp),
            static_result_sha256=sha(sp),scope='Reproducibility replay, not new independent implementations or throughput samples.')
        plan['maximum_wall_seconds']=900
        for a in plan['assets']:assert sha(ROOT/a['path'])==a['sha256']
        path=work/'plans'/(item['id']+'.json');path.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        plans.append(dict(batch_id=item['id'],path=str(path.relative_to(ROOT)).replace('\\','/'),sha256=sha(path)))
    manifest=dict(plans=plans,labels=77,normalization_plan_sha256=sha(pp),static_result_sha256=sha(sp),
        frozen_before_execution=True,replayer_sha256=sha(Path(__file__)),unchanged_limits=True)
    manifest_path=work/'manifest.json';manifest_path.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    status=dict(status='prepared-not-executed',pid=os.getpid(),manifest_sha256=sha(manifest_path),batches=[],goal_complete=False)
    def save():
        p=work/'status.tmp';p.write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8');p.replace(work/'status.json')
    save()
    if not args.execute:
        print(json.dumps(dict(status=status['status'],manifest=str(manifest_path),plans=len(plans),labels=77)));return
    seen=set();checks=0
    try:
        for entry in plans:
            label=entry['batch_id'];plan_path=ROOT/entry['path'];assert sha(plan_path)==entry['sha256']
            status['status']='running-'+label;save()
            with (work/(label+'-stdout.txt')).open('w',encoding='utf-8') as output,(work/(label+'-stderr.txt')).open('w',encoding='utf-8') as error:
                done=subprocess.run([sys.executable,'scripts/run_followup_isolated.py','--plan',str(plan_path),
                    '--runner','controlled.cjs','--mode','input-diagnostic'],cwd=ROOT,stdout=output,stderr=error,timeout=1000)
            if done.returncode:raise RuntimeError(label+' replay failed; preserve all records')
            message=json.loads((work/(label+'-stdout.txt')).read_text(encoding='utf-8').strip().splitlines()[-1]);run=Path(message['run'])
            audited=subprocess.run([sys.executable,'scripts/audit_followup_checks.py','controlled',str(run)],cwd=ROOT,capture_output=True,text=True,timeout=120)
            (work/(label+'-audit-stdout.txt')).write_text(audited.stdout,encoding='utf-8');(work/(label+'-audit-stderr.txt')).write_text(audited.stderr,encoding='utf-8')
            if audited.returncode:raise RuntimeError(label+' replay audit failed')
            ap=run/'controlled-audit.json';a=json.loads(ap.read_text(encoding='utf-8'));assert a['status']=='passed'
            rp=run/'outputs/controlled-checks.json';assert a['measurement_sha256']==sha(rp)
            p=json.loads(plan_path.read_text(encoding='utf-8'))
            for artifact in p['controlled']['artifacts']:
                assert artifact['id'] not in seen;seen.add(artifact['id'])
            checks+=a['checks'];status['batches'].append(dict(batch_id=label,run=str(run.relative_to(ROOT)).replace('\\','/'),
                audit='passed',audit_sha256=sha(ap),measurement_sha256=sha(rp),checks=a['checks']));save()
        wanted={r['input_id']+'--'+r['method'] for r in static['records']};assert seen==wanted and checks==2793
        status.update(status='replay-complete',labels=77,unique_sha256=static['unique_output_sha256'],output_checks=checks,
            finished_utc=datetime.now(timezone.utc).isoformat(),scope='Separate reproducibility run; do not add to primary 77-label result as independent evidence.')
        save();print(json.dumps(dict(status=status['status'],directory=str(work),labels=77,checks=checks)))
    except Exception as error:
        status.update(status='failed',error=str(error));save();raise


if __name__=='__main__':main()
