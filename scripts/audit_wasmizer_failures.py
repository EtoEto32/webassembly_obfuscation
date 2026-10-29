"""Measure tool-failure concentration in author-provided source-path metadata."""
import collections
import csv
import datetime
import hashlib
import json
import re
from analyze_corpus import ROOT, CACHE, VERSION


def main():
    source=ROOT/'results/provenance/wasmizer-metadata.jsonl'
    metadata=[json.loads(line) for line in source.read_text(encoding='utf-8').splitlines()]
    rows=[];receipts=[]
    for m in metadata:
        path=CACHE/(m['sha256']+'.json')
        raw=path.read_bytes() if path.exists() else None
        d=json.loads(raw) if raw else {'status':'pending'}
        if raw and not (d.get('analyzer_version')==VERSION or (d.get('analyzer_version')=='2.0.0' and d['status']=='ok')):
            d={'status':'pending_stale_version'}
        receipts.append({'sha256':m['sha256'],'cache_sha256':hashlib.sha256(raw).hexdigest() if raw else None})
        paths=m.get('source_paths',[])
        rows.append({'sha256':m['sha256'],'status':d['status'],
                     'test_path_evidence':m.get('test_path_evidence',False),
                     'dependency_path_evidence':m.get('dependency_path_evidence',False),
                     'invalid_named_path_evidence':any(re.search(r'(^|[/_.-])invalid([/_.-]|$)',s,re.I) for s in paths),
                     'valid_without_custom_sections':d.get('valid_wabt_without_custom_sections'),
                     'source_paths_json':json.dumps(paths),
                     'diagnostic':d.get('error','')})
    strata=[]
    for field in ('test_path_evidence','dependency_path_evidence','invalid_named_path_evidence'):
        for value in (False,True):
            selected=[r for r in rows if r[field]==value]
            counts=collections.Counter(r['status'] for r in selected)
            attempted=sum(n for status,n in counts.items() if not status.startswith('pending'))
            failed=attempted-counts['ok']
            strata.append({'path_indicator':field,'indicator_value':value,'modules':len(selected),
                           'attempted':attempted,'failed':failed,'failure_fraction_among_attempted':failed/attempted if attempted else None,
                           'status_counts':dict(counts)})
    output=ROOT/'results/provenance'
    with (output/'wasmizer-analysis-status.csv').open('w',encoding='utf-8',newline='') as dest:
        writer=csv.DictWriter(dest,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    summary={'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'modules':len(rows),
             'status_counts':dict(collections.Counter(r['status'] for r in rows)),
             'metadata_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'strata':strata,
             'method':'One row per binary SHA; source-path flags can overlap and use any associated source path. Failure refers to this WABT/analyzer configuration.',
             'interpretation':'Paths containing test, fixture, spec, dependencies, or invalid are provenance indicators. They do not prove that a module was intentionally invalid, malicious, or obfuscated.'}
    (output/'wasmizer-failure-summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    (output/'wasmizer-analysis-inputs.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in receipts),encoding='utf-8')
    print(json.dumps(summary),flush=True)


if __name__=='__main__':main()
