"""Freeze follow-up experiments without executing Wasm or changing prior results."""
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/followup-evaluation-20261016'
IMAGE = 'sha256:a05286e66b0f1ca712671db5849229594c92e035bae253362cc8b6d0af4a70b6'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(exist_ok=True)
    source = ROOT / 'experiments/runtime-reference/swamped-host.cjs'
    original = source.read_text(encoding='utf-8')
    anchor = 'return {calls,layout:'
    assert original.count(anchor) == 1
    diagnostic = OUT / 'diagnostic-host.cjs'
    diagnostic.write_text(original.replace(anchor,
        'return {diagnostic:{memory,exports,ctx,input,output},calls,layout:'), encoding='utf-8')
    vector_source = ROOT / 'results/runtime-mining/cross-dataset/proof-of-theft/glue-control-input.json'
    spec = json.loads(vector_source.read_text(encoding='utf-8'))
    old_plan_path = ROOT / 'results/countermeasures/runtime-preparation/plan.json'
    old_plan = json.loads(old_plan_path.read_text(encoding='utf-8'))
    permission_path = ROOT / 'results/countermeasures/runtime-preparation/professor-permission.json'
    permission = json.loads(permission_path.read_text(encoding='utf-8'))
    assert permission['confirmed'] and permission['plan_sha256'] == sha(old_plan_path)
    assets = []
    def asset(name, relative):
        path = ROOT / relative
        assert path.resolve().is_relative_to(ROOT.resolve())
        row = dict(name=name, path=str(path.relative_to(ROOT)).replace('\\', '/'), sha256=sha(path))
        assets.append(row)
        return row
    asset('host-original.cjs', source.relative_to(ROOT))
    asset('host-diagnostic.cjs', diagnostic.relative_to(ROOT))
    asset('glue-loader.cjs', 'experiments/runtime-reference/proof-glue-controls.cjs')
    asset('input-diagnostic.cjs', 'experiments/runtime-reference/followup-input-diagnostic.cjs')
    asset('original-permission.json', permission_path.relative_to(ROOT))
    asset('original-plan.json', old_plan_path.relative_to(ROOT))
    cases = []
    for label in ['roundtrip', 'nop10', 'constsplit10']:
        entry = asset(label+'.wasm', f'results/runtime-mining/cross-dataset/swamped/046dc081-{label}.wasm')
        cases.append(dict(id=label, file=entry['name'], sha256=entry['sha256']))
    references = []
    for family in ['webminerpoolhashcn', 'xmr-wasm']:
        item = next(m for m in spec['modules'] if m['method'] == family)
        wasm = asset(family+'.wasm', item['object'])
        glue = asset(family+'.js', item['glue'])
        assert wasm['sha256'] == item['sha256'] and glue['sha256'] == item['glue_sha256']
        references.append(dict(family=family, wasm=wasm['name'], glue=glue['name']))
    wat_path = ROOT / 'results/runtime-mining/cross-dataset/swamped/046dc081-roundtrip.wat'
    lines = wat_path.read_text(encoding='utf-8').splitlines()
    start = next(i for i,line in enumerate(lines) if line.startswith('  (func $_cryptonight_hash_variant_0 '))
    end = next(i for i in range(start+1,len(lines)) if lines[i].startswith('  (func '))
    body = lines[start:end]
    (OUT / 'baseline-input-entry.wat.txt').write_text('\n'.join(body[:123])+'\n', encoding='utf-8')
    assert body[2:4] == ['    global.get $g4', '    local.set $p3']
    copy_end = body.index('    i32.load offset=72 align=1')
    offsets = [int(m[1] or 0) for line in body[:copy_end+1]
               if (m := re.fullmatch(r'    i64.load(?: offset=(\d+))? align=1',line))]
    assert offsets == list(range(0,72,8))
    contract = dict(wat_sha256=sha(wat_path), function_first_line=start+1,
                    fourth_argument_overwritten_before_use=True,
                    contiguous_input_loads_bytes=list(range(76)),
                    interpretation='Entry copies exactly 76 input bytes; incoming fourth parameter is discarded. Runtime probes still required.',
                    evidence_path='baseline-input-entry.wat.txt')
    (OUT / 'static-input-contract.json').write_text(json.dumps(contract,indent=2)+'\n', encoding='utf-8')
    plan = dict(created_utc=datetime.now(timezone.utc).isoformat(), image=IMAGE,
        intended_node='v18.20.4', intended_v8='10.2.154.26-node.37', assets=assets,
        cases=cases, references=references, public_vectors=spec['vectors'],
        additional_vectors=old_plan['additional_vectors'],
        authorization=dict(user_request='この方針でゴールモードを開始して。既存の研究成果を大事にしながら、難読化前後の性能評価を進めて、その結果を踏まえてコード正規化を検討してください。',
            inherited_professor_permission_sha256=sha(permission_path),
            scope='Local offline correctness, dynamic-path and throughput follow-up; no pools, shares, rewards or external communications. Original permission remains associated with its original plan.'),
        input_diagnostic=dict(case_ids=[c['id'] for c in cases],
            length_arguments=[0,1,8,32,75,76,77,128,255], short_lengths=[1,8,32],
            maximum_wall_seconds=300,
            expectations=['public vectors unchanged', 'full input ignores length argument',
                'short input output equals canonical effective 76-byte buffer',
                'tail outside first 76 bytes does not affect output',
                'canonical 76-byte input matches independently distributed reference implementations']),
        frozen_before_execution=True)
    path = OUT / 'plan.json'
    if path.exists():
        raise RuntimeError('Preserve existing frozen plan; use a new output directory for revisions')
    path.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(plan=str(path),sha256=sha(path),assets=len(assets),contract=contract),indent=2))


if __name__ == '__main__':
    main()
