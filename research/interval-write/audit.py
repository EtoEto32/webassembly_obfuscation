"""Integrity audit of saved evidence; no additional performance experiment."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent


def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('original',type=Path);ap.add_argument('current',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args()
    reports=[];hashes=[]
    for folder in [a.original,a.current]:
        manifest=read(folder/'manifest.json');files=manifest['files'];names={f['path'] for f in files}
        assert len(names)==len(files)==96
        assert len({(f['model'],f['mode'],f['opt']) for f in files})==48
        checks=read(folder/'checks.json');assert checks['files']==96 and checks['calls']==1975680
        assert checks['mismatches']==checks['memory_mismatches']==0
        assert {r['path'] for r in checks['rows']}==names
        assert sum(r['calls'] for r in checks['rows'])==checks['calls']
        assert all(r['mismatches']==r['memory_mismatches']==0 for r in checks['rows'])
        assert [r['mismatches'] for r in checks['negative_controls']]==[296,1]
        analysis=read(folder/'analysis.json')
        assert len(analysis)==48 and all(r['status']=='success' and r['boolean_identity'] and len(r['samples_ms'])==9 for r in analysis)
        interp=read(folder/'interpreter.json')
        assert interp['calls']==384 and interp['mismatches']==0
        assert len(interp['records'])==96 and all(r['got']==r['expected'] for r in interp['records'])
        timing=read(folder/'timings.json');assert timing['fresh_processes']==len(timing['records'])==144
        counts=Counter(r['path'] for r in timing['records'])
        assert set(counts)=={r['path'] for r in analysis} and set(counts.values())=={3}
        assert all(len(r['samples_ns'])==9 and r['warmup']==2000 and r['calls_per_repetition']==10000 and r['public_memory_bytes']==65536 for r in timing['records'])
        digest=read(folder/'binary-sha256.json');assert set(digest)==names
        assert all(sha(folder/n)==v for n,v in digest.items());hashes.append(digest)
        saved=read(folder/'audit.json')['source_sha256']
        assert all(sha(folder/'sources'/n)==v for n,v in saved.items())
        reports.append(dict(folder=str(folder),binaries=len(names),calls=checks['calls'],interpreter_calls=interp['calls'],recovered=len(analysis),fresh_processes=timing['fresh_processes']))
    assert hashes[0]==hashes[1]
    assert all(r['rejected'] for r in read(a.current/'negative-analysis.json'))
    assert len(read(a.current/'negative-analysis.json'))==5
    assert not (a.current/'must-not-exist.wasm').exists()
    for name,value in read(a.current/'audit.json')['source_sha256'].items():
        path=HERE.parent/'connectivity-elimination/prototype.py' if name=='common-prototype.py' else HERE/name
        assert sha(path)==value
    links=0
    for f in HERE.glob('*.md'):
        for target in re.findall(r'\]\(([^)]+)\)',f.read_text(encoding='utf-8')):
            if target.startswith(('https:', 'http:', '#')):continue
            assert (f.parent/target.split('#')[0]).exists(),(f,target)
            links+=1
    result=dict(experiments=reports,identical_binaries=96,negative_rejections=5,current_sources_match=True,
                local_links_checked=links,scope='Saved evidence integrity, not a novelty or universal equivalence proof.')
    with a.output.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(result))


if __name__=='__main__':main()
