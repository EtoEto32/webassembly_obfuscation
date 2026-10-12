"""Inspect bounded reference follow-ups from the core papers and author links."""
import concurrent.futures
import json
from acquire import ROOT
from catalog_datasets import audit, fetch

SOURCES=[{'id':'wasm-r3','github':'sola-st/wasm-r3','ref':'OOPSLA_2024'},
         {'id':'minesweeper','github':'vusec/minesweeper'},
         {'id':'outguard','github':'teamnsrg/outguard'}]


def one(dataset):
    row=audit(dataset)
    path=ROOT/'data/catalog'/dataset['id']/'releases.json'
    releases=fetch(f"https://api.github.com/repos/{dataset['github']}/releases",path)
    row['releases']=len(releases)
    return row


if __name__=='__main__':
    results=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for dataset,future in zip(SOURCES,[pool.submit(one,d) for d in SOURCES]):
            try:row={'status':'ok','result':future.result()}
            except Exception as exc:row={'status':'failed','dataset':dataset['id'],'error':repr(exc)}
            results.append(row);print(json.dumps(row),flush=True)
    (ROOT/'results/catalog/final-reference-layouts.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
