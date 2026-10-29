"""Audit saved research evidence. Does not certify novelty or patentability."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'results/invention-20261019'
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);a=ap.parse_args()
    if a.output.exists():raise FileExistsError(a.output)
    main=BASE/'quotient-lift-v3';manifest=read(main/'manifest.json');checks=read(main/'correctness.json')
    assert len(manifest['files'])==112 and checks['binaries']==112 and checks['calls']==231280 and checks['traps']==30688 and checks['mismatches']==0
    replay=read(main/'replay.json');assert len(replay)==112 and all(replay.values())
    for f in manifest['files']:
        assert (main/f['path']).is_file()
        assert hashlib.sha256((main/f['path']).read_bytes()).digest()==hashlib.sha256((BASE/'quotient-lift-v2'/f['path']).read_bytes()).digest()
    env=read(main/'environment.json')
    for name,digest in env['source_sha256'].items():
        source=ROOT/name;assert hashlib.sha256(source.read_bytes()).hexdigest()==digest,name
        copy=main/'sources'/(source.parent.name+'_'+source.name);assert hashlib.sha256(copy.read_bytes()).hexdigest()==digest
    static=read(main/'static-analysis.json');assert len(static)==32 and all(r['equivalent'] for r in static)
    learned=read(main/'public-learning.json');assert len(learned)==40 and all(r['posthoc_manager_equivalence']['equivalent'] for r in learned)
    assert sum(r['queries'] for r in learned)==99300
    for model in manifest['models']:
        group=[r for r in learned if r['path'].startswith(model+'.')];assert len(group)==10
        assert len({r['transcript_sha256'] for r in group})==1
        assert all(len(r['learning_samples_ms'])==3 for r in group)
    negative=read(main/'rare-control.json');assert not negative['posthoc_manager_equivalence']['equivalent']
    assert negative['posthoc_manager_equivalence']['witness']=='0'*31+'1'
    adaptive=read(BASE/'quotient-adaptive-v1/checks.json');assert adaptive['conditions']==32 and adaptive['equivalent']==32
    assert all(r['posthoc_equivalence']['equivalent'] and r['same_as_existing_static_clone'] for r in adaptive['records'])
    assert max(r['physical_states_probed'] for r in adaptive['records'])==33
    assert not adaptive['rare_control']['posthoc_equivalence']['equivalent']
    assert hashlib.sha256((ROOT/'research/quotient-lift/adaptive.py').read_bytes()).hexdigest()==adaptive['source_sha256']
    interpreter=read(BASE/'quotient-interpreter-v1/checks.json');assert interpreter['calls']==672 and interpreter['memory_probes']==2688 and interpreter['mismatches']==0
    assert hashlib.sha256((ROOT/'research/quotient-lift/interpreter.py').read_bytes()).hexdigest()==interpreter['script_sha256']
    controls=read(BASE/'quotient-controls-v1/checks.json');assert controls['model_conditions']==384 and controls['model_mismatches']==0 and len(controls['rejections'])==3
    bench=read(main/'benchmark.json');assert len(bench)==120
    assert all(r['warmup']==10000 and r['repetitions']==11 and r['calls_per_sample']==3000 for r in bench)
    links=0
    for path in (ROOT/'research/quotient-lift').glob('*.md'):
        prose=re.sub(r'```[\s\S]*?```','',path.read_text(encoding='utf-8'))
        prose=re.sub(r'`[^`]+`','',prose)
        for target in re.findall(r'\]\(([^\s)]+)\)',prose):
            if ':' in target or target.startswith('#'):continue
            assert (path.parent/target.split('#')[0]).exists(),(path,target);links+=1
    result=dict(status='passed',binaries=112,calls=231280,traps=30688,mismatches=0,static_models=32,adaptive_models=32,public_models=40,
                public_queries_per_repetition=99300,public_query_repetitions=3,interpreter_calls=672,memory_probes=2688,model_controls=384,rejected_controls=3,
                benchmark_processes=120,source_hashes=len(env['source_sha256']),local_markdown_links=links,replay_byte_matches=112,
                goal_complete=False,novel_invention_established=False)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
    print(json.dumps(result))

if __name__=='__main__':main()
