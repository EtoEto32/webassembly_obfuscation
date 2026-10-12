"""Read the published Proof-of-Theft archive; never execute its scripts."""
import collections
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/runtime-mining/cross-dataset/proof-of-theft'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    source_receipts, modules = [], []
    with zipfile.ZipFile(ROOT / 'data/archives/proof-of-theft.zip') as archive:
        names = archive.namelist()
        for name in names:
            if not name.startswith('supp-materials/artifact/samples/'):
                continue
            if name.endswith(('.og.wasm', '.ogdeopt.wasm', '.orig.wasm', '.wasm')):
                if not any(k in name for k in ('webminerpoolhashcn', 'cryptonight-hash',
                        'miner_bitcoin', 'miner_eth', 'miner_bitzeny', 'xmr-wasm')):
                    continue
                data = archive.read(name)
                sha = hashlib.sha256(data).hexdigest()
                cache = ROOT / 'data/analysis-v2' / (sha + '.json')
                meta = json.loads(cache.read_text(encoding='utf-8')) if cache.exists() else {}
                imports = meta.get('imports', [])
                hooked = any(i['module'] == '__wasabi_hooks' for i in imports)
                modules.append(dict(path=name, sha256=sha, bytes=len(data),
                    object='data/objects/' + sha + '.bin',
                    stored_object_present=(ROOT / 'data/objects' / (sha + '.bin')).exists(),
                    wasabi_imports=hooked, imports=imports, exports=meta.get('exports', []),
                    role='instrumented; excluded from uninstrumented performance comparison' if hooked
                        else 'no Wasabi hook imports; verify program and algorithm before measurement',
                    method_context='declared obfuscated directory' if '___obfuscated_miners/' in name else 'baseline directory',
                    runtime_status='not measured'))
            if ('webminerpoolhashcn' in name and name.endswith(('/main.c', '/obf.sh', '/cn.js', '/cryptonight.c', '/Makefile'))):
                data = archive.read(name)
                # Preserve exact source under its digest with path mapping.
                sha = hashlib.sha256(data).hexdigest()
                target = OUT / (sha + Path(name).suffix)
                target.write_bytes(data)
                source_receipts.append(dict(path=name, sha256=sha, bytes=len(data),
                    saved=str(target.relative_to(ROOT)), executed=False))
    report = dict(archive='data/archives/proof-of-theft.zip', modules=modules,
        source_receipts=source_receipts, scope='Six named miner families in ready-to-serve source tree',
        wasabi_instrumented=sum(r['wasabi_imports'] for r in modules),
        without_wasabi_hooks=sum(not r['wasabi_imports'] for r in modules),
        runtime_measurements=0,
        limitations=['No-hook imports alone do not prove an unobfuscated program.',
            'Source pairing, minified export mapping, time ABI and algorithm need verification.',
            'No dataset-wide mining correctness or novelty established by this audit.'])
    (OUT / 'runtime-roles.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('modules', 'source_receipts')}))


if __name__ == '__main__':
    main()
