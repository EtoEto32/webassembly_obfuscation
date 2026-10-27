"""Freeze a bounded pilot before observing throughput under new conditions."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/followup-evaluation-20261016'


def main():
    destination=OUT/'runtime-pilot-plan.json'
    if destination.exists():
        raise RuntimeError('Do not replace a frozen plan')
    plan=json.loads((OUT/'plan.json').read_text(encoding='utf-8'))
    def asset(name,relative):
        path=ROOT/relative
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        plan['assets'].append(dict(name=name,path=relative,sha256=digest))
        return digest
    asset('runtime.cjs','experiments/runtime-reference/followup-runtime.cjs')
    spec=json.loads((ROOT/'results/runtime-mining/cross-dataset/proof-of-theft/glue-control-input.json').read_text(encoding='utf-8'))
    artifacts=[dict(id=c['id'],file=c['file'],sha256=c['sha256'],family='swamped') for c in plan['cases']]
    for method in ['xmr-wasm','xmr-wasm-emccobf-flattening','xmr-wasm-emccobf-substitution']:
        item=next(m for m in spec['modules'] if m['method']==method)
        # Existing xmr baseline assets were already frozen with the input diagnostic.
        if method=='xmr-wasm':
            wasm_name='xmr-wasm.wasm';glue_name='xmr-wasm.js'
        else:
            wasm_name=method+'.wasm';glue_name=method+'.js'
            assert asset(wasm_name,item['object'])==item['sha256']
            assert asset(glue_name,item['glue'])==item['glue_sha256']
        artifacts.append(dict(id=method,file=wasm_name,glue=glue_name,sha256=item['sha256'],family='xmr-wasm'))
    modes=[dict(id='default',flags=[]),
        dict(id='liftoff',flags=['--liftoff','--no-wasm-tier-up','--no-wasm-lazy-compilation']),
        dict(id='turbofan',flags=['--no-liftoff','--no-wasm-tier-up','--no-wasm-lazy-compilation'])]
    schedule=[]
    # Baseline twice supplies A/A; baseline-variant-baseline triples are adjacent.
    for repetition in range(2):
        order=modes[repetition:]+modes[:repetition]
        for mode in order:
            for family in (['swamped','xmr-wasm'] if repetition==0 else ['xmr-wasm','swamped']):
                group=[a for a in artifacts if a['family']==family];base=group[0]
                variants=group[1:] if repetition==0 else list(reversed(group[1:]))
                rows=[(base,'AA-first'),(base,'AA-second')]
                for variant in variants:
                    rows.extend([(variant,'variant'),(base,'bracket-reference')])
                for artifact,role in rows:
                    schedule.append(dict(sequence=len(schedule),repetition=repetition+1,mode=mode['id'],family=family,
                        artifact_id=artifact['id'],role=role))
    plan['maximum_wall_seconds']=3600
    plan['runtime']=dict(stage='pilot',artifacts=artifacts,modes=modes,schedule=schedule,
        warmup_seconds=5,block_seconds=10,repetitions=2,
        sample_unit='Fresh process per block; repeated baselines diagnose measurement variability, not independent implementations.',
        interpretation='Compiler-mode dependence and pilot variability only. Confirmatory design is to be frozen after the pilot, before its own outcomes.',
        change_from_prior='CPU guest affinity 0, fresh process, near references, cpu/cgroup timing, compilation logs; original Wasm/hosts and public vectors retained.')
    destination.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(plan=str(destination),blocks=len(schedule),nominal_seconds=len(schedule)*15)))


if __name__=='__main__':
    main()
