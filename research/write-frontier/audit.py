"""Inspect the completed evidence and create a fresh audit record."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from run import save


def main():
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);args=ap.parse_args()
    root=Path(__file__).resolve().parents[2];results=root/'results/invention-20261018';main=results/'frontier-wasm-v3';replay=results/'frontier-wasm-replay-v4';io=results/'frontier-io-v2'
    load=lambda p:json.loads(p.read_text(encoding='utf-8'));hashes={}
    files=load(main/'manifest.json')['files'];assert len(files)==144
    for folder in (main,replay):
        checks=load(folder/'checks.json');assert checks['calls']==164196 and checks['traps']==70632 and checks['mismatches']==0
        analysis=load(folder/'analysis.json');assert len(analysis)==72 and all(x['status']=='success' for x in analysis)
        assert all(len(x['samples_ms'])==11 and len(x['bit_samples_ms'])==11 for x in analysis)
        interpreter=load(folder/'interpreter.json');assert interpreter['writer_calls']==288 and interpreter['memory_reads']==16128 and interpreter['mismatches']==0
        assert len(load(folder/'benchmark.json'))==216
        assert all(x['public_memory_bytes']==65536 for x in load(folder/'summary.json'))
        transforms=load(folder/'transforms.json')
        for model in ('increasing','descending','zigzag','overlap'):
            counts={x['mode']:x['output_stores'] for x in transforms if x['model']==model};assert counts['woven1']==counts['random1']
    assert load(replay/'replay.json')['identical']==144
    assert all((main/f['path']).read_bytes()==(replay/f['path']).read_bytes() for f in files)
    checks=load(io/'checks.json');assert checks['binaries']==72 and checks['calls']==82098 and checks['traps']==35316 and checks['mismatches']==0
    oracle=load(io/'analysis.json');assert len(oracle)==72 and sum(x['queries'] for x in oracle)==234
    assert all(x['queries']==len(x['frames'])+1 for x in oracle)
    for folder in (main,replay,io):
        for name,digest in load(folder/'environment.json')['source_hashes'].items():
            assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
            assert hashlib.sha256((folder/'sources'/name).read_bytes()).hexdigest()==digest,name
            hashes[name]=digest
    study=results/'frontier-study-v1';models=load(study/'model-checks.json')
    assert models['programs']==400 and models['comparisons']==132000 and models['mismatches']==0
    controls=load(study/'controls.json');assert len(controls)==2 and all(x['original_trap'] and x['wrong_trap'] and x['memory_differences'] for x in controls)
    rejects=load(study/'rejections.json');assert len(rejects)==3 and all(x['status']=='rejected' for x in rejects)
    assert len(load(study/'minimum-counts.json'))==12
    links=[]
    for file in Path(__file__).parent.glob('*.md'):
        for link in re.findall(r'\]\(([^)]+)\)',file.read_text(encoding='utf-8')):
            if link.startswith(('http:','https:','#')):continue
            assert (file.parent/link.split('#')[0]).resolve().exists(),(str(file),link)
            links.append(dict(source=str(file.relative_to(root)),target=link))
    save(args.output,dict(passed=True,main_binaries=144,main_calls=164196,static_recoveries=72,wabt_writer_calls=288,wabt_memory_reads=16128,
                         model_comparisons=132000,io_clones=72,io_queries=234,io_checks=82098,binary_replay_identical=144,source_hashes=hashes,checked_links=links))
    print(json.dumps(dict(passed=True,output=str(args.output))))


if __name__=='__main__':main()
