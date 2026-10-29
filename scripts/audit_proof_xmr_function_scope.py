"""Compare saved WAT function bodies; never execute a miner or compile a binary."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/runtime-mining/cross-dataset/proof-of-theft'

def functions(text):
    # WABT's saved disassembly places each module field on a two-space line.
    fields = list(re.finditer(r'^  \(', text, re.M))
    result = {}
    for i, field in enumerate(fields):
        end = fields[i + 1].start() if i + 1 < len(fields) else len(text)
        body = text[field.start():end].rstrip()
        match = re.match(r'  \(func (\$[^\s()]+)', body)
        if match:
            result[match[1]] = body
    return result

texts = {name: (OUT / f'xmr-{name}.wat').read_text() for name in
         ('original', 'flattening', 'substitution', 'split')}
parsed = {name: functions(text) for name, text in texts.items()}
reference = parsed['original']
assert '$f111' in reference and '$hash' in reference
rows = []
for name, funcs in parsed.items():
    shared = sorted(set(reference) & set(funcs))
    unchanged = [f for f in shared if reference[f] == funcs[f]]
    selected = {}
    for f in ('$hash', '$f35', '$f111'):
        body = funcs.get(f)
        if body is None:
            continue
        calls = sorted(set(re.findall(r'\bcall (\$[^\s()]+)', body)))
        selected[f] = dict(body_sha256=hashlib.sha256(body.encode()).hexdigest(),
                           identical_text_to_reference=body == reference.get(f),
                           direct_callees=calls,
                           call_indirect_sites=len(re.findall(r'\bcall_indirect\b', body)),
                           lines=len(body.splitlines()))
        (OUT / f'xmr-{name}-{f[1:]}-complete.wat.txt').write_text(body + '\n')
    rows.append(dict(variant=name,wat_sha256=hashlib.sha256(texts[name].encode()).hexdigest(),
                     function_count=len(funcs),shared_identifiers=len(shared),
                     unchanged_text_count=len(unchanged),unchanged_identifiers=unchanged,
                     changed_identifiers=[f for f in shared if f not in unchanged],
                     selected_functions=selected))
report = dict(modules=rows,
              scope='Exact saved WABT function-text comparison at matching identifiers, with direct call inventory.',
              limitations=['Matching numeric identifiers alone does not establish semantic function correspondence.',
                           'Identical caller text does not prove identical callees, data, tables, or runtime behavior.',
                           'No execution, dynamic path coverage, historical rebuild, or full semantic equivalence proof.'])
(OUT / 'xmr-function-scope-audit.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps([{k: row[k] for k in ('variant','function_count','unchanged_text_count','selected_functions')}
                  for row in rows], indent=2))
