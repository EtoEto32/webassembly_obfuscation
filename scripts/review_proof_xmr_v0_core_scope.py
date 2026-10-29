"""Separate guarded instruction-text growth from v0 core text; no execution."""
import hashlib
import json
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'results/runtime-mining/cross-dataset/proof-of-theft'
records={};normalized={};types_by_name={}
for variant in ['original','flattening']:
    text=(P/f'xmr-{variant}-f111-complete.wat.txt').read_text()
    ls=text.splitlines();stack=[];end=None
    for i,l in enumerate(ls):
        s=l.strip()
        if s.startswith(('block ','loop ','if ')):stack.append((s.split()[1],i))
        elif s=='end':
            label,start=stack.pop()
            if start==2417:
                assert label=='$B26';end=i
    assert end is not None
    assert [x.strip() for x in ls[2398:2421]]==[
        x.strip() for x in (P/'xmr-original-f111-complete.wat.txt').read_text().splitlines()[2398:2421]]
    # Keep the guard and matching outer end; remove payload after br_if through its end.
    outside=ls[2:2421]+ls[end:]
    names={}
    pattern=r'\$(?:l|B|L)\d+'
    norm=[re.sub(pattern,lambda m:names.setdefault(m[0],f'$N{len(names)}'),l.strip()) for l in outside]
    local_types=dict(re.findall(r'\(local (\$l\d+) (i32|i64|f32|f64)\)',ls[1]))
    types_by_name[variant]={names[k]:v for k,v in local_types.items() if k in names}
    normalized[variant]=norm
    records[variant]=dict(function_excerpt_sha256=hashlib.sha256(text.encode()).hexdigest(),
        body_text_lines=len(ls)-2,guard_block_lines=[2418,end+1],
        skipped_payload_lines=[2422,end],skipped_payload_text_lines=end-2421,
        retained_text_lines=len(outside),declared_locals=len(local_types),
        normalized_retained_sha256=hashlib.sha256(('\n'.join(norm)+'\n').encode()).hexdigest())
assert normalized['original']==normalized['flattening']
assert types_by_name['original']==types_by_name['flattening']
delta=records['flattening']['body_text_lines']-records['original']['body_text_lines']
assert delta==9428
assert delta==records['flattening']['skipped_payload_text_lines']-records['original']['skipped_payload_text_lines']
report=dict(function='$f111',variants=records,body_text_growth=delta,
    retained_opcode_operand_dataflow_and_local_types_match=True,
    rule='Exclude only instructions after variant>=4 br_if until the matching block end. Rename locals and branch labels consistently by first occurrence, preserving numeric operands and other identifiers.',
    interpretation='All net instruction-text growth in this function is in a path excluded by recorded v0 inputs. Retained text and referenced local types correspond. Changed helper bodies and unreviewed module state can still affect runtime.',
    limitations=['WABT instruction-text line counts, not dynamically executed instruction counts or encoded byte sizes.',
                 'Not a proof of whole-module equivalence, full v0 reachability, or absence of runtime effects.',
                 'Local declarations grow and compiled code layout/JIT behavior may differ; these effects are unmeasured.',
                 'No hashing, instrumentation, or new throughput measurement.'])
(P/'xmr-v0-core-scope-review.json').write_text(json.dumps(report,indent=2)+'\n')
print('f111 net text growth9428 lies in excluded v4 payload; retained3609 lines and local types match after renaming.')
