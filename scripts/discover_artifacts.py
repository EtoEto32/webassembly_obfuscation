"""Fetch primary-source metadata; preserve URLs, timestamps and checksums."""
import datetime
import hashlib
import json
import re
from pathlib import Path
from acquire import ROOT, get


def fetch(url, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        with get(url) as response:
            data = response.read()
        dest.write_bytes(data)
    else:
        data = dest.read_bytes()
    return {'url':url,'file':dest.relative_to(ROOT).as_posix(),
            'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}


def main():
    registry = json.loads((ROOT/'experiments/dataset-registry.json').read_text())
    out = ROOT/'data/catalog'
    log = []
    targets = []
    for d in registry['datasets']:
        if not d.get('github'):
            continue
        folder = out/d['id']
        tree = json.loads((folder/'tree.json').read_text())
        base = f'https://raw.githubusercontent.com/{d["github"]}/{tree["sha"]}/'
        for f in tree['tree']:
            p = f['path']
            if f['type'] == 'blob' and (p.lower() in ('license','license.md','license.txt','copying','.gitmodules')
               or (d['id']=='wasmbench' and p=='dataset-metadata/filtered.pretty.json')):
                targets.append((base+p, folder/p))
        targets.append((f'https://api.github.com/repos/{d["github"]}/releases',folder/'releases.json'))
    targets.append(('https://zenodo.org/api/records/17964973',out/'androwasm/record.json'))
    targets.append(('https://zenodo.org/api/records/18496931',out/'proof-of-theft/record.json'))
    targets.append(('https://drops.dagstuhl.de/entities/document/10.4230/DARTS.12.1.19',out/'proof-of-theft/landing.html'))
    targets.append(('https://arxiv.org/html/2503.21240v1',out/'industry2025/paper.html'))
    targets.append(('https://software-lab.org/publications/www2021.pdf',out/'wasmbench/paper.pdf'))
    targets.append(('https://yonghwi-kwon.github.io/data/wasm_perturbation_ase25.pdf',out/'swamped/paper.pdf'))
    targets.append(('https://arxiv.org/pdf/2308.03123',out/'wasmixer/paper.pdf'))
    targets.append(('https://arxiv.org/pdf/2403.15197',out/'wasm-obf/paper.pdf'))
    for url, dest in targets:
        try:
            item = fetch(url,dest); item['status'] = 'ok'
            print(item['file'],item['bytes'],flush=True)
        except Exception as exc:
            item = {'url':url,'file':dest.relative_to(ROOT).as_posix(),'status':'failed','error':str(exc)}
            print(item,flush=True)
        log.append(item)
    (ROOT/'results/catalog/artifact-discovery.json').write_text(json.dumps(log,indent=2),encoding='utf-8')


if __name__=='__main__':
    main()
