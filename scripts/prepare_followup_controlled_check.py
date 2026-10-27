"""Freeze correctness checks for controlled transforms, before normalization."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/followup-evaluation-20261016'


def main():
    destination=OUT/'controlled-check-plan.json'
    if destination.exists():
        raise RuntimeError('Preserve existing frozen plan')
    plan=json.loads((OUT/'plan.json').read_text(encoding='utf-8'))
    generation=json.loads((OUT/'controlled-generation-v2.json').read_text(encoding='utf-8'))
    cases=[]
    for row in generation['cases']:
        path=ROOT/row['path'];digest=hashlib.sha256(path.read_bytes()).hexdigest();assert digest==row['sha256']
        name=row['id']+'.wasm';plan['assets'].append(dict(name=name,path=row['path'],sha256=digest))
        cases.append(dict(id=row['id'],family=row['family'],file=name,sha256=digest,
            glue=row['family']+'.js' if row['family']!='swamped' else None))
    runner='experiments/runtime-reference/followup-controlled-check.cjs'
    plan['assets'].append(dict(name='controlled.cjs',path=runner,sha256=hashlib.sha256((ROOT/runner).read_bytes()).hexdigest()))
    additional=[]
    for i,nonce in enumerate([0,1,2,255,256,0x1020304,0x7fffffff,0xffffffff]):
        data=bytearray.fromhex(plan['public_vectors'][0]['hex']);assert len(data)==76 and data[0]<7
        data[39:43]=nonce.to_bytes(4,'little')
        additional.append(dict(id='controlled-nonce-'+str(i),hex=data.hex(),nonce=nonce))
    plan['controlled']=dict(artifacts=cases,additional_vectors=additional,
        generation_manifest_sha256=hashlib.sha256((OUT/'controlled-generation-v2.json').read_bytes()).hexdigest(),
        modes=['fresh-each','forward','reverse'],normalization_applied=False,
        contract='Exactly 76 bytes, cn/0; xmr public vectors limited to leading byte below 7.',
        reference='Published vectors plus a separately distributed original webminerpoolhashcn implementation for nonce changes.')
    plan['maximum_wall_seconds']=600
    destination.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(plan=str(destination),artifacts=len(cases),additional_vectors=len(additional))))


if __name__=='__main__':
    main()
