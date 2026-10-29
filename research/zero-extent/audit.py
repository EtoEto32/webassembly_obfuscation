import argparse
import hashlib
import json
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[2]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);a=ap.parse_args();base=ROOT/'results/invention-20261019';run=base/'extent-wasm-replay-v4';old=base/'extent-wasm-v3'
    manifest=read(run/'manifest.json')['files'];checks=read(run/'checks.json');analysis=read(run/'analysis.json');env=read(run/'environment.json')
    assert len(manifest)==96 and len(analysis)==48 and all(x['status']=='success' for x in analysis)
    assert checks['calls']==239616 and checks['traps']==177785 and checks['mismatches']==0
    for item in manifest:
        assert (run/item['path']).read_bytes()==(old/item['path']).read_bytes()
    assert read(run/'replay.json')['identical']==96
    for name,digest in env['source_hashes'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
        assert hashlib.sha256((run/'sources'/name).read_bytes()).hexdigest()==digest,name
    other=read(base/'extent-interpreter-v1/checks.json');assert (other['writer_calls'],other['probe_calls'],other['mismatches'])==(384,7296,0)
    assert other['source_hashes']['interpreter.py']==hashlib.sha256((Path(__file__).with_name('interpreter.py')).read_bytes()).hexdigest()
    control=read(base/'extent-controls-v3/checks.json');assert len(control['negative_controls'])==4 and control['normalizer_cases']==21 and control['normalizer_mismatches']==0 and len(control['rejections'])==2
    assert len(read(run/'benchmark.json'))==432 and len(read(run/'summary.json'))==144
    broken=[];links=0
    for doc in Path(__file__).parent.glob('*.md'):
        for link in re.findall(r'\]\(([^)]+)\)',doc.read_text(encoding='utf-8')):
            if '://' in link or link.startswith('#'):continue
            links+=1
            if not (doc.parent/link.split('#')[0]).exists():broken.append((doc.name,link))
    assert not broken,broken
    result=dict(status='passed',binaries=96,calls=239616,traps=177785,mismatches=0,analysis_success=48,
                wasm_byte_replay=96,writer_calls=384,memory_probes=7296,negative_controls=4,normalizer_controls=21,
                benchmark_processes=432,source_hashes_checked=len(env['source_hashes']),relative_links_checked=links,
                main_result=str(run.relative_to(ROOT)),research_goal_complete=False)
    with a.output.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result))
if __name__=='__main__':main()
