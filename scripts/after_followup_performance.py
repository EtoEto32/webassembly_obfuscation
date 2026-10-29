"""Run dependent static analysis and call-site checks after all timings stop."""
import argparse
import json
import os
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/followup-evaluation-20261016'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--after',type=Path,required=True);args=parser.parse_args()
    parent=args.after.resolve();assert parent.is_relative_to(OUT/'confirmatory-execution')
    existing=list((OUT/'post-performance').glob('*/status.json')) if (OUT/'post-performance').exists() else []
    if existing:raise RuntimeError('Inspect existing dependent job; do not duplicate it')
    work=OUT/'post-performance'/uuid.uuid4().hex;work.mkdir(parents=True)
    status=dict(status='waiting-for-three-timed-sessions',pid=os.getpid(),after=str(parent.relative_to(ROOT)),
        started_utc=datetime.now(timezone.utc).isoformat(),steps=[],goal_complete=False,normalization_applied=False)
    def save():
        temporary=work/'status.tmp';temporary.write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8');temporary.replace(work/'status.json')
    save();deadline=time.monotonic()+6*3600
    def command(label,arguments,timeout=900):
        status['status']=label;save()
        result=subprocess.run([sys.executable,*arguments],cwd=ROOT,capture_output=True,text=True,timeout=timeout)
        (work/(label+'-stdout.txt')).write_text(result.stdout,encoding='utf-8');(work/(label+'-stderr.txt')).write_text(result.stderr,encoding='utf-8')
        status['steps'].append(dict(label=label,exit_code=result.returncode));save()
        if result.returncode:raise RuntimeError(label+' failed; dependent analysis stopped')
        return result
    try:
        while True:
            parent_status=json.loads((parent/'status.json').read_text(encoding='utf-8'))
            if parent_status['status']=='stage-complete':break
            if parent_status['status']=='failed':raise RuntimeError('Timed sessions failed; preserve partial results')
            if time.monotonic()>deadline:raise TimeoutError('No recorded completion within six hours; revalidate live process before any restart')
            time.sleep(5)
        command('measure-structure',['scripts/measure_followup_structure.py'])
        command('summarize-performance',['scripts/summarize_followup_confirmatory.py','--execution',str(parent)])
        finished=command('callsite-checks',['scripts/run_followup_isolated.py','--plan',str(OUT/'callsite-plan.json'),
            '--runner','paths.cjs','--mode','input-diagnostic'])
        run=Path(json.loads(finished.stdout.strip().splitlines()[-1])['run'])
        command('audit-callsites',['scripts/audit_followup_checks.py','paths',str(run)])
        command('summarize-callsites',['scripts/summarize_followup_callsites.py',str(run)])
        status['status']='stage-complete';status['finished_utc']=datetime.now(timezone.utc).isoformat();save();print(json.dumps(status,indent=2))
    except Exception as error:
        status['status']='failed';status['error']=str(error);save();raise


if __name__=='__main__':main()
