"""Run and audit preplanned sessions serially, stopping on any failure."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/followup-evaluation-20261016'


def main():
    manifest=json.loads((OUT/'confirmatory-plans.json').read_text(encoding='utf-8'))
    existing=list((OUT/'confirmatory-execution').glob('*/status.json')) if (OUT/'confirmatory-execution').exists() else []
    if existing:raise RuntimeError('Inspect existing execution instead of starting duplicate sessions')
    work=OUT/'confirmatory-execution'/uuid.uuid4().hex;work.mkdir(parents=True)
    status=dict(status='starting',pid=os.getpid(),started_utc=datetime.now(timezone.utc).isoformat(),sessions=[],goal_complete=False)
    def save():
        temporary=work/'status.tmp';temporary.write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8');temporary.replace(work/'status.json')
    save()
    try:
        for i,entry in enumerate(manifest['plans'],1):
            plan=ROOT/entry['path'];assert hashlib.sha256(plan.read_bytes()).hexdigest()==entry['sha256']
            status['status']='running-session-'+str(i);save()
            with (work/f'session-{i}-stdout.txt').open('w',encoding='utf-8') as output,(work/f'session-{i}-stderr.txt').open('w',encoding='utf-8') as error:
                result=subprocess.run([sys.executable,'scripts/run_followup_isolated.py','--plan',str(plan),
                    '--runner','confirmatory.cjs','--mode','runtime'],cwd=ROOT,stdout=output,stderr=error,timeout=7500)
            if result.returncode:raise RuntimeError('Session '+str(i)+' failed; preserve logs and stop')
            summary=json.loads((work/f'session-{i}-stdout.txt').read_text(encoding='utf-8').strip().splitlines()[-1]);run=Path(summary['run'])
            row=dict(session=i,run=str(run.relative_to(ROOT)),audit='pending');status['sessions'].append(row);status['status']='auditing-session-'+str(i);save()
            audit=subprocess.run([sys.executable,'scripts/audit_followup_confirmatory.py',str(run)],cwd=ROOT,capture_output=True,text=True,timeout=60)
            (work/f'session-{i}-audit-stdout.txt').write_text(audit.stdout,encoding='utf-8');(work/f'session-{i}-audit-stderr.txt').write_text(audit.stderr,encoding='utf-8')
            if audit.returncode:raise RuntimeError('Session '+str(i)+' audit failed; preserve logs and stop')
            row['audit']='passed';save()
        status['status']='stage-complete';status['finished_utc']=datetime.now(timezone.utc).isoformat();save();print(json.dumps(status,indent=2))
    except Exception as error:
        status['status']='failed';status['error']=str(error);save();raise


if __name__=='__main__':main()
