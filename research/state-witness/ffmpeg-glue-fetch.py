"""Fetch the exact npm package already used for the corpus; extract selected text only."""
import argparse
import base64
import hashlib
import io
import json
from pathlib import Path
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parents[2]

def main(out):
    source = ROOT / '.tools/state-witness-ffmpeg-0.12.10-v1/provenance.json'
    row = next(r for r in json.loads(source.read_text())['rows'] if r['package'] == '@ffmpeg/core-mt')
    out.mkdir(parents=True, exist_ok=False)
    with urllib.request.urlopen(row['tarballURL'], timeout=90) as response:
        raw = response.read()
    actual = 'sha512-' + base64.b64encode(hashlib.sha512(raw).digest()).decode()
    assert actual == row['integrity'], (actual, row['integrity'])
    selected = ['package/dist/umd/ffmpeg-core.js', 'package/dist/umd/ffmpeg-core.worker.js',
                'package/package.json']
    files = []
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:gz') as archive:
        for member in selected:
            data = archive.extractfile(member).read()
            dest = out / Path(member).name
            dest.write_bytes(data)
            files.append(dict(file=dest.name, member=member, bytes=len(data),
                              sha256=hashlib.sha256(data).hexdigest()))
    (out/'provenance.json').write_text(json.dumps(dict(package=row['package'], version=row['version'],
        url=row['tarballURL'], integrity=actual, tarballBytes=len(raw), files=files), indent=2))
    print(json.dumps(dict(files=files, verifiedIntegrity=True)))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('out', type=Path)
    main(parser.parse_args().out)
