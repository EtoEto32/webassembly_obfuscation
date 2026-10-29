"""Stage frozen files; probe runs no Wasm. Execute requires separate user evidence."""
import argparse
import hashlib
import json
import shutil
import subprocess
import time
import uuid
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREP = ROOT/'results/countermeasures/runtime-preparation'
RUNS = ROOT/'results/countermeasures/runtime-runs'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def attach_with_deadline(container_id, work, limit):
    """Attach until terminal or deadline; caller always removes its owned container."""
    if not re.fullmatch('[a-f0-9]{64}',container_id):
        raise RuntimeError('Unexpected container ID')
    start=time.monotonic()
    with (work/'stdout.txt').open('w',encoding='utf-8') as stdout, (work/'stderr.txt').open('w',encoding='utf-8') as stderr:
        process=subprocess.Popen(['docker','start','-a',container_id],stdout=stdout,stderr=stderr)
        try:
            code=process.wait(timeout=limit)
        except subprocess.TimeoutExpired:
            process.kill();process.wait(timeout=30)
            (work/'timeout.json').write_text(json.dumps(dict(container_id=container_id,
                maximum_wall_seconds=limit,elapsed_seconds=time.monotonic()-start,
                attached_cli_terminated=True,container_removal_required=True),indent=2),encoding='utf-8')
            raise RuntimeError('Wall time limit exceeded; stopping owned container')
    return code,time.monotonic()-start


def remove_owned_container(container_id):
    if not re.fullmatch('[a-f0-9]{64}',container_id):
        raise RuntimeError('Unexpected container ID')
    subprocess.run(['docker','rm','-f',container_id],capture_output=True,timeout=30,check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode',choices=['describe','probe','execute'],default='describe')
    parser.add_argument('--permission',type=Path)
    args = parser.parse_args()
    plan_path=PREP/'plan.json'
    plan=json.loads(plan_path.read_text(encoding='utf-8'))
    plan_sha=sha(plan_path)
    if args.mode=='execute':
        if not args.permission:
            raise RuntimeError('Explicit professor permission evidence is required before execution')
        permission=json.loads(args.permission.read_text(encoding='utf-8'))
        if (permission.get('confirmed') is not True or permission.get('plan_sha256')!=plan_sha
            or not permission.get('user_statement') or not permission.get('confirmed_at')):
            raise RuntimeError('Permission evidence must match this plan and the user confirmation')
    for item in plan['artifacts']:
        if sha(ROOT/item['path']) != item['sha256']:
            raise RuntimeError('Artifact digest mismatch')
    if sha(ROOT/plan['host']['path']) != plan['host']['sha256']:
        raise RuntimeError('Host digest mismatch')
    runner=ROOT/'experiments/runtime-reference/countermeasure-benchmark.cjs'
    description=dict(mode=args.mode,plan_sha256=plan_sha,runner_sha256=sha(runner),
                     unique_artifacts=len(plan['artifacts']),isolation=plan['environment'],
                     target_wasm_executed=False if args.mode!='execute' else 'not started yet')
    if args.mode=='describe':
        (PREP/'launcher-description.json').write_text(json.dumps(description,indent=2),encoding='utf-8')
        print(json.dumps(description));return
    # A fresh directory prevents a probe from replacing any measured result.
    run_id=args.mode+'-'+uuid.uuid4().hex
    work=RUNS/run_id
    staged=work/'inputs';outputs=work/'outputs'
    staged.mkdir(parents=True);outputs.mkdir()
    shutil.copyfile(plan_path,staged/'plan.json')
    shutil.copyfile(ROOT/plan['host']['path'],staged/'swamped-host.cjs')
    shutil.copyfile(runner,staged/'runner.cjs')
    for item in plan['artifacts']:
        shutil.copyfile(ROOT/item['path'],staged/(item['sha256']+'.wasm'))
    if args.mode=='execute':
        shutil.copyfile(args.permission,staged/'permission.json')
    image=plan['environment']['image']
    container_name='wasm-countermeasure-'+uuid.uuid4().hex
    arguments=['create','--name',container_name,'--network','none','--cpus','1',
               '--memory','1g','--memory-swap','1g','--pids-limit','64','--read-only',
               '--user','10001:10001','--cap-drop','ALL','--security-opt','no-new-privileges',
               '--tmpfs','/tmp:rw,nosuid,nodev,size=64m','--env','PLAN_SHA256='+plan_sha,
               '--env','EXPERIMENT_IMAGE_ID='+image,
               '--mount',f'type=bind,source={staged},target=/inputs,readonly',
               '--mount',f'type=bind,source={outputs},target=/outputs',
               '--entrypoint','node']
    if args.mode=='execute':
        arguments += ['--env','PROFESSOR_PERMISSION_CONFIRMED=yes']
    arguments += [image,'--max-old-space-size=256','/inputs/runner.cjs',
                  '--execute' if args.mode=='execute' else '--validate-only']
    container_id=None
    try:
        result=subprocess.run(['docker',*arguments],capture_output=True,text=True,timeout=30,check=True)
        container_id=result.stdout.strip()
        metadata=json.loads(subprocess.run(['docker','inspect',container_id],capture_output=True,text=True,timeout=30,check=True).stdout)[0]
        host=metadata['HostConfig'];config=metadata['Config']
        if not (host['NetworkMode']=='none' and host['NanoCpus']==1_000_000_000 and
                host['Memory']==1024**3 and host['MemorySwap']==1024**3 and host['PidsLimit']==64 and
                host['ReadonlyRootfs'] is True and 'ALL' in host['CapDrop'] and
                any(s.startswith('no-new-privileges') for s in host['SecurityOpt']) and
                config['User']=='10001:10001' and metadata['Image']==image):
            raise RuntimeError('Container isolation mismatch; not starting')
        mounts={m['Destination']:m for m in metadata['Mounts']}
        if mounts['/inputs']['RW'] or not mounts['/outputs']['RW']:
            raise RuntimeError('Mount permission mismatch; not starting')
        (work/'container-inspect.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
        (work/'launch.json').write_text(json.dumps(description|dict(container_id=container_id,arguments=arguments),indent=2),encoding='utf-8')
        limit=plan['environment']['maximum_wall_seconds'] if args.mode=='execute' else 60
        code,elapsed=attach_with_deadline(container_id,work,limit)
        state=json.loads(subprocess.run(['docker','inspect',container_id],capture_output=True,text=True,timeout=30,check=True).stdout)[0]['State']
        (work/'completion.json').write_text(json.dumps(dict(exit_code=code,state=state,elapsed_seconds=elapsed),indent=2),encoding='utf-8')
        if code or state['Running'] or state['ExitCode'] or state['OOMKilled']:
            raise RuntimeError('Container did not finish successfully; see retained logs')
        print(json.dumps(dict(status='probe-passed' if args.mode=='probe' else 'execution-finished',run=str(work),target_wasm_executed=args.mode=='execute')))
    except Exception as error:
        (work/'failure.json').write_text(json.dumps(dict(error=str(error),mode=args.mode,
            container_id=container_id,plan_sha256=plan_sha),indent=2),encoding='utf-8')
        raise
    finally:
        if container_id:
            remove_owned_container(container_id)


if __name__=='__main__':
    main()
