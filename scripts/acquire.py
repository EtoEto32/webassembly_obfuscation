"""Reproducible, read-only acquisition of upstream public research artifacts."""
import argparse
import bisect
import hashlib
import io
import json
from pathlib import Path
import time
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
META = ROOT / 'data' / 'upstream'
HEADERS = {'User-Agent': 'wasm-obfuscation-pilot-research', 'Accept-Encoding': 'identity'}

def get(url, headers=None):
    req = urllib.request.Request(url, headers={**HEADERS, **(headers or {})})
    return urllib.request.urlopen(req, timeout=90)

def json_fetch(url, name):
    META.mkdir(parents=True, exist_ok=True)
    path = META / name
    if not path.exists():
        with get(url) as response:
            path.write_bytes(response.read())
    return json.loads(path.read_text(encoding='utf-8'))

class RemoteSplitZip(io.RawIOBase):
    """Seekable concatenation of release assets; fetch only requested byte ranges.

    ZipFile supplies ZIP64/central-directory handling and CRC validation. Cached
    byte ranges avoid downloading the multi-GB archive, without altering entries.
    """
    def __init__(self, assets):
        self.assets = assets
        self.starts = [0]
        for a in assets:
            self.starts.append(self.starts[-1] + a['size'])
        self.pos = 0
        self.downloaded = 0
        self.cache = META / 'range-cache'
        self.cache.mkdir(parents=True, exist_ok=True)

    def seekable(self): return True
    def readable(self): return True
    def tell(self): return self.pos

    def seek(self, offset, whence=0):
        self.pos = offset if whence == 0 else self.pos + offset if whence == 1 else self.starts[-1] + offset
        if self.pos < 0:
            raise ValueError('negative seek')
        return self.pos

    def read(self, size=-1):
        if size < 0:
            size = self.starts[-1] - self.pos
        size = min(size, self.starts[-1] - self.pos)
        chunks = []
        while size > 0:
            i = bisect.bisect_right(self.starts, self.pos) - 1
            asset = self.assets[i]
            offset = self.pos - self.starts[i]
            count = min(size, asset['size'] - offset)
            key = f"{asset['name']}.{offset}.{count}"
            path = self.cache / key
            if path.exists():
                chunk = path.read_bytes()
            else:
                with get(asset['browser_download_url'], {'Range': f'bytes={offset}-{offset+count-1}'}) as response:
                    if response.status != 206:
                        raise RuntimeError(f'Range unsupported: {response.status}; refusing full archive download')
                    expected = f'bytes {offset}-{offset+count-1}/{asset["size"]}'
                    if response.headers.get('Content-Range') != expected:
                        raise RuntimeError(f'Unexpected Content-Range: {response.headers.get("Content-Range")}')
                    chunk = response.read(count + 1)
                if len(chunk) != count:
                    raise RuntimeError('Short/oversized range response')
                path.write_bytes(chunk)
                self.downloaded += len(chunk)
            if len(chunk) != count:
                raise RuntimeError('Invalid cached range')
            chunks.append(chunk)
            self.pos += count
            size -= count
        return b''.join(chunks)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['metadata', 'index', 'extract'])
    parser.add_argument('--selection', type=Path)
    args = parser.parse_args()
    release = json_fetch('https://api.github.com/repos/HakonHarnes/wasm-obf/releases/tags/v1.0', 'release.json')
    if args.action == 'metadata':
        tree = json_fetch('https://api.github.com/repos/HakonHarnes/wasm-obf/git/trees/main?recursive=1', 'tree.json')
        print('upstream commit', tree['sha'])
        for item in tree['tree']:
            p = item['path']
            if (p.startswith('dataset/utilities/') and p.count('/') == 2) or p in ['dataset/main.py', 'dataset/Dockerfile', 'obfuscation/tigress/main.py', 'obfuscation/llvm/main.py', 'optimization/opt/main.py']:
                print(p)
        for a in release['assets']:
            print(a['name'], a['size'])
        return
    assets = sorted([a for a in release['assets'] if a['name'].startswith('binaries.zip.')], key=lambda a:a['name'])
    stream = RemoteSplitZip(assets)
    with zipfile.ZipFile(stream) as archive:
        entries = [{'name': z.filename, 'size': z.file_size, 'compressed_size': z.compress_size, 'crc32': z.CRC} for z in archive.infolist()]
        (META / 'archive-index.json').write_text(json.dumps(entries, indent=2), encoding='utf-8')
        if args.action == 'index':
            selected = [z for z in entries if z['name'].endswith('.wasm') and ('flatten' in z['name'].lower() or 'original' in z['name'].lower())]
            print(json.dumps(selected[:80], indent=2))
            print('entries', len(entries), 'downloaded bytes', stream.downloaded)
            return
        names = json.loads(args.selection.read_text(encoding='utf-8'))
        manifest = []
        for name in names:
            destination = (ROOT / 'data' / 'raw' / name).resolve()
            destination.relative_to((ROOT / 'data' / 'raw').resolve())
            content = archive.read(name)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
            manifest.append({'archive_entry': name, 'path': destination.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(content).hexdigest(), 'bytes': len(content), 'retrieved_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'source': release['html_url']})
            print(name, len(content), flush=True)
        (META / 'acquisition-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        print('downloaded bytes', stream.downloaded)

if __name__ == '__main__':
    main()
