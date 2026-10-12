"""Cache primary metadata for literature candidates; never run their code."""
import concurrent.futures
import datetime
import hashlib
import json
from acquire import ROOT, get
from catalog_datasets import audit


SOURCES = [
    ('wasmizer-zenodo', 'https://zenodo.org/api/records/7742004'),
    ('wasmizer-figshare', 'https://api.figshare.com/v2/articles/22264000'),
    ('jwbinder-releases', 'https://api.github.com/repos/JWBinderRepository/JWBinder/releases'),
    ('wasmizer-releases', 'https://api.github.com/repos/arash-mazidi/WASMIZER/releases'),
]


def fetch_metadata(source):
    name, url = source
    path = ROOT/'data/catalog/followup-sources'/(name+'.json')
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with get(url) as response:
            data = response.read()
        json.loads(data)
        path.write_bytes(data)
    data = path.read_bytes()
    return {'source':name, 'url':url, 'path':path.relative_to(ROOT).as_posix(),
            'sha256':hashlib.sha256(data).hexdigest(), 'bytes':len(data),
            'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}


def main():
    tasks = [(fetch_metadata, s, s[0]) for s in SOURCES]
    tasks += [(audit, d, d['id']) for d in [
        {'id':'jwbinder','github':'JWBinderRepository/JWBinder'},
        {'id':'wasmizer','github':'arash-mazidi/WASMIZER'},
    ]]
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        pending = {pool.submit(fn, arg):name for fn,arg,name in tasks}
        for future in concurrent.futures.as_completed(pending):
            try:
                row = {'source':pending[future], 'status':'ok', 'result':future.result()}
            except Exception as exc:
                row = {'source':pending[future], 'status':'failed', 'error':repr(exc)}
            results.append(row)
            print(json.dumps(row), flush=True)
    output = ROOT/'results/catalog/followup-source-audit.json'
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(results,indent=2),encoding='utf-8')


if __name__ == '__main__':
    main()
