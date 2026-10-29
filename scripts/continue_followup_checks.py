"""Wait for the timed pilot, audit it, then run correctness diagnostics serially."""
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
    runtime=args.after.resolve();assert runtime.is_relative_to(OUT/'runs')
    work=OUT/'serial-checks'/uuid.uuid4().hex;work.mkdir(parents=True)
    status=dict(status='waiting-for-timed-pilot',pid=os.getpid(),started_utc=datetime.now(timezone.utc).isoformat(),
        after=str(runtime.relative_to(ROOT)),steps=[],goal_complete=False)
    def save():
        (work/'status.json').write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
    save();deadline=time.monotonic()+3600
    def command(label,arguments):
        status['status']=label;save()
        result=subprocess.run([sys.executable,*arguments],cwd=ROOT,capture_output=True,text=True,timeout=900)
        (work/(label+'-stdout.txt')).write_text(result.stdout,encoding='utf-8')
        (work/(label+'-stderr.txt')).write_text(result.stderr,encoding='utf-8')
        status['steps'].append(dict(label=label,exit_code=result.returncode));save()
        if result.returncode:
            raise RuntimeError(label+' failed; see preserved output')
        return result
    try:
        while not (runtime/'completion.json').exists():
            if (runtime/'failure.json').exists():
                raise RuntimeError('Timed pilot failed; do not start dependent experiments')
            if time.monotonic()>deadline:
                raise TimeoutError('Timed pilot completion was not recorded within one hour')
            time.sleep(2)
        completion=json.loads((runtime/'completion.json').read_text(encoding='utf-8'))
        assert completion['exit_code']==0 and not completion['state']['OOMKilled']
        command('audit-runtime',['scripts/audit_followup_runtime.py',str(runtime)])
        for label,plan,runner,output in [
            ('path-checks','path-plan.json','paths.cjs','paths.json'),
            ('controlled-checks','controlled-check-plan.json','controlled.cjs','controlled-checks.json')]:
            result=command(label,['scripts/run_followup_isolated.py','--plan',str(OUT/plan),'--runner',runner,'--mode','input-diagnostic'])
            finished=json.loads(result.stdout.strip().splitlines()[-1]);run=Path(finished['run'])
            data=json.loads((run/'outputs'/output).read_text(encoding='utf-8'));assert data['status']=='complete'
            status['steps'][-1]['run']=str(run.relative_to(ROOT));save()
        status['status']='stage-complete';status['finished_utc']=datetime.now(timezone.utc).isoformat();save()
        print(json.dumps(status,indent=2))
    except Exception as error:
        status['status']='failed';status['error']=str(error);save();raise


if __name__=='__main__':
    main()
