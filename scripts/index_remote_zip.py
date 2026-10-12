"""Read a public ZIP central directory via validated HTTP byte ranges."""
import argparse
import collections
import json
import zipfile
from pathlib import Path
from acquire import ROOT, RemoteSplitZip


def index(item):
    folder=ROOT/'data/catalog'/(item['id']+'-remote')
    folder.mkdir(parents=True,exist_ok=True)
    stream=RemoteSplitZip([{'name':item['filename'],'size':item['bytes'],
                            'browser_download_url':item['url']}])
    stream.cache=folder/'ranges'; stream.cache.mkdir(exist_ok=True)
    with zipfile.ZipFile(stream) as archive:
        rows=[{'path':z.filename,'bytes':z.file_size,'compressed_bytes':z.compress_size,
               'crc32':z.CRC,'method':z.compress_type} for z in archive.infolist()]
    (folder/'index.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
    summary={'artifact':item['id'],'members':len(rows),'range_bytes_downloaded':stream.downloaded,
             'extensions':dict(collections.Counter(Path(r['path']).suffix for r in rows)),
             'wasm_paths':[r for r in rows if r['path'].lower().endswith('.wasm')]}
    (folder/'index-summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k!='wasm_paths'}),flush=True)
    print('wasm members',len(summary['wasm_paths']),'compressed bytes',sum(r['compressed_bytes'] for r in summary['wasm_paths']),flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('ids',nargs='+'); args=ap.parse_args()
    for item in json.loads((ROOT/'experiments/archive-registry.json').read_text()):
        if item['id'] in args.ids: index(item)
