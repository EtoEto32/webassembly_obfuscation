import argparse
import hashlib
import json
from pathlib import Path
import shutil
import transform as T


def record(directory):
    manifest=json.loads((directory/'manifest.json').read_text())
    for e in manifest['entries']:
        b=(directory/e['file']).read_bytes()
        assert len(b)==e['bytes'] and hashlib.sha256(b).hexdigest()==e['sha256']
    src=directory/'source-snapshot';src.mkdir(exist_ok=False)
    files=[p for p in Path(__file__).parent.iterdir() if p.is_file()]
    files += [T.ROOT/'research/observation-synthesis'/n for n in ['transform.py','core.py']]
    entries=[]
    for p in files:
        relative=p.relative_to(T.ROOT);out=src/relative
        out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,out)
        entries.append({'path':relative.as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    result={'sources':entries,'verified_main_binaries':len(manifest['entries']),
            'all_binary_hashes':{p.relative_to(directory).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in directory.rglob('*.wasm')},
            'tool_hashes':{n:hashlib.sha256((T.TOOLS/folder/'bin'/(n+'.exe')).read_bytes()).hexdigest()
                          for n,folder in [('wat2wasm','wabt-1.0.42'),('wasm2wat','wabt-1.0.42'),
                                           ('wasm-validate','wabt-1.0.42'),('wasm-interp','wabt-1.0.42'),
                                           ('wasm-opt','binaryen-version_133')]}}
    (src/'manifest.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps({'verified_main_binaries':len(manifest['entries']),'saved_sources':len(entries)}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directory',type=Path);record(p.parse_args().directory)
