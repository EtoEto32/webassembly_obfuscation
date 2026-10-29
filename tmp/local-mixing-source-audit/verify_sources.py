import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
tree = {x['path']: x for x in json.loads((root / 'tree.json').read_text(encoding='utf-8-sig'))['tree']}
files = {
    'docs/gadgetization.md': 'docs__gadgetization.md',
    'security_tests/gadgetization/nonlinear193.py': 'nonlinear193.py',
    'security_tests/gadgetization/nonlinear291.py': 'security_tests__gadgetization__nonlinear291.py',
    'tests/python/gadgetization/test_nonlinear_gadgets.py': 'tests__python__gadgetization__test_nonlinear_gadgets.py',
}
results = []
for source, local in files.items():
    data = (root / local).read_bytes()
    git_sha = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    assert git_sha == tree[source]['sha'], source
    results.append(dict(source=source, local=local, git_blob=git_sha, sha256=hashlib.sha256(data).hexdigest()))
(root / 'source-verification.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
print(f'{len(results)} files match pinned Git tree blobs')
