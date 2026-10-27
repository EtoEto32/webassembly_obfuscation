"""Run a frozen reviewed follow-up plan in the existing offline container image."""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from run_countermeasure_isolated import attach_with_deadline, remove_owned_container

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def docker(*args, timeout=45):
    return subprocess.run(['docker', *args], capture_output=True, text=True,
                          timeout=timeout, check=True).stdout


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan', type=Path, default=ROOT/'results/followup-evaluation-20261016/plan.json')
    parser.add_argument('--runner', default='input-diagnostic.cjs')
    parser.add_argument('--mode', default='input-diagnostic', choices=['input-diagnostic', 'runtime', 'probe'])
    args = parser.parse_args()
    plan_path=args.plan.resolve()
    assert plan_path.is_relative_to(ROOT)
    plan=json.loads(plan_path.read_text(encoding='utf-8'))
    assert plan.get('frozen_before_execution') is True
    permission_path=ROOT/'results/countermeasures/runtime-preparation/professor-permission.json'
    permission=json.loads(permission_path.read_text(encoding='utf-8'))
    assert permission['confirmed'] is True
    assert sha(permission_path)==plan['authorization']['inherited_professor_permission_sha256']
    assert plan['authorization']['user_request']
    assert args.runner in {a['name'] for a in plan['assets']}
    for asset in plan['assets']:
        path=(ROOT/asset['path']).resolve()
        assert path.is_relative_to(ROOT) and sha(path)==asset['sha256']
        assert Path(asset['name']).name==asset['name'] and '/' not in asset['name'] and '\\' not in asset['name']
    # Fresh directories preserve all earlier results, including failed attempts.
    work=plan_path.parent/'runs'/(args.mode+'-'+uuid.uuid4().hex)
    inputs=work/'inputs';outputs=work/'outputs'
    inputs.mkdir(parents=True);outputs.mkdir()
    shutil.copyfile(plan_path,inputs/'plan.json')
    for asset in plan['assets']:
        shutil.copyfile(ROOT/asset['path'],inputs/asset['name'])
    plan_sha=sha(plan_path)
    command=['create','--name','wasm-followup-'+uuid.uuid4().hex,
        '--network','none','--cpus','1','--cpuset-cpus','0','--memory','1g','--memory-swap','1g',
        '--pids-limit','64','--read-only','--user','10001:10001','--cap-drop','ALL',
        '--security-opt','no-new-privileges','--tmpfs','/tmp:rw,nosuid,nodev,size=64m',
        '--env','PLAN_SHA256='+plan_sha,'--env','EXPERIMENT_IMAGE_ID='+plan['image'],
        '--mount',f'type=bind,source={inputs},target=/inputs,readonly',
        '--mount',f'type=bind,source={outputs},target=/outputs','--entrypoint','node',
        plan['image'],'--max-old-space-size=256','/inputs/'+args.runner]
    container_id=None
    try:
        if docker('image','inspect',plan['image'],'--format','{{.Id}}').strip()!=plan['image']:
            raise RuntimeError('Image mismatch')
        container_id=docker(*command).strip()
        assert re.fullmatch('[a-f0-9]{64}',container_id)
        inspection=json.loads(docker('inspect',container_id))[0]
        host=inspection['HostConfig'];mounts={m['Destination']:m for m in inspection['Mounts']}
        assert inspection['Image']==plan['image'] and inspection['Config']['User']=='10001:10001'
        assert host['NetworkMode']=='none' and host['NanoCpus']==10**9 and host['CpusetCpus']=='0'
        assert host['Memory']==1024**3 and host['MemorySwap']==1024**3 and host['PidsLimit']==64
        assert host['ReadonlyRootfs'] and 'ALL' in host['CapDrop']
        assert any(s.startswith('no-new-privileges') for s in host['SecurityOpt'])
        assert not mounts['/inputs']['RW'] and mounts['/outputs']['RW']
        (work/'container-inspect.json').write_text(json.dumps(inspection,indent=2),encoding='utf-8')
        (work/'launch.json').write_text(json.dumps(dict(plan_sha256=plan_sha,runner=args.runner,
            launcher_sha256=sha(Path(__file__)),started_utc=datetime.now(timezone.utc).isoformat(),
            arguments=command,container_id=container_id),indent=2),encoding='utf-8')
        limit=plan.get('maximum_wall_seconds',plan.get('input_diagnostic',{}).get('maximum_wall_seconds',300))
        code,elapsed=attach_with_deadline(container_id,work,limit)
        state=json.loads(docker('inspect',container_id))[0]['State']
        (work/'completion.json').write_text(json.dumps(dict(exit_code=code,elapsed_seconds=elapsed,state=state),indent=2),encoding='utf-8')
        if code or state['ExitCode'] or state['OOMKilled'] or state['Running']:
            raise RuntimeError('Run did not finish successfully; preserve diagnostics')
        print(json.dumps(dict(status='completed',run=str(work),elapsed_seconds=elapsed)))
    except Exception as error:
        (work/'failure.json').write_text(json.dumps(dict(error=str(error),container_id=container_id,
            plan_sha256=plan_sha),indent=2),encoding='utf-8')
        raise
    finally:
        if container_id:
            remove_owned_container(container_id)


if __name__=='__main__':
    main()
