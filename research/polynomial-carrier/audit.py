"""Assert the saved evidence and source hashes; never overwrite an audit."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from run import save


def main():
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);args=ap.parse_args()
    root=Path(__file__).resolve().parents[2];results=root/'results/invention-20261018'
    main=results/'carrier-wasm-v3';replay=results/'carrier-wasm-replay-v4'
    load=lambda p:json.loads(p.read_text(encoding='utf-8'))
    files=load(main/'manifest.json')['files'];assert len(files)==72
    sources={}
    for folder in (main,replay):
        checks=load(folder/'checks.json')
        assert checks['calls']==75024 and checks['traps']==19728 and checks['mismatches']==0
        interp=load(folder/'interpreter.json');assert interp['engine']=='WABT' and interp['calls']==288 and interp['mismatches']==0
        analysis=load(folder/'analysis.json');assert len(analysis)==36
        assert all(x['status']=='success' and x['exact_original_update'] for x in analysis)
        assert sum(x['method']=='linear_preimage' for x in analysis)==24
        assert sum(x['method']=='known_factor' for x in analysis)==12
        assert all(len(x['samples_ms'])==11 and len(x['trials'])==2 for x in analysis)
        assert all(x['status']=='rejected' for x in load(folder/'negatives.json'))
        assert len(load(folder/'benchmark.json'))==108
        assert all(x['public_memory_bytes']==65536 for x in load(folder/'summary.json'))
        for name,digest in load(folder/'environment.json')['source_hashes'].items():
            assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
            assert hashlib.sha256((folder/'sources'/name).read_bytes()).hexdigest()==digest,name
            sources[name]=digest
    assert load(replay/'replay.json')['identical']==72
    assert all((main/f['path']).read_bytes()==(replay/f['path']).read_bytes() for f in files)
    study=load(results/'carrier-study-v1.json');assert len(study['records'])==72
    assert all(any(t['status']=='success' for t in r['trials']) for r in study['records'])
    assert len(study['negative_controls'])==4
    links=[]
    for file in Path(__file__).parent.glob('*.md'):
        for link in re.findall(r'\]\(([^)]+)\)',file.read_text(encoding='utf-8')):
            if link.startswith(('http:','https:','#')):continue
            assert (file.parent/link.split('#')[0]).resolve().exists(),(str(file),link)
            links.append(dict(source=str(file.relative_to(root)),target=link))
    save(args.output,dict(passed=True,main_binaries=72,node_calls=75024,wabt_calls=288,recovered=36,
                         model_conditions=72,negative_controls=4,binary_replay_identical=72,source_hashes=sources,checked_links=links))
    print(json.dumps(dict(passed=True,output=str(args.output))))


if __name__=='__main__':main()
