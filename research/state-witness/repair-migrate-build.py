"""Visibility and documentation-lint build repair; no function body changes."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
a=argparse.ArgumentParser();a.add_argument('--root',type=Path,default=ROOT/'.tools/wasm-migrate-build')
base=a.parse_args().root
path=base/'crates/wasm-mutate/src/lib.rs';raw=path.read_bytes()
expected=next(x['sha256'] for x in json.loads((base/'provenance.json').read_text())['rows'] if x['path']=='crates/wasm-mutate/src/lib.rs')
assert hashlib.sha256(raw).hexdigest()==expected
old=b'\nmod module;';new=b'\n#[allow(missing_docs)]\npub mod module;';assert raw.count(old)==1
changed=raw.replace(old,new);path.write_bytes(changed)
(base/'build-repair.json').write_text(json.dumps({'file':'crates/wasm-mutate/src/lib.rs','before':expected,
 'after':hashlib.sha256(changed).hexdigest(),'change':'Expose module and allow missing_docs on that helper module.',
 'reason':'wasm-migrate imports map_type from this private module. No algorithm/body changes.'},indent=2))
print('Recorded visibility/documentation-only repair')
