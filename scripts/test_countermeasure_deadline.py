"""Real deadline/cleanup check with an idle Node process; no Wasm files mounted."""
import json
import subprocess
import uuid
from pathlib import Path
from run_countermeasure_isolated import ROOT, PREP, attach_with_deadline, remove_owned_container, sha


def main():
    work=ROOT/'results/countermeasures/runtime-runs'/('deadline-test-'+uuid.uuid4().hex)
    work.mkdir(parents=True)
    image=json.loads((PREP/'plan.json').read_text(encoding='utf-8'))['environment']['image']
    args=['docker','create','--name','wasm-deadline-test-'+uuid.uuid4().hex,'--network','none',
        '--cpus','1','--memory','1g','--memory-swap','1g','--pids-limit','64','--read-only',
        '--user','10001:10001','--cap-drop','ALL','--security-opt','no-new-privileges',
        '--entrypoint','node',image,'--max-old-space-size=128','-e',
        "console.log('idle-test-started');setTimeout(()=>{},30000)"]
    container_id=None
    timed_out=False
    try:
        container_id=subprocess.run(args,capture_output=True,text=True,timeout=30,check=True).stdout.strip()
        inspect=json.loads(subprocess.run(['docker','inspect',container_id],capture_output=True,text=True,timeout=30,check=True).stdout)[0]
        assert not inspect['Mounts'] and inspect['HostConfig']['NetworkMode']=='none'
        (work/'container-inspect.json').write_text(json.dumps(inspect,indent=2),encoding='utf-8')
        try:
            attach_with_deadline(container_id,work,2)
        except RuntimeError as error:
            assert 'Wall time limit exceeded' in str(error)
            timed_out=True
        assert timed_out
        assert 'idle-test-started' in (work/'stdout.txt').read_text(encoding='utf-8')
    finally:
        if container_id:
            remove_owned_container(container_id)
    missing=subprocess.run(['docker','inspect',container_id],capture_output=True,text=True,timeout=30)
    assert missing.returncode!=0 and 'no such object' in missing.stderr.lower()
    report=dict(test_sha256=sha(Path(__file__)),launcher_sha256=sha(ROOT/'scripts/run_countermeasure_isolated.py'),
        run=str(work.relative_to(ROOT)).replace('\\','/'),deadline_seconds=2,
        idle_process_started=True,deadline_triggered=timed_out,owned_container_removed=True,
        target_wasm_executed=False,no_input_files_mounted=True,
        scope='Real idle-container deadline and cleanup, not mining execution or performance validation.')
    (PREP/'deadline-checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report))


if __name__=='__main__':
    main()
