"""Download named public literature for local reading; no external uploads."""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request
from pypdf import PdfReader

URLS={
 'flexible-access-control':'https://kth.diva-portal.org/smash/get/diva2%3A2046977/FULLTEXT01.pdf',
 'array-checkpoint':'https://citeseerx.ist.psu.edu/document?doi=f51646ac11d05d221166ab2246935d876a21c7f9&repid=rep1&type=pdf',
}
def main(out):
    out.mkdir(parents=True,exist_ok=False);records=[]
    for name,url in URLS.items():
        record={'name':name,'url':url}
        try:
            with urllib.request.urlopen(url,timeout=45) as response:
                data=response.read(32*1024*1024+1)
            if len(data)>32*1024*1024 or not data.startswith(b'%PDF-'):raise ValueError('not a bounded PDF')
            pdf=out/(name+'.pdf');pdf.write_bytes(data)
            reader=PdfReader(pdf)
            texts=[p.extract_text() or '' for p in reader.pages]
            (out/(name+'.txt')).write_text('\n\n'.join('=== page %d ===\n%s'%(i+1,t) for i,t in enumerate(texts)),encoding='utf8')
            record.update(status='downloaded-and-text-extracted',sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),pages=len(texts))
        except Exception as e:record.update(status='failed',error=str(e))
        records.append(record)
    (out/'retrieval.json').write_text(json.dumps(records,indent=2),encoding='utf8')
    print(json.dumps(records))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path)
    main(ap.parse_args().output.resolve())
