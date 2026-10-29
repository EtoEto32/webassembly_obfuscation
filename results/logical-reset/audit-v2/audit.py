"""Audit preserved evidence, local document links and deterministic rebuilds."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RESULTS = ROOT/'results/logical-reset'


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main(out):
    out = out.resolve()
    if out.exists(): raise FileExistsError(out)
    counts = {'manifests':0, 'hashEntries':0, 'documentLinks':0}
    for manifest in RESULTS.rglob('sha256.json'):
        entries = json.loads(manifest.read_text(encoding='utf8'))
        for name, expected in entries.items():
            path = (manifest.parent/name).resolve()
            path.relative_to(manifest.parent.resolve())
            assert path.is_file() and digest(path)==expected, str(path)
            counts['hashEntries'] += 1
        counts['manifests'] += 1
    for doc in HERE.glob('*.md'):
        for link in re.findall(r'\]\(([^)]+)\)', doc.read_text(encoding='utf8')):
            if '://' in link or link.startswith('#'): continue
            path = (doc.parent/link.split('#')[0]).resolve()
            assert path.exists(), (str(doc),link)
            counts['documentLinks'] += 1
    comparisons = []
    for original, rebuilt in [('probe-v3','reproduction-v1/probe'), ('bench-inputs-v1','reproduction-v1/bench-inputs')]:
        files = sorted((RESULTS/original).glob('*.wasm'))
        for file in files:
            target = RESULTS/rebuilt/file.name
            assert target.is_file() and file.read_bytes()==target.read_bytes(), str(file)
            comparisons.append({'original':file.relative_to(ROOT).as_posix(),
                                'rebuilt':target.relative_to(ROOT).as_posix(), 'sha256':digest(file)})
    a = json.loads((RESULTS/'probe-v3/results.json').read_text())
    b = json.loads((RESULTS/'reproduction-v1/probe/results.json').read_text())
    assert a == b
    full = sum(r.get('counts',{}).get('full',0) for r in a['rows'])
    assert full == 25704
    cross = json.loads((RESULTS/'reproduction-v1/cross/results.json').read_text())
    assert cross['calls'] == 8148
    user_files = {name:digest(ROOT/name) for name in ('paper/main.tex','paper/README.md')}
    source_hashes = {p.relative_to(ROOT).as_posix():digest(p) for p in HERE.iterdir() if p.is_file()}
    result = {'counts':counts, 'byteIdenticalBinaries':len(comparisons), 'comparisons':comparisons,
              'nodeFullComparisons':full, 'wasmtimeComparisons':cross['calls'],
              'sourceHashes':source_hashes, 'unrelatedPaperHashes':user_files,
              'note':'Repeated fixtures are reproducibility checks, not independent application evidence.'}
    out.mkdir(parents=True); shutil.copy2(__file__,out/'audit.py')
    (out/'results.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    (out/'sha256.json').write_text(json.dumps({p.name:digest(p) for p in out.iterdir() if p.is_file()},indent=2),encoding='utf8')
    print(json.dumps({**counts,'byteIdenticalBinaries':len(comparisons),'nodeFullComparisons':full,'wasmtimeComparisons':cross['calls']}))


if __name__ == '__main__':
    a=argparse.ArgumentParser();a.add_argument('out',type=Path);main(a.parse_args().out)
