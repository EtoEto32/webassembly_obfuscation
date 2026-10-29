"""Prepare unchanged Emscripten glue and public hashing test vectors."""
import hashlib
import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/runtime-mining/cross-dataset/proof-of-theft'
roles = json.loads((OUT / 'runtime-roles.json').read_text())
header = (OUT / 'xmrig-v6.18.0-CryptoNight_test.h').read_bytes()


def array(name):
    match = re.search(rb'uint8_t\s+' + name.encode() + rb'\[[^\]]*\]\s*=\s*\{([^}]+)\}', header)
    if not match:
        raise ValueError(name)
    return bytes(int(x, 16) for x in re.findall(rb'0x([0-9a-fA-F]{2})', match[1]))


inputs, expected = array('test_input'), array('test_output_v0')
assert len(inputs) == 380 and len(expected) >= 160
vectors = [dict(id=f'xmrig-cn0-{i}', hex=inputs[i*76:(i+1)*76].hex(),
                expected=expected[i*32:(i+1)*32].hex(), lite=0, variant=0, height=0)
           for i in range(5)]
report = dict(vectors=vectors, modules=[],
              reference_url='https://raw.githubusercontent.com/xmrig/xmrig/v6.18.0/src/crypto/cn/CryptoNight_test.h',
              reference_sha256=hashlib.sha256(header).hexdigest(),
              scope='Published uninstrumented originals and variants; original generated glue, no original HTML')
with zipfile.ZipFile(ROOT / 'data/archives/proof-of-theft.zip') as z:
    for row in roles['modules']:
        if row['wasabi_imports'] or not row['path'].endswith('.og.wasm'):
            continue
        family = next((f for f in ('webminerpoolhashcn', 'xmr-wasm', 'cryptonight-hash') if f in row['path']), None)
        if family is None:
            continue
        names = [e['name'] for e in row['exports']]
        glue_name = row['path'].replace('.og.wasm', '.js')
        if glue_name not in z.namelist():
            continue
        data = z.read(glue_name)
        sha = hashlib.sha256(data).hexdigest()
        target = OUT / 'original-glue' / (sha + '.js')
        target.parent.mkdir(exist_ok=True)
        target.write_bytes(data)
        entry = dict(family=family, method=row['path'].split('/')[4], path=row['path'],
                     sha256=row['sha256'], object=row['object'], exports=names,
                     glue=str(target.relative_to(ROOT)).replace('\\', '/'),
                     glue_source=glue_name, glue_sha256=sha)
        entry['method'] = row['path'].split('/')[-3] if family == 'xmr-wasm' else row['path'].split('/')[-2]
        if family == 'cryptonight-hash':
            entry['limitation'] = 'No cryptonight_hash export in published uninstrumented module; inspect original glue correspondence.'
        report['modules'].append(entry)
(OUT / 'glue-control-input.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'modules': len(report['modules']), 'public_vectors': len(vectors)}))
