"""Read only the HTTP headers of the author-linked crawled corpus."""
import datetime
import json
import urllib.request
from acquire import ROOT,HEADERS

url='https://download.vusec.net/dataset/cryptominers_dataset.tar'
request=urllib.request.Request(url,headers=HEADERS,method='HEAD')
try:
    with urllib.request.urlopen(request,timeout=45) as response:
        result={'url':url,'status':response.status,'headers':dict(response.headers),'final_url':response.url}
except Exception as exc:result={'url':url,'status':'failed','error':repr(exc)}
result['checked_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
(ROOT/'results/catalog/minesweeper-archive-head.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result),flush=True)
