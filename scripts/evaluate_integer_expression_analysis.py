"""Evaluate read-only integer expression analysis on static comparison inputs."""
import csv
import json
import time
from collections import Counter
from pathlib import Path
from analyze_integer_expressions import extract
from evaluate_local_normalization import ROOT,WABT,run,sha

OUT=ROOT/'results/countermeasures/expression-analysis'


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    inputs=json.loads((ROOT/'results/countermeasures/transfer/comparison.json').read_text(encoding='utf-8'))['records']
    records=[]
    for row in inputs:
        if row['variant'] not in ['unmodified','binaryen-O2']:
            continue
        path=ROOT/row['path']
        text=run([WABT/'wasm2wat.exe',path])
        stem=row['source']+'-'+row['variant']
        watpath=OUT/(stem+'.wat');watpath.write_text(text,encoding='utf-8')
        start=time.perf_counter();matches,counts=extract(text);elapsed=(time.perf_counter()-start)*1000
        detail=OUT/(stem+'.json')
        detail.write_text(json.dumps(dict(matches=matches,counts=counts,input_sha256=sha(path)),indent=2),encoding='utf-8')
        records.append(dict(source=row['source'],role=row['role'],variant=row['variant'],input_sha256=sha(path),
                            matches=len(matches),unique_line_spans=len({(m['function'],m['first_line'],m['last_line']) for m in matches}),
                            counts=counts,shift_histogram=dict(Counter(m['shift'] for m in matches)),
                            elapsed_ms=elapsed,detail=str(detail.relative_to(ROOT)),wat_sha256=sha(watpath)))
    report=dict(records=records,analyzer_sha256=sha(ROOT/'scripts/analyze_integer_expressions.py'),
                evaluator_sha256=sha(Path(__file__)),date='2026-10-10',wabt=run([WABT/'wasm2wat.exe','--version']).strip(),
                code_rewritten=False,runtime_executed=False,
                development='Previously reviewed xmr substitution expression informed the supported algebra; xmr is not held-out.',
                scope='Exact polynomial identities for supported single-variable local expressions only, not module equivalence, maliciousness, path coverage or detector performance.',
                limitations=['Matches may overlap and must not be counted as distinct transformations.',
                             'Minimum 12 expression nodes; simple reference shifts are intentionally not returned.',
                             'No symbolic propagation across unsupported instructions, branches, memory or calls.',
                             'Polynomial and expression limits skip difficult cases; absence is not proof of no obfuscation.',
                             'This implementation is not a reimplementation or benchmark of MBA-Blast.'])
    (OUT/'comparison.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    with (OUT/'comparison.csv').open('w',encoding='utf-8',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=['source','role','variant','input_sha256','matches','unique_line_spans','elapsed_ms'],extrasaction='ignore')
        writer.writeheader();writer.writerows(records)
    print(json.dumps([{k:r[k] for k in ['source','variant','matches','elapsed_ms']} for r in records],indent=2))


if __name__=='__main__':
    main()
