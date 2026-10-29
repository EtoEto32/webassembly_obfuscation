"""Static held-out expression evaluation; no Wasm instantiation or rewriting."""
import csv
import json
import time
from pathlib import Path
from analyze_integer_expressions import extract
from evaluate_local_normalization import ROOT,WABT,run,sha

OUT=ROOT/'results/countermeasures/cryptic-expression-transfer'
METHODS={'unobfuscated','llvm/subobf','tigress/encodearithmetic'}


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    with (ROOT/'results/provenance/cryptic-bytes-parents.csv').open(encoding='utf-8',newline='') as handle:
        selected=[r for r in csv.DictReader(handle) if r['program_category']=='miners' and r['declared_transformation'] in METHODS]
    # Freeze selection before inspecting results; include both published build
    # conditions, all ten miners, and every selected method, including negatives.
    (OUT/'selection.json').write_text(json.dumps(dict(selection=selected,analyzer_sha256=sha(ROOT/'scripts/analyze_integer_expressions.py'),
                                                    rule='All miners, both published release variants, unobfuscated/llvm-subobf/tigress-encodearithmetic'),indent=2),encoding='utf-8')
    records=[]
    for row in selected:
        path=ROOT/'data/objects'/(row['sha256']+'.bin')
        assert sha(path)==row['sha256']
        run([WABT/'wasm-validate.exe',path])
        text=run([WABT/'wasm2wat.exe',path])
        start=time.perf_counter();matches,counts=extract(text);elapsed=(time.perf_counter()-start)*1000
        stem='-'.join([row['program'],row['release_variant'],row['declared_transformation'].replace('/','-')])
        detail=OUT/(stem+'.json')
        detail.write_text(json.dumps(dict(matches=matches,counts=counts,input_sha256=row['sha256']),indent=2),encoding='utf-8')
        (OUT/(stem+'.wat')).write_text(text,encoding='utf-8')
        record=dict(program=row['program'],release_variant=row['release_variant'],declared_transformation=row['declared_transformation'],
                    sha256=row['sha256'],baseline_sha256=row['comparison_baseline_sha256'],path=row['path'],source_commit=row['source_commit'],
                    matches=len(matches),candidates=counts.get('candidates',0),supported_polynomials=counts.get('supported_polynomials',0),
                    elapsed_ms=elapsed,validated=True,detail=str(detail.relative_to(ROOT)))
        records.append(record)
        (OUT/'progress.json').write_text(json.dumps(dict(completed=len(records),total=len(selected),records=records),indent=2),encoding='utf-8')
    report=dict(date='2026-10-10',records=records,analyzer_sha256=sha(ROOT/'scripts/analyze_integer_expressions.py'),evaluator_sha256=sha(Path(__file__)),
                selection_sha256=sha(OUT/'selection.json'),wabt=run([WABT/'wasm2wat.exe','--version']).strip(),code_rewritten=False,runtime_executed=False,
                limitations=['Miners share CryptoNight ancestry; ten programs are not ten independent malware families.',
                             'Declared transformation labels are not full instruction-level mechanism validation.',
                             'A complex identity does not by itself prove obfuscation intent.',
                             'Zero matches may result from unsupported syntax or dependency patterns.',
                             'Matches may overlap; these are expression outputs, not counts of unique obfuscation sites.'])
    (OUT/'comparison.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    with (OUT/'comparison.csv').open('w',encoding='utf-8',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
    print(json.dumps(dict(records=len(records),nonzero_records=sum(bool(r['matches']) for r in records),matches=sum(r['matches'] for r in records))))


if __name__=='__main__':
    main()
