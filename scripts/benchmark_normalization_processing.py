"""Repeated static preprocessing timings, no target module execution.

Measure implemented pipelines, including their CLI startup and final validation.
Not an algorithm-only benchmark and never a mining-throughput measurement.
"""
import json
import platform
import statistics
import subprocess
import sys
import time
from pathlib import Path
from evaluate_local_normalization import ROOT, WABT, OPT, sha
from normalize_wat_local import normalize

OUT = ROOT/'results/countermeasures/processing-timing'
METHODS = ('roundtrip', 'both', 'binaryen-local', 'binaryen-O2')


def run(args):
    result = subprocess.run(list(map(str, args)), capture_output=True, timeout=60)
    if result.returncode:
        raise RuntimeError(result.stderr.decode(errors='replace'))
    return result.stdout


def main():
    OUT.mkdir(exist_ok=True)
    development = json.loads((ROOT/'results/countermeasures/local-normalization/static-comparison.json').read_text(encoding='utf-8'))['records']
    transfer = json.loads((ROOT/'results/countermeasures/transfer/comparison.json').read_text(encoding='utf-8'))['records']
    chosen = [r for r in development if r['variant'] == 'unmodified']
    names = ('xmr-substitution', 'A-Star-instrumentation-control', 'CreaturePack-ordinary-control')
    chosen += [next(r for r in transfer if r['source'] == name and r['variant'] == 'unmodified') for name in names]
    assert len(chosen) == 6
    selection = dict(inputs=[dict(source=r['source'], path=r['path'], sha256=r['sha256']) for r in chosen],
                     methods=list(METHODS), warmup_rounds=1, measured_rounds=6,
                     scope='Input read, disassembly/rewrite/assembly or optimizer CLI, then output validation. SHA and log serialization are outside timing. Python process reused, tool subprocess startup included; compare implemented pipelines, not algorithm-only cost.',
                     normalizer_sha256=sha(ROOT/'scripts/normalize_wat_local.py'),
                     tools={name: sha(path) for name, path in [('wasm2wat', WABT/'wasm2wat.exe'), ('wat2wasm', WABT/'wat2wasm.exe'), ('validate', WABT/'wasm-validate.exe'), ('binaryen', OPT)]},
                     versions=dict(wabt=run([WABT/'wasm2wat.exe', '--version']).decode().strip(), binaryen=run([OPT, '--version']).decode().strip()),
                     python=sys.version, platform=platform.platform(), target_wasm_executed=False)
    for row in chosen:
        assert sha(ROOT/row['path']) == row['sha256']
    (OUT/'selection.json').write_text(json.dumps(selection, indent=2), encoding='utf-8')
    records = []
    for round_index in range(-1, 6):
        offset = (round_index+1) % len(chosen)
        ordered_inputs = chosen[offset:]+chosen[:offset]
        for input_index, row in enumerate(ordered_inputs):
            rotation = (round_index+1+input_index) % len(METHODS)
            order = METHODS[rotation:]+METHODS[:rotation]
            for position, method in enumerate(order):
                target = OUT/(row['source']+'-'+method+'.wasm')
                wat = target.with_suffix('.wat')
                start = time.perf_counter()
                data = (ROOT/row['path']).read_bytes()
                input_copy = OUT/'current-input.wasm'
                input_copy.write_bytes(data)
                events = []
                if method in ('roundtrip', 'both'):
                    text = run([WABT/'wasm2wat.exe', input_copy]).decode('utf-8')
                    if method == 'both':
                        text, events = normalize(text)
                    wat.write_text(text, encoding='utf-8')
                    run([WABT/'wat2wasm.exe', wat, '-o', target])
                else:
                    flags = ['--vacuum', '--precompute'] if method == 'binaryen-local' else ['-O2']
                    run([OPT, input_copy, *flags, '-o', target])
                run([WABT/'wasm-validate.exe', target])
                elapsed = (time.perf_counter()-start)*1000
                reference_rows = development if row in development else transfer
                expected = next((x for x in reference_rows if x['source'] == row['source'] and x['variant'] == method), None)
                output_sha = sha(target)
                if expected:
                    assert output_sha == expected['sha256'], (row['source'], method)
                records.append(dict(source=row['source'], method=method, round=round_index,
                                    warmup=round_index < 0, input_position=input_index, method_position=position,
                                    elapsed_ms=elapsed, events=len(events), output_sha256=output_sha,
                                    output_bytes=target.stat().st_size, valid=True,
                                    existing_processed_artifact_equal=output_sha == expected['sha256'] if expected else None))
        (OUT/'progress.json').write_text(json.dumps(dict(completed_round=round_index, records=len(records), target_wasm_executed=False)), encoding='utf-8')
    summaries = []
    for row in chosen:
        for method in METHODS:
            values = [x for x in records if x['source'] == row['source'] and x['method'] == method and not x['warmup']]
            assert len(values) == 6 and len({x['output_sha256'] for x in values}) == 1
            times = [x['elapsed_ms'] for x in values]
            summaries.append(dict(source=row['source'], method=method, repetitions=len(values), median_ms=statistics.median(times), min_ms=min(times), max_ms=max(times), stable_output_sha256=values[0]['output_sha256']))
    report = dict(selection_sha256=sha(OUT/'selection.json'), evaluator_sha256=sha(Path(__file__)), records=records, summaries=summaries,
                  target_wasm_executed=False, hash_throughput_measured=False,
                  limitations='Single host, six repetitions, warm filesystem cache, no CPU affinity. CLI/Python startup boundaries differ by pipeline. Timing includes output write and validation; cannot identify pure rewrite/optimizer superiority.')
    (OUT/'results.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(dict(records=len(records), measured=sum(not x['warmup'] for x in records), summary_conditions=len(summaries))))


if __name__ == '__main__':
    main()
