"""Static transfer evaluation on existing independent programs and controls.

Never instantiate Wasm. Rules remain frozen in normalize_wat_local.py.
Controls are manually reviewed research instrumentation and ordinary programs;
changes in those controls are not evidence of malicious obfuscation.
"""
import json
import csv
import time
from collections import Counter
from pathlib import Path
from evaluate_local_normalization import ROOT, WABT, OPT, run, sha, measure
from normalize_wat_local import normalize

OUT = ROOT / 'results/countermeasures/transfer'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ledger = json.loads((ROOT/'results/rq-validation/review-ledger.json').read_text(encoding='utf-8'))
    sources = []
    for row in ledger:
        if row['mechanism'] == 'research_instrumentation':
            for role, key in [('ordinary-control', 'origin'), ('instrumentation-control', 'variant')]:
                sources.append((row['program']+'-'+role, role, ROOT/'data/objects'/(row[key]+'.bin')))
        elif row['mechanism'] == 'control_flow_flattening':
            for role, key in [('reference', 'origin'), ('flattened-heldout-program', 'variant')]:
                sources.append((row['program']+'-'+role, role, ROOT/'data/objects'/(row[key]+'.bin')))
    # Saved WAT is reassembled uniformly; retain provenance distinct from originals.
    for label in ['original', 'flattening', 'substitution', 'split']:
        text = ROOT/'results/runtime-mining/cross-dataset/proof-of-theft'/('xmr-'+label+'.wat')
        target = OUT/('xmr-'+label+'-roundtrip.wasm')
        run([WABT/'wat2wasm.exe', text, '-o', target])
        sources.append(('xmr-'+label, 'existing-miner-'+label, target))
    records = []
    for name, role, source in sources:
        metrics, wat = measure(source)
        original = dict(source=name, role=role, variant='unmodified', path=str(source.relative_to(ROOT)), **metrics)
        records.append(original)
        for label, rules in [('nop', ('nop',)), ('integer-fold', ('integer-fold',)), ('both', ('nop', 'integer-fold'))]:
            start = time.perf_counter()
            text, events = normalize(wat, rules)
            elapsed = (time.perf_counter()-start)*1000
            target = OUT/(name+'-'+label+'.wasm')
            target.with_suffix('.wat').write_text(text, encoding='utf-8')
            target.with_suffix('.events.json').write_text(json.dumps(events, indent=2), encoding='utf-8')
            run([WABT/'wat2wasm.exe', target.with_suffix('.wat'), '-o', target])
            result, _ = measure(target)
            records.append(dict(source=name, role=role, variant=label, path=str(target.relative_to(ROOT)), **result,
                                events=len(events), events_by_rule=dict(Counter(e['rule'] for e in events)),
                                transform_elapsed_ms=elapsed, timing_scope='in-process rewrite only',
                                byte_identical_to_input=result['sha256']==metrics['sha256'],
                                imports_exports_unchanged=result['imports']==metrics['imports'] and result['exports']==metrics['exports']))
        for label, flags in [('binaryen-local', ['--vacuum', '--precompute']), ('binaryen-O2', ['-O2'])]:
            target = OUT/(name+'-'+label+'.wasm')
            start = time.perf_counter()
            run([OPT, source, *flags, '-o', target])
            elapsed = (time.perf_counter()-start)*1000
            result, _ = measure(target)
            records.append(dict(source=name, role=role, variant=label, path=str(target.relative_to(ROOT)), **result,
                                transform_elapsed_ms=elapsed, timing_scope='optimizer process startup and run'))
    for row in records:
        base = next(r for r in records if r['source']==row['source'] and r['variant']=='unmodified')
        row['instruction_delta'] = row['instruction_count']-base['instruction_count']
        row['byte_delta'] = row['bytes']-base['bytes']
        row['control_call_opcodes_equal'] = all(row['instructions'].get(op, 0)==base['instructions'].get(op, 0)
            for op in ['block', 'loop', 'if', 'else', 'br', 'br_if', 'br_table', 'call', 'call_indirect'])
    report = dict(date='2026-10-10', records=records, normalizer_sha256=sha(ROOT/'scripts/normalize_wat_local.py'),
                  evaluator_sha256=sha(Path(__file__)),
                  tools=dict(wabt=run([WABT/'wasm2wat.exe', '--version']).strip(), binaryen=run([OPT, '--version']).strip(), binaryen_sha256=sha(OPT)),
                  runtime_executed=False, output_correctness_checked=False,
                  scope='Static transfer to held-out programs and selected negative controls. No detector evaluation or all-input equivalence proof.',
                  leakage='Frozen rules created with SWAMPED development pair; A-Star, CreaturePack, base64 and seqtk were not used to implement rules. xmr was previously reviewed for mechanisms.',
                  limitations=['Different programs are transfer cases, not random population sampling.',
                               'Harmless constant folding or NOP removal on normal code must not be labelled malicious obfuscation.',
                               'Control/call opcode counts are weaker evidence than full control-flow equivalence.',
                               'Miner inputs are uniformly reassembled saved WAT, not claimed byte-identical distributed originals.'])
    (OUT/'comparison.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    fields = ['source', 'role', 'variant', 'sha256', 'bytes', 'instruction_count', 'byte_delta', 'instruction_delta', 'events', 'transform_elapsed_ms', 'timing_scope', 'control_call_opcodes_equal']
    with (OUT/'comparison.csv').open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(records)
    print(json.dumps([dict(source=r['source'],variant=r['variant'],instructions=r['instruction_count'],delta=r['instruction_delta'],events=r.get('events'),controls_equal=r['control_call_opcodes_equal']) for r in records if r['variant'] in ['unmodified', 'both']], indent=2))


if __name__ == '__main__':
    main()
