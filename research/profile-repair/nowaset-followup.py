"""Resolve only the two rejected records; preserve the original scan unchanged."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('scan',HERE/'nowaset-scan.py');scan=importlib.util.module_from_spec(spec);spec.loader.exec_module(scan)

def main(source,inventory,previous,out):
    out.mkdir(parents=True,exist_ok=False);shutil.copy2(__file__,out/'nowaset-followup.py')
    prior=json.loads((previous/'results.json').read_text(encoding='utf8'));commit=json.loads((inventory/'commit.json').read_text(encoding='utf8'));tree=json.loads((inventory/'tree.json').read_text(encoding='utf8'))
    provenance=json.loads((source/'provenance.json').read_text(encoding='utf8'));hashes={r['file']:r['sha256'] for r in provenance['files']};rows=[]
    for row in prior['rows']:
        if row['status']!='validation_rejected':continue
        file=source/row['file'];data=file.read_bytes();assert hashlib.sha256(data).hexdigest()==hashes[file.name]
        cmd=[str(scan.WABT/'wasm-validate.exe'),'--enable-all','--ignore-custom-section-errors',str(file)]
        check=subprocess.run(cmd,capture_output=True,text=True,timeout=30)
        current={'file':file.name,'command':cmd,'returncode':check.returncode,'stderr':check.stderr,'bytes':len(data),'sha256':hashes[file.name]}
        if check.returncode:current['status']='empty_file' if not data else 'validation_rejected'
        else:
            current.update(status='ok_ignoring_custom_errors',prefixCandidates=scan.candidates(data),relaxedInstructions={})
            if current['prefixCandidates']:current['disassembly']=scan.disassemble(file)
        rows.append(current)
    result={'rows':rows,'originalScanSHA256':hashlib.sha256((previous/'results.json').read_bytes()).hexdigest(),
        'commit':commit['sha'],'actualCommitTree':commit['commit']['tree']['sha'],'treeApiResponseIdentifier':tree['sha'],
        'correction':'inventory-v1 results.tree was copied from the tree API response identifier. The actual commit tree is commit.commit.tree.sha; fixed here without editing the frozen original report.',
        'note':'Ignoring custom metadata errors is a follow-up core validation result, not a claim that custom metadata was understood.'}
    (out/'results.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    (out/'sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir() if f.name!='sha256.json'},indent=2),encoding='utf8')
    print(json.dumps(result))

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    for name in ('source','inventory','previous','output'):ap.add_argument(name,type=Path)
    a=ap.parse_args();main(a.source.resolve(),a.inventory.resolve(),a.previous.resolve(),a.output.resolve())
