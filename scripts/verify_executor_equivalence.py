"""Compare scheduling modes on fixed public modules without executing modules."""
import concurrent.futures
import datetime
import hashlib
import json
import time
from analyze_corpus import ROOT, CACHE, analyze, acquired_rows


def stable(result):
    return {k:v for k,v in result.items() if k not in ('analyzed_utc','analysis_seconds')}


def main():
    candidates=sorted(acquired_rows(['wasm-r3']),key=lambda r:(r['bytes'],r['sha256']))
    indices=[0,len(candidates)//4,len(candidates)//2,3*len(candidates)//4,len(candidates)-1]
    selected=[candidates[i] for i in indices]
    expected={r['sha256']:stable(json.loads((CACHE/(r['sha256']+'.json')).read_text(encoding='utf-8')))
              for r in selected}
    report=[]
    for name,executor in [('threads',concurrent.futures.ThreadPoolExecutor),('processes',concurrent.futures.ProcessPoolExecutor)]:
        start=time.monotonic()
        with executor(max_workers=2) as pool:
            results=list(pool.map(analyze,selected))
        rows=[]
        for result in results:
            value=stable(result);matches=value==expected[result['sha256']]
            rows.append({'sha256':result['sha256'],'status':result['status'],
                         'all_measurements_equal_to_saved_process_run':matches,
                         'stable_measurement_sha256':hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()})
            if not matches:raise ValueError('Scheduling mode changed a measurement: '+result['sha256'])
        report.append({'executor':name,'workers':2,'wall_seconds':round(time.monotonic()-start,4),'modules':rows})
    output={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'selection':'Wasm-R3 size-order positions 0, floor(N/4), floor(N/2), floor(3N/4), N-1; immutable SHA identifiers below',
            'excluded_comparison_fields':['analyzed_utc','analysis_seconds'],'results':report,
            'interpretation':'A bounded scheduling-equivalence check; timings under concurrent system load are not a general performance benchmark.'}
    (ROOT/'results/corpus/executor-equivalence.json').write_text(json.dumps(output,indent=2),encoding='utf-8')
    print(json.dumps({'all_measurements_equal':True,'modules':len(selected),
                      'timings':[{k:r[k] for k in ('executor','workers','wall_seconds')} for r in report]}),flush=True)


if __name__=='__main__':main()
