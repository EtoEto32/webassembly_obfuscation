"""Read-only assertions of completed evidence; writes a fresh audit JSON."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from run import save


def main():
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);a=ap.parse_args()
    root=Path(__file__).resolve().parents[2];results=root/'results/invention-20261018';main=results/'overlap-wasm-v3';replay=results/'overlap-wasm-replay-v4'
    load=lambda x:json.loads(x.read_text(encoding='utf-8'))
    files=load(main/'manifest.json')['files'];assert len(files)==72
    checks=load(main/'checks.json');assert checks['mismatches']==0 and checks['calls']==148680
    assert load(main/'interpreter.json')['calls']==288
    assert load(replay/'checks.json')['mismatches']==0 and load(replay/'replay.json')['identical']==72
    assert all((main/f['path']).read_bytes()==(replay/f['path']).read_bytes() for f in files)
    analysis=load(main/'analysis.json');assert len(analysis)==36 and all(x['status']=='success' for x in analysis)
    assert all(z['equivalent'] and z['status']=='success' for x in analysis for z in x['attacks'])
    assert len(load(main/'benchmark.json'))==108
    assert all(x['public_memory_bytes']==65536 for x in load(main/'summary.json'))
    assert len(load(main/'negatives.json'))==3 and load(main/'unsafe-merge.json')['got']==[0,1]
    study=load(results/'overlap-study-v1/results.json');assert len(study)==70
    assert all(z['equivalent'] and z['status']=='success' for x in study for z in x['attacks'])
    assert len(load(results/'overlap-study-v1/simulation-checks.json'))==120
    edges=load(results/'overlap-edge-v1/checks.json');assert edges['binaries']==6 and edges['mismatches']==0
    hashes=load(main/'environment.json')['source_hashes']
    for name,digest in hashes.items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
    links=[]
    for file in Path(__file__).parent.glob('*.md'):
        for link in re.findall(r'\]\(([^)]+)\)',file.read_text(encoding='utf-8')):
            if link.startswith(('http:','https:','#')):continue
            target=(file.parent/link.split('#')[0]).resolve();assert target.exists(),(file,link)
            links.append(dict(source=str(file.relative_to(root)),target=link))
    save(a.output,dict(passed=True,main_binaries=72,node_calls=checks['calls'],wabt_calls=288,recovered=36,
                       model_conditions=70,model_attacks=280,edge_calls=edges['calls'],binary_replay_identical=72,
                       source_hashes=hashes,checked_links=links))
    print(json.dumps(dict(passed=True,output=str(a.output))))


if __name__=='__main__':main()
