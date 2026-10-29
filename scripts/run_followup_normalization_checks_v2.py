"""Execute revised bounded batches and carry forward the verified first batch."""
import json
import os
import subprocess
import sys
import uuid
from datetime import datetime,timezone
from pathlib import Path
from evaluate_followup_normalization import ROOT,OUT,sha


def main():
    manifest_path=OUT/'normalization-check-plans-v2.json';manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    parent=OUT/'normalization-execution-v2';assert not list(parent.glob('*/status.json'))
    reuse=manifest['reused'];prior=ROOT/reuse['run'];audit_path=prior/'controlled-audit.json'
    a=json.loads(audit_path.read_text(encoding='utf-8'));assert sha(audit_path)==reuse['audit_sha256'] and a['status']=='passed'
    assert a['measurement_sha256']==sha(prior/'outputs/controlled-checks.json')
    work=parent/uuid.uuid4().hex;work.mkdir(parents=True)
    status=dict(status='starting',pid=os.getpid(),started_utc=datetime.now(timezone.utc).isoformat(),
        manifest_sha256=sha(manifest_path),batches=[dict(batch_id='swamped-completed',run=reuse['run'],audit='passed',audit_sha256=sha(audit_path),reused=True)],goal_complete=False)
    def save():
        p=work/'status.tmp';p.write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8');p.replace(work/'status.json')
    save()
    try:
        for entry in manifest['plans']:
            plan=ROOT/entry['path'];assert sha(plan)==entry['sha256'];label=entry['batch_id'];status['status']='running-'+label;save()
            with (work/(label+'-stdout.txt')).open('w',encoding='utf-8') as out,(work/(label+'-stderr.txt')).open('w',encoding='utf-8') as error:
                done=subprocess.run([sys.executable,'scripts/run_followup_isolated.py','--plan',str(plan),
                    '--runner','controlled.cjs','--mode','input-diagnostic'],cwd=ROOT,stdout=out,stderr=error,timeout=1000)
            if done.returncode:raise RuntimeError(label+' correctness failed; preserve results')
            message=json.loads((work/(label+'-stdout.txt')).read_text(encoding='utf-8').strip().splitlines()[-1]);run=Path(message['run'])
            row=dict(batch_id=label,run=str(run.relative_to(ROOT)).replace('\\','/'),audit='pending',reused=False);status['batches'].append(row);save()
            audited=subprocess.run([sys.executable,'scripts/audit_followup_checks.py','controlled',str(run)],cwd=ROOT,capture_output=True,text=True,timeout=120)
            (work/(label+'-audit-stdout.txt')).write_text(audited.stdout,encoding='utf-8');(work/(label+'-audit-stderr.txt')).write_text(audited.stderr,encoding='utf-8')
            if audited.returncode:raise RuntimeError(label+' audit failed; preserve results')
            row.update(audit='passed',audit_sha256=sha(run/'controlled-audit.json'));save()
        status.update(status='stage-complete',finished_utc=datetime.now(timezone.utc).isoformat());save();print(json.dumps(status,indent=2))
    except Exception as error:
        status.update(status='failed',error=str(error));save();raise


if __name__=='__main__':main()
