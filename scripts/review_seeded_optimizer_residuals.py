"""Review stored static opcode differences; never execute mining modules."""
import json
from pathlib import Path
from evaluate_local_normalization import ROOT,sha


def main():
    directory=ROOT/'results/countermeasures/seeded-normalization'
    source=directory/'comparison.json';rows=json.loads(source.read_text(encoding='utf-8'))['records'];records=[]
    for row in rows:
        if row['method']!='nop' or not row['variant'].startswith('binaryen'):
            continue
        baseline=next(r for r in rows if r['source']=='baseline' and r['variant']==row['variant'])
        difference={op:row['instructions'].get(op,0)-baseline['instructions'].get(op,0)
                    for op in baseline['instructions'].keys()|row['instructions'].keys()
                    if row['instructions'].get(op,0)!=baseline['instructions'].get(op,0)}
        records.append(dict(source=row['source'],variant=row['variant'],nop_count=row['instructions'].get('nop',0),
                            reference_nop_count=baseline['instructions'].get('nop',0),opcode_differences=difference,
                            instruction_difference=row['instruction_difference_to_processed_reference'],
                            byte_difference=row['byte_difference_to_processed_reference']))
    result=dict(records=records,comparison_sha256=sha(source),evaluator_sha256=sha(Path(__file__)),runtime_executed=False,
                interpretation='NOP count is zero in all optimized NOP controls. Remaining byte/instruction differences concern other optimizer output, not a demonstrated failure to remove NOP.',
                limitation='Does not identify the responsible optimizer pass or prove output equivalence or speed effects.')
    (directory/'optimizer-residual-review.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(dict(optimized_nop_cases=len(records),all_zero_nops=all(r['nop_count']==0 for r in records))))


if __name__=='__main__':
    main()
