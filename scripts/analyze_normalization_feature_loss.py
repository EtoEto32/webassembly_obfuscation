"""Quantify static feature changes; never claim detector accuracy or execute Wasm."""
import csv
import json
from pathlib import Path
from evaluate_local_normalization import ROOT, sha


def category(op):
    if op in {'block', 'loop', 'if', 'else', 'end', 'br', 'br_if', 'br_table', 'return', 'unreachable'}:
        return 'control'
    if op.startswith(('call', 'return_call')):
        return 'calls'
    if '.load' in op or '.store' in op or op.startswith(('memory.', 'table.')):
        return 'memory_table'
    return 'other'


def main():
    records = []
    for group, filename in [('local-normalization', 'static-comparison.json'),
                            ('transfer', 'comparison.json'),
                            ('seeded-normalization', 'comparison.json')]:
        rows = json.loads((ROOT/'results/countermeasures'/group/filename).read_text(encoding='utf-8'))['records']
        for row in rows:
            original = next(x for x in rows if x['source'] == row['source'] and x['variant'] == 'unmodified')
            for item in (original, row):
                assert sha(ROOT/item['path']) == item['sha256']
            a, b = original['instructions'], row['instructions']
            deltas = {op: b.get(op, 0)-a.get(op, 0) for op in sorted(set(a)|set(b)) if a.get(op, 0) != b.get(op, 0)}
            preserved = {c: not any(category(op) == c for op in deltas) for c in ('control', 'calls', 'memory_table')}
            allowed = {'nop'} if row['variant'] == 'nop' else {
                f'i{width}.{op}' for width in (32, 64) for op in ('const', 'add', 'sub', 'mul', 'and', 'or', 'xor')}
            if row['variant'] == 'both':
                allowed.add('nop')
            if row['variant'] in ('nop', 'integer-fold', 'both'):
                assert all(preserved.values()), (group, row['source'], row['variant'], deltas)
                assert set(deltas) <= allowed, deltas
            old_count, new_count = original['instruction_count'], row['instruction_count']
            records.append(dict(group=group, source=row['source'], variant=row['variant'],
                                original_sha256=original['sha256'], processed_sha256=row['sha256'],
                                nop_before=a.get('nop', 0), nop_after=b.get('nop', 0),
                                nop_presence_removed=a.get('nop', 0) > 0 and b.get('nop', 0) == 0,
                                instruction_count_before=old_count, instruction_count_after=new_count,
                                changed_opcode_counts=deltas, preserved_category_counts=preserved,
                                nop_frequency_before=a.get('nop', 0)/old_count,
                                nop_frequency_after=b.get('nop', 0)/new_count))
    custom = [r for r in records if r['variant'] in ('nop', 'integer-fold', 'both')]
    summary = dict(conditions=len(records), dedicated_conditions=len(custom),
                   dedicated_nop_presence_removed=sum(r['nop_presence_removed'] for r in custom),
                   dedicated_instruction_count_changed=sum(r['instruction_count_before'] != r['instruction_count_after'] for r in custom),
                   dedicated_category_count_changes=sum(not all(r['preserved_category_counts'].values()) for r in custom))
    report = dict(summary=summary, records=records, evaluator_sha256=sha(Path(__file__)),
                  runtime_executed=False, detector_evaluated=False,
                  scope='Counts and normalized NOP frequency only, not full CFG, locations, operand values, semantic invariance or classifier outputs. Original and processed bytes are SHA-linked to saved comparisons. Multiple conditions are not independent programs.')
    out = ROOT/'results/countermeasures/feature-loss'
    out.mkdir(exist_ok=True)
    (out/'comparison.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    with (out/'comparison.csv').open('w', newline='', encoding='utf-8') as f:
        fields = ['group', 'source', 'variant', 'original_sha256', 'processed_sha256', 'nop_before', 'nop_after', 'nop_presence_removed', 'instruction_count_before', 'instruction_count_after', 'nop_frequency_before', 'nop_frequency_after']
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(records)
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
