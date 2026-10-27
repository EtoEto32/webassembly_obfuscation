"""Verify saved primary source blobs and record the existing optimization baseline."""
import hashlib
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/followup-evaluation-20261016/prior-method-audit.json'


def main():
    if OUT.exists():
        raise RuntimeError('Preserve earlier source audit')
    tree_path=ROOT/'data/upstream/tree.json'
    tree=json.loads(tree_path.read_text(encoding='utf-8'))
    rows=[]
    for relative in ['optimization/opt/main.py','optimization/opt/Dockerfile','README.md']:
        item=next(row for row in tree['tree'] if row['path']==relative)
        path=ROOT/'data/upstream/source'/relative;raw=path.read_bytes()
        blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        assert blob==item['sha']
        rows.append(dict(path=str(path.relative_to(ROOT)).replace('\\','/'),bytes=len(raw),git_blob_sha1=blob,
            sha256=hashlib.sha256(raw).hexdigest(),source_url='https://github.com/HakonHarnes/wasm-obf/blob/'+tree['sha']+'/'+relative))
    optimization=(ROOT/'data/upstream/source/optimization/opt/main.py').read_text()
    dockerfile=(ROOT/'data/upstream/source/optimization/opt/Dockerfile').read_text()
    command=re.search(r"f'wasm-opt .*?'",optimization)[0]
    assert '-O3' in command
    binaryen_commit=re.search(r'git checkout ([a-f0-9]{40})',dockerfile)[1]
    result=dict(status='saved-primary-blobs-match',source_revision=tree['sha'],files=rows,
        tree_receipt_sha256=hashlib.sha256(tree_path.read_bytes()).hexdigest(),
        prior_optimization_command=command,binaryen_commit_in_saved_dockerfile=binaryen_commit,
        source_executed=False,
        implication='Include an O3 baseline in the normalization comparison. Binaryen133 O3 is a current fixed comparator, not an exact reproduction of this historical compiler commit.',
        limitations=['Source shows configured optimization, not a proof that every released binary was built by that command.',
            'Thesis deobfuscation chapter has not been fully inspected in this follow-up.'])
    OUT.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
