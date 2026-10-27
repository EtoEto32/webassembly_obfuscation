"""Build and validate clones learned through public exports only."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import prototype as p
from run import save,command,HERE


def cumulative(groups):
    image={};result=[]
    for g in groups:
        image.update(g['image']);result.append((g['right'],sorted(image.items())))
    return result


def main():
    ap=argparse.ArgumentParser();ap.add_argument('main',type=Path);ap.add_argument('output',type=Path);args=ap.parse_args()
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=False);original=json.loads((args.main/'manifest.json').read_text());manifest=dict(models=original['models'],files=[]);records=[]
    for item in original['files']:
        if item['recovered']:continue
        report=json.loads(command(['node',HERE/'io-attack.cjs',args.main/item['path']]));previous={};groups=[]
        for frame in report['frames']:
            image={int(k):tuple(v) for k,v in frame['image'].items()}
            delta={k:v for k,v in image.items() if previous.get(k)!=v}
            groups.append(dict(right=frame['right'],image=delta));previous=image
        # Scoring only: static extraction is not passed to the oracle learner.
        expected=p.extract(p.read(args.main/item['path']))
        assert cumulative(groups)==cumulative(expected)
        name=Path(item['path']).stem+'.io.wasm';p.compile_wat(p.module(report['params'],p.plan(groups,'coalesced')),out/name)
        manifest['files'].append(dict(item,path=name,recovered=True));records.append(dict(path=item['path'],**report))
    save(out/'manifest.json',manifest);save(out/'analysis.json',records)
    checks=json.loads(command(['node',HERE/'check.cjs',out]));save(out/'checks.json',checks)
    hashes={}
    for src in [HERE/'io-study.py',HERE/'io-attack.cjs',HERE/'check.cjs',HERE/'prototype.py',HERE/'run.py',Path(p.w.__file__)]:
        name=src.relative_to(p.w.ROOT).as_posix();hashes[name]=hashlib.sha256(src.read_bytes()).hexdigest();dst=out/'sources'/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
    save(out/'environment.json',dict(source_hashes=hashes,node=checks['node'],v8=checks['v8']))
    # The main reference tests use different labels and random values, including
    # 0xff, so the byte labels used during learning are not the check inputs.
    print(json.dumps(dict(clones=len(records),queries=sum(x['queries'] for x in records),calls=checks['calls'],mismatches=checks['mismatches'])))


if __name__=='__main__':main()
