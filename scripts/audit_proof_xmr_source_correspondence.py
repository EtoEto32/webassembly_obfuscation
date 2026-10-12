"""Compare distributed source trees without building or executing mining code."""
import hashlib
import json
import zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/runtime-mining/cross-dataset/proof-of-theft'
spec=json.loads((OUT/'glue-control-input.json').read_text())
rows=[]
with zipfile.ZipFile(ROOT/'data/archives/proof-of-theft.zip') as z:
    for item in spec['modules']:
        if item['family']!='xmr-wasm':continue
        prefix=item['path'].rsplit('/',1)[0]+'/'
        files={}
        for name in z.namelist():
            if name.startswith(prefix) and name.endswith(('.c','.cpp','.h')):
                data=z.read(name);files[name[len(prefix):]]=hashlib.sha256(data).hexdigest()
        build=z.read(prefix+'Makefile').decode(errors='replace')
        rows.append(dict(name=item['method'],module_sha256=item['sha256'],source_prefix=prefix,
                         source_files=files,source_file_count=len(files),build_text=build))
    base=next(r for r in rows if r['name']=='xmr-wasm')
    for r in rows:
        r['added_source_paths']=sorted(set(r['source_files'])-set(base['source_files']))
        r['missing_source_paths']=sorted(set(base['source_files'])-set(r['source_files']))
        r['changed_source_paths']=[p for p in r['source_files'] if p in base['source_files'] and r['source_files'][p]!=base['source_files'][p]]
        r['source_tree_identical_to_reference']=r['source_files']==base['source_files']
    for name in ['main.cpp','crypto/slow-hash.c']:
        (OUT/('xmr-source-'+name.rsplit('/',1)[-1]+'.txt')).write_bytes(z.read(base['source_prefix']+name))
report=dict(modules=rows,scope='Distributed C/C++/header files below the wasm directory, excluding generated JS/binaries and Makefile',
            limitation='Identical distributed sources do not prove the historical compiler, library objects, or commands that generated each binary. No new compilation or hash execution was performed.')
(OUT/'xmr-source-correspondence.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps([dict(name=r['name'],files=r['source_file_count'],identical=r['source_tree_identical_to_reference'],
                      changed=r['changed_source_paths']) for r in rows],indent=2))
