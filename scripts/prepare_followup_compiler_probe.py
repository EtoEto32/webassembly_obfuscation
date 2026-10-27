"""Freeze a small actual-compiler check before scheduling new fixed-tier timings."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/followup-evaluation-20261016'


def main():
    destination=OUT/'compiler-probe-plan.json'
    if destination.exists():raise RuntimeError('Preserve previous probe plan')
    plan=json.loads((OUT/'runtime-pilot-plan.json').read_text(encoding='utf-8'))
    plan['runtime']['modes']=[dict(id='liftoff',flags=['--liftoff-only','--no-wasm-tier-up','--no-wasm-dynamic-tiering','--no-wasm-lazy-compilation'])]
    plan['runtime']['schedule']=[dict(sequence=i,repetition=1,mode='liftoff',family=family,
        artifact_id=identifier,role='compiler-probe') for i,(family,identifier) in enumerate([('swamped','roundtrip'),('xmr-wasm','xmr-wasm')])]
    plan['runtime'].update(stage='compiler-validation-only',warmup_seconds=1,block_seconds=2,repetitions=1,
        interpretation='Validate actual compiler output under explicit liftoff-only. Not a performance comparison.')
    plan['maximum_wall_seconds']=300
    destination.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(str(destination))


if __name__=='__main__':main()
