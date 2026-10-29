"""Retrieve public primary-source leads; keep failed downloads distinct."""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

URLS=[('incremental-openmp','https://www.osti.gov/servlets/purl/956842'),
 ('compiler-checkpoint-patent','https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/6708288'),
 ('array-checkpoint','https://citeseerx.ist.psu.edu/document?doi=f51646ac11d05d221166ab2246935d876a21c7f9&repid=rep1&type=pdf')]
def main(out,only=None,timeout=12):
    out.mkdir(parents=True,exist_ok=False);(out/'.gitignore').write_text('*.pdf\n*.txt\n',encoding='utf8');records=[]
    for name,url in URLS:
        if only is not None and name!=only:continue
        row={'name':name,'url':url}
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'WasmResearch/1.0 public-literature'})
            with urllib.request.urlopen(req,timeout=timeout) as response:
                data=response.read(16*1024*1024+1);row['finalUrl']=response.url
            if len(data)>16*1024*1024:raise ValueError('document size bound')
            if not data.startswith(b'%PDF-'):raise ValueError('not a PDF')
            file=out/(name+'.pdf');file.write_bytes(data);row.update(status='downloaded',bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
            from pypdf import PdfReader
            reader=PdfReader(file);text='\n'.join('PAGE '+str(i+1)+'\n'+(p.extract_text()or'') for i,p in enumerate(reader.pages))
            (out/(name+'.txt')).write_text(text,encoding='utf8');row['pages']=len(reader.pages)
        except Exception as error:row.update(status='failed',error=str(error))
        records.append(row);(out/'retrieval.json').write_text(json.dumps(records,indent=2),encoding='utf8')
        print(json.dumps(row),flush=True)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);ap.add_argument('--only',choices=[n for n,u in URLS]);ap.add_argument('--timeout',type=int,default=12)
    a=ap.parse_args();main(a.output.resolve(),a.only,a.timeout)
