"""Read-only verification of local evidence; write a new checkpoint on success."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[2]
AREAS=('fuel-frontier','import-alias-quotient','fuel-observer','waiter-identity','profile-repair')


def main(dest):
    if dest.exists():raise ValueError('checkpoint already exists')
    source={};results=[];links=0;files=0
    for area in AREAS:
        for p in (ROOT/'research'/area).rglob('*'):
            if not p.is_file() or '__pycache__' in p.parts:continue
            source[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
            if p.suffix=='.md':
                for target in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf8')):
                    if '://' in target or target.startswith('#'):continue
                    target=target.split('#')[0]
                    if not (p.parent/target).exists():raise ValueError(str(p)+': missing '+target)
                    links+=1
        for p in (ROOT/'results'/area).glob('*/sha256.json'):
            hashes=json.loads(p.read_text(encoding='utf8'))
            for rel,h in hashes.items():
                actual=hashlib.sha256((p.parent/rel).read_bytes()).hexdigest()
                if actual!=h:raise ValueError('hash mismatch '+str(p.parent/rel))
                files+=1
            results.append({'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'files':len(hashes),'hasResults':(p.parent/'results.json').exists() or (p.parent/'report.json').exists()})
    inherited={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'paper/main.tex',ROOT/'paper/README.md')}
    report={'sources':source,'manifests':results,'verifiedFiles':files,'localLinks':links,'inheritedPaperHashes':inherited,'note':'Presence of a results file is not a claim of successful research. Failed/intermediate runs are retained. Usage threshold is not inferred from this audit.'}
    dest.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8')
    print(json.dumps({'sources':len(source),'manifests':len(results),'verifiedFiles':files,'localLinks':links,'inheritedPaperHashes':inherited}))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);main(ap.parse_args().output)
