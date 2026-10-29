"""Freeze measured-input controlled comparisons after pilot/mode validation."""
import hashlib
import json
import random
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/followup-evaluation-20261016'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    destination=OUT/'confirmatory-plans.json'
    if destination.exists():raise RuntimeError('Preserve frozen plans')
    pilot=OUT/'runs/runtime-bd69ee8d729c4792823d9f3860c5c0c6/pilot-audit.json'
    audit=json.loads(pilot.read_text(encoding='utf-8'))
    assert audit['status']=='measurement-checks-passed-with-compiler-mode-deviation'
    controlled=OUT/'runs/input-diagnostic-7d69953eb3d44538929da22fe95b4b63/controlled-audit.json'
    paths=OUT/'runs/input-diagnostic-bcebbc1a56fe4253b48b3b95e2911d9e/paths-audit.json'
    assert json.loads(controlled.read_text())['status']=='passed'
    assert json.loads(paths.read_text())['status']=='passed'
    probe=OUT/'runs/runtime-7b50bc8894dd410dbbf65067d2f3c21f'
    probe_plan=probe/'inputs/plan.json';probe_raw=probe/'outputs/runtime.json'
    data=json.loads(probe_raw.read_text());completion=json.loads((probe/'completion.json').read_text())
    assert data['status']=='complete' and completion['exit_code']==0 and not completion['state']['OOMKilled']
    assert data['plan_sha256']==sha(probe_plan) and len(data['samples'])==2
    for sample in data['samples']:
        trace=probe/'outputs'/(str(sample['sequence']).zfill(3)+'-stdout.txt')
        assert set(re.findall(r'using (Liftoff|TurboFan),',trace.read_text()))=={'Liftoff'}
        assert '--liftoff-only' in sample['flags'] and sample['final_output']==sample['final_expected']
    probe_audit=dict(status='passed',plan_sha256=sha(probe_plan),measurement_sha256=sha(probe_raw),
        samples=2,observed_compilers=['Liftoff'],scope='Corrected compiler setting validation only; not a speed comparison.')
    (OUT/'compiler-probe-audit.json').write_text(json.dumps(probe_audit,indent=2)+'\n',encoding='utf-8')
    # Keep the original pilot runner frozen; derive an explicit version for new families/phase logging.
    source=ROOT/'experiments/runtime-reference/followup-runtime.cjs'
    text=source.read_text(encoding='utf-8')
    old="host=require('/inputs/host-original.cjs').load(wasm);hash=v=>host.hash(v);output=()=>host.output();close=()=>host.close();nonce=()=>true;"
    new="host=require('/inputs/host-diagnostic.cjs').load(wasm);let last;hash=v=>{last=Buffer.from(v.hex,'hex');if(last.length!==76)throw Error('SWAMPED fixed input contract');host.hash(v);};output=()=>host.output();close=()=>host.close();nonce=()=>Buffer.from(host.diagnostic.memory.buffer,host.diagnostic.input+39,4).equals(last.subarray(39,43));"
    assert text.count(old)==1;text=text.replace(old,new)
    anchor="  }else{\n    host=await"
    replacement="""  }else if(artifact.family==='webminerpoolhashcn'){
    host=await require('/inputs/glue-loader.cjs').load(read('/inputs/'+artifact.glue).toString('utf8'),wasm);
    const m=host.Module;let actual;
    hash=v=>{const q=m.ccall('hash_cn','number',['string','number','number','number'],[v.hex,0,0,0]);actual=Buffer.from(m.HEAPU8.buffer,q,64).toString('ascii');};
    output=()=>actual;nonce=()=>true;close=()=>{};
  }else{
    host=await"""
    assert text.count(anchor)==1;text=text.replace(anchor,replacement)
    text=text.replace("const before=check();let n=0,t=performance.now();",
        "const before=check();console.log('FOLLOWUP_PHASE warmup-start '+new Date().toISOString());let n=0,t=performance.now();")
    text=text.replace("n=0;t=performance.now();const bins=[];",
        "console.log('FOLLOWUP_PHASE timed-start '+new Date().toISOString());n=0;t=performance.now();const bins=[];")
    text=text.replace("const after=check();",
        "console.log('FOLLOWUP_PHASE timed-end '+new Date().toISOString());const after=check();")
    text=text.replace("family:artifact.family,\n      flags:","family:artifact.family,nonce_check_kind:artifact.family==='webminerpoolhashcn'?'not-applicable-string-API':'input-memory-bytes',\n      flags:")
    text=text.replace("scope:'Pilot of fresh-process, bracketed throughput and explicit compiler modes; not a powered equivalence study.'",
        "scope:'Preplanned controlled comparisons: 30-second blocks, six repetitions across three sessions. Finite implementation-conditional effects, not population or equivalence claims.'")
    runner=ROOT/'experiments/runtime-reference/followup-confirmatory.cjs';runner.write_text(text,encoding='utf-8')
    plan=json.loads((OUT/'controlled-check-plan.json').read_text(encoding='utf-8'))
    plan['assets'].append(dict(name='confirmatory.cjs',path=str(runner.relative_to(ROOT)).replace('\\','/'),sha256=sha(runner)))
    def asset(name,relative):
        path=ROOT/relative;row=dict(name=name,path=str(relative).replace('\\','/'),sha256=sha(path));plan['assets'].append(row);return row
    artifacts=[];groups=[]
    for family in ['swamped','xmr-wasm','webminerpoolhashcn']:
        members=[a for a in plan['controlled']['artifacts'] if a['family']==family]
        artifacts.extend(members);groups.append(dict(id=family+'-controlled',family=family,baseline=members[0]['id'],variants=[a['id'] for a in members[1:]]))
    spec=json.loads((ROOT/'results/runtime-mining/cross-dataset/proof-of-theft/glue-control-input.json').read_text())
    flat=next(m for m in spec['modules'] if m['method']=='xmr-wasm-emccobf-flattening')
    a=asset('published-flat.wasm',flat['object']);asset('published-flat.js',flat['glue'])
    artifacts.append(dict(id='published-flat',family='xmr-wasm',file=a['name'],glue='published-flat.js',sha256=a['sha256']))
    ablations=json.loads((OUT/'path-plan.json').read_text(encoding='utf-8'))['path_diagnostic']['ablations']
    for row in ablations:
        a=asset(row['id']+'.wasm',Path('results/followup-evaluation-20261016/path-artifacts')/(row['id']+'.wasm'))
        assert a['sha256']==row['sha256']
        artifacts.append(dict(id=row['id'],family='xmr-wasm',file=a['name'],glue='published-flat.js',sha256=a['sha256']))
    groups.append(dict(id='xmr-helper-ablation',family='xmr-wasm',baseline='published-flat',variants=[a['id'] for a in ablations]))
    modes=[dict(id='liftoff',flags=['--liftoff-only','--no-wasm-tier-up','--no-wasm-dynamic-tiering','--no-wasm-lazy-compilation']),
        dict(id='turbofan',flags=['--no-liftoff','--no-wasm-tier-up','--no-wasm-dynamic-tiering','--no-wasm-lazy-compilation'])]
    plans=[]
    for session in range(3):
        current=json.loads(json.dumps(plan));schedule=[]
        for repetition in range(session*2,session*2+2):
            mode_order=modes[repetition%2:]+modes[:repetition%2]
            group_order=groups[repetition%len(groups):]+groups[:repetition%len(groups)]
            for mode in mode_order:
                for group in group_order:
                    variants=group['variants'][repetition%len(group['variants']):]+group['variants'][:repetition%len(group['variants'])]
                    rows=[(group['baseline'],'reference')]
                    if repetition==0:rows.append((group['baseline'],'AA-second'))
                    for variant in variants:rows.extend([(variant,'variant'),(group['baseline'],'bracket-reference')])
                    for identifier,role in rows:
                        schedule.append(dict(sequence=len(schedule),session=session+1,repetition=repetition+1,
                            mode=mode['id'],family=group['family'],group=group['id'],artifact_id=identifier,role=role))
        current['runtime']=dict(stage='controlled-confirmatory',artifacts=artifacts,groups=groups,modes=modes,
            schedule=schedule,warmup_seconds=5,block_seconds=30,repetitions=6,session=session+1,
            inference='Describe finite conditional effects with individual bracket ratios and interval estimates. Six repetitions do not by themselves prove practical equivalence or generalization.',
            selection_reason='Pilot A/A varied approximately -10% to +12.5%; use longer blocks, additional repetitions, alternating compiler modes and near references. No posthoc exclusions.',
            compiler_probe_audit_sha256=sha(OUT/'compiler-probe-audit.json'),pilot_audit_sha256=sha(pilot),
            controlled_correctness_audit_sha256=sha(controlled),path_correctness_audit_sha256=sha(paths),
            runner_derivation=dict(pilot_source_sha256=sha(source),new_source_sha256=sha(runner),
                changes=['Add webminerpool string API','Expose unchanged SWAMPED input memory for nonce checks','Log warmup/timed phase boundaries','Preserve pilot runner and raw measurements']))
        current['maximum_wall_seconds']=7200
        target=OUT/f'confirmatory-session-{session+1}-plan.json'
        assert not target.exists();target.write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        plans.append(dict(path=str(target.relative_to(ROOT)).replace('\\','/'),sha256=sha(target),blocks=len(schedule),nominal_seconds=35*len(schedule)))
    destination.write_text(json.dumps(dict(plans=plans,artifacts=len(artifacts),modes=modes,
        total_blocks=sum(p['blocks'] for p in plans),frozen_before_execution=True),indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(plans=plans,total_blocks=sum(p['blocks'] for p in plans)),indent=2))


if __name__=='__main__':main()
