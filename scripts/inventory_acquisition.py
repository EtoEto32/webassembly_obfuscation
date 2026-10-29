"""Count every candidate occurrence, including acquisition failures without SHA."""
import collections
import datetime
import hashlib
import json
from analyze_corpus import ROOT, acquired_rows


def main():
    rows=[r for r in acquired_rows(include_unhashed=True) if r['dataset']!='wasm-obf-controls']
    report=[]
    for dataset in sorted({r['dataset'] for r in rows}):
        members=[r for r in rows if r['dataset']==dataset]
        report.append({'dataset':dataset,'candidate_occurrences':len(members),
            'hashed_occurrences':sum(bool(r.get('sha256')) for r in members),
            'unique_sha256':len({r['sha256'] for r in members if r.get('sha256')}),
            'stored_verified_occurrences':sum(r.get('acquisition_status')=='stored_verified' for r in members),
            'failure_statuses':dict(collections.Counter(r['acquisition_status'] for r in members
                                    if r.get('acquisition_status')!='stored_verified'))})
    result={'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'datasets':report,
            'dataset_count':len(report),'candidate_occurrences':len(rows),
            'hashed_occurrences':sum(bool(r.get('sha256')) for r in rows),
            'unique_sha256':len({r['sha256'] for r in rows if r.get('sha256')}),
            'inputs':[{'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
                      for p in sorted((ROOT/'data/catalog').glob('*/acquisition.jsonl'))],
            'note':'Acquisition snapshot only; not an opcode analysis completion claim. Historical hand-picked controls excluded as duplicate extraction of release members.'}
    (ROOT/'results/corpus/acquisition-checkpoint.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('datasets','inputs')}),flush=True)


if __name__=='__main__':
    main()
