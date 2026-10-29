"""Static comparison only; disassemble/validate/optimize, never instantiate miners."""
import hashlib
import json
import subprocess
import time
from collections import Counter
from pathlib import Path
from normalize_wat_local import normalize
from analyze_corpus import analyze

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/countermeasures/local-normalization'
WABT=ROOT/'.tools/wabt-1.0.42/bin'
OPT=ROOT/'.tools/binaryen-version_133/bin/wasm-opt.exe'
SOURCE=ROOT/'results/runtime-mining/cross-dataset/swamped'

def run(args):
    result=subprocess.run([str(a) for a in args],capture_output=True,text=True,timeout=120)
    if result.returncode:raise RuntimeError(result.stderr)
    return result.stdout+result.stderr

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def measure(path):
    result=analyze(dict(object=str(path.relative_to(ROOT)).replace('\\','/'),sha256=sha(path)))
    assert result['status']=='ok' and result['valid_wabt'],result
    wat=run([WABT/'wasm2wat.exe',path])
    return dict(sha256=sha(path),bytes=path.stat().st_size,instruction_count=result['instruction_count'],instructions=result['opcodes'],sections=result['sections'],imports=result['imports'],exports=result['exports'],validated=True),wat

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    records=[]
    for name in ['046dc081-roundtrip','046dc081-nop10','046dc081-constsplit10']:
        original=SOURCE/(name+'.wasm')
        original_metrics,wat=measure(original)
        targets=[('unmodified',original,[],None)]
        for label,rules in [('nop',('nop',)),('integer-fold',('integer-fold',)),('both',('nop','integer-fold'))]:
            t=time.perf_counter();result,events=normalize(wat,rules);elapsed=(time.perf_counter()-t)*1000
            target=OUT/(name+'-'+label+'.wasm');textpath=target.with_suffix('.wat')
            textpath.write_text(result,encoding='utf-8')
            run([WABT/'wat2wasm.exe',textpath,'-o',target])
            target.with_suffix('.events.json').write_text(json.dumps(events,indent=2),encoding='utf-8')
            targets.append((label,target,events,elapsed))
        for label,flags in [('binaryen-local',['--vacuum','--precompute']),('binaryen-O2',['-O2'])]:
            target=OUT/(name+'-'+label+'.wasm');t=time.perf_counter()
            run([OPT,original,*flags,'-o',target]);elapsed=(time.perf_counter()-t)*1000
            targets.append((label,target,[],elapsed))
        for label,target,events,elapsed in targets:
            metrics,text=measure(target)
            target_wat=OUT/(name+'-'+label+'-canonical.wat');target_wat.write_text(text,encoding='utf-8')
            records.append(dict(source=name,variant=label,path=str(target.relative_to(ROOT)).replace('\\','/'),**metrics,
                                canonical_wat_sha256=sha(target_wat),events=len(events),events_by_rule=dict(Counter(e['rule'] for e in events)),
                                transform_elapsed_ms=elapsed,
                                timing_scope='in-process rewrite only' if label in ['nop','integer-fold','both'] else 'optimizer process startup and run' if label.startswith('binaryen') else None,
                                runtime_executed=False,output_correctness_checked=False))
    for row in records:
        ref=next(r for r in records if r['source']=='046dc081-roundtrip' and r['variant']==row['variant'])
        row['same_as_equally_processed_reference_bytes']=row['sha256']==ref['sha256']
        row['same_as_equally_processed_reference_wat']=row['canonical_wat_sha256']==ref['canonical_wat_sha256']
        original=next(r for r in records if r['source']==row['source'] and r['variant']=='unmodified')
        row['raw_import_export_records_equal']=row['imports']==original['imports'] and row['exports']==original['exports']
        row['import_export_names_kinds_equal']=([(x['module'],x['name'],x['kind']) for x in row['imports']]==[(x['module'],x['name'],x['kind']) for x in original['imports']]
            and [(x['name'],x['kind']) for x in row['exports']]==[(x['name'],x['kind']) for x in original['exports']])
    report=dict(date='2026-10-10',records=records,
                normalizer_sha256=sha(ROOT/'scripts/normalize_wat_local.py'),
                tools=dict(wabt=run([WABT/'wasm2wat.exe','--version']).strip(),binaryen=run([OPT,'--version']).strip(),binaryen_sha256=sha(OPT)),
                provenance='Existing seed-20261008 controls are development cases, not held-out evaluation.',
                scope='Static validated artifacts only; no new hashing, throughput, detector or all-input equivalence claim.')
    (OUT/'static-comparison.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps([dict(source=r['source'],variant=r['variant'],bytes=r['bytes'],instructions=r['instruction_count'],events=r['events'],reference_wat_equal=r['same_as_equally_processed_reference_wat']) for r in records],indent=2))

if __name__=='__main__':main()
