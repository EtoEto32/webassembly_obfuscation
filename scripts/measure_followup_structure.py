"""Use the existing WABT static analyzer on the same 13 frozen timed artifacts."""
import hashlib
import json
from pathlib import Path

from analyze_corpus import analyze

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/followup-evaluation-20261016'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    destination=OUT/'confirmatory-structure.json'
    if destination.exists():raise RuntimeError('Preserve measured structure')
    plan_path=OUT/'confirmatory-session-1-plan.json';plan=json.loads(plan_path.read_text(encoding='utf-8'))
    rows=[]
    for artifact in plan['runtime']['artifacts']:
        asset=next(a for a in plan['assets'] if a['name']==artifact['file']);path=ROOT/asset['path'];assert sha(path)==artifact['sha256']
        result=analyze(dict(object=asset['path'],sha256=artifact['sha256']))
        assert result['status']=='ok' and result['valid_wabt']
        rows.append(dict(id=artifact['id'],family=artifact['family'],path=asset['path'],sha256=artifact['sha256'],
            bytes=path.stat().st_size,instruction_count=result['instruction_count'],opcodes=result['opcodes'],
            sections=result['sections'],imports=result['imports'],exports=result['exports']))
    comparisons=[]
    for group in plan['runtime']['groups']:
        baseline=next(r for r in rows if r['id']==group['baseline'])
        for identifier in group['variants']:
            variant=next(r for r in rows if r['id']==identifier)
            comparisons.append(dict(group=group['id'],artifact_id=identifier,baseline_id=baseline['id'],
                instruction_ratio=variant['instruction_count']/baseline['instruction_count'],byte_ratio=variant['bytes']/baseline['bytes'],
                instruction_delta=variant['instruction_count']-baseline['instruction_count'],byte_delta=variant['bytes']-baseline['bytes']))
    result=dict(status='wabt-static-analysis-passed',plan_sha256=sha(plan_path),records=rows,comparisons=comparisons,
        existing_analyzer_sha256=sha(ROOT/'scripts/analyze_corpus.py'),script_sha256=sha(Path(__file__)),
        wasm_executed=False,interpretation='Static instructions are stored opcodes, not dynamic instruction counts.')
    destination.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=result['status'],artifacts=len(rows),comparisons=comparisons),indent=2))


if __name__=='__main__':main()
