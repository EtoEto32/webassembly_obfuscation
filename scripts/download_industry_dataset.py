"""Fetch the paper-linked public Drive artifact without account credentials."""
import json
import hashlib
from html.parser import HTMLParser
from urllib.parse import urlencode, urlparse
from acquire import ROOT, get
from download_artifacts import download

FILE_ID='1HflCNDkIDyqNLFi4uvp6IdZgfJQCz510'


class DownloadForm(HTMLParser):
    def __init__(self):
        super().__init__(); self.action=None; self.fields={}; self.in_form=False
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='form' and a.get('id')=='download-form':
            self.in_form=True; self.action=a.get('action')
        if self.in_form and tag=='input' and a.get('type')=='hidden':
            self.fields[a['name']]=a.get('value','')
    def handle_endtag(self,tag):
        if tag=='form': self.in_form=False


def main():
    cached=ROOT/'data/archives/industry2025-validwasm.7z'
    receipt=cached.with_suffix(cached.suffix+'.receipt.json')
    if cached.exists() and receipt.exists():
        recorded=json.loads(receipt.read_text())
        checksum=hashlib.sha256()
        with cached.open('rb') as stream:
            for chunk in iter(lambda:stream.read(8*1024*1024),b''): checksum.update(chunk)
        if cached.stat().st_size==recorded['bytes'] and checksum.hexdigest()==recorded['sha256']:
            print('Existing public artifact size and SHA-256 verified; no new download URL needed',flush=True)
            return
        raise ValueError('Cached public artifact differs from receipt; preserve for inspection')
    source=f'https://drive.google.com/uc?export=download&id={FILE_ID}'
    with get(source) as response:
        if 'text/html' not in response.headers.get('Content-Type',''):
            raise ValueError('Expected the public large-file download form')
        html=response.read(200000).decode('utf-8')
    parser=DownloadForm(); parser.feed(html)
    if not parser.action or urlparse(parser.action).netloc!='drive.usercontent.google.com' or parser.fields.get('id')!=FILE_ID:
        raise ValueError('Unexpected public download form')
    item={'id':'industry2025-validwasm','dataset':'industry2025','filename':'industry2025-validwasm.7z',
          'url':parser.action+'?'+urlencode(parser.fields),'paper_url':'https://arxiv.org/html/2503.21240v1',
          'public_view_url':f'https://drive.google.com/file/d/{FILE_ID}/view',
          'file_magic_hex':'377abcaf271c','role':'paper-linked complete valid-binary comparator; dates and labels pending content audit',
          'license_note':'public paper-linked download; explicit artifact license pending inspection'}
    path=ROOT/'experiments/archive-registry.json'
    entries=json.loads(path.read_text()); entries=[e for e in entries if e['id']!=item['id']]+[item]
    path.write_text(json.dumps(entries,indent=2)+'\n',encoding='utf-8')
    download(item)


if __name__=='__main__': main()
