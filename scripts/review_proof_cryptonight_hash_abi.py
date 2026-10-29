"""Check partial hash ABI and natural finalization evidence without execution."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/runtime-mining/cross-dataset/proof-of-theft'
entry = json.loads((OUT / 'cryptonight-entrypoint-review.json').read_text())
layouts = {
    'cryptonight-hash': (2097596, 2097592, 2097588),
    'cryptonight-hash-emccobf-substitution': (2097596, 2097592, 2097588),
    'cryptonight-hash-emccobf-split': (28, 24, 20),
    'cryptonight-hash-emccobf-flattening': (2097612, 2097608, 2097604),
    'cryptonight-hash_fsplitflatten': (2097596, 2097592, 2097588),
}
records = []
for row in entry['modules']:
    if row['method'] not in layouts:
        continue
    body = row['inspected_functions'][-1]
    assert body['function'] == '$f10'
    text = (ROOT / body['excerpt']).read_text()
    lines = text.splitlines()
    instructions = [s.strip() for s in lines[2:]]
    slots = layouts[row['method']]
    stores = []
    for i, slot in enumerate(slots):
        pattern = rf'local\.get (\$l\d+)\n\s*local\.get \$p{i}\n\s*i32\.store offset={slot}\b'
        matches = list(re.finditer(pattern, text))
        assert len(matches) == 1
        match = matches[0]
        stores.append(dict(parameter=f'$p{i}', role=['input pointer', 'output pointer', 'input length'][i],
            stack_base=match[1], byte_offset=slot,
            source_line=text[:match.start()].count('\n') + 1, instructions=match[0]))
    assert len({s['stack_base'] for s in stores}) == 1
    first_call = next(i for i, s in enumerate(instructions) if s.startswith('call '))
    prefix = instructions[:first_call + 1]
    # Straight-line prefix loads the saved input and length before the first call.
    loadlocals = []
    for slot in [slots[0], slots[2]]:
        at = prefix.index(f'i32.load offset={slot}')
        assert prefix[at + 1].startswith('local.set ')
        loadlocals.append(prefix[at + 1].split()[1])
    assert prefix[-3:-1] == [f'local.get {loadlocals[0]}', f'local.get {loadlocals[1]}']
    indirects = [i for i, s in enumerate(instructions) if s.startswith('call_indirect ')]
    assert len(indirects) == 1
    at = indirects[0]
    output_load = max(i for i, s in enumerate(instructions[:at]) if s == f'i32.load offset={slots[1]}')
    outlocal = instructions[output_load + 1].split()[1]
    assert instructions[output_load + 1] == f'local.set {outlocal}'
    assert instructions[at - 2] == f'local.get {outlocal}'
    assert instructions[at - 4].startswith('local.get ')
    assert instructions[at - 3].startswith('local.get ')
    assert instructions[at - 1].startswith('local.get ')
    lengthlocal = instructions[at - 3].split()[1]
    assert instructions[output_load + 2:output_load + 4] == ['i32.const 200', f'local.set {lengthlocal}']
    selection = instructions[max(0, at - 90):at + 1]
    assert 'i32.const 3' in selection and 'i32.and' in selection
    records.append(dict(method=row['method'], sha256=row['sha256'], function='$f10',
        evidence_excerpt=body['excerpt'], excerpt_sha256=body['excerpt_sha256'],
        parameter_storage=stores, first_call=prefix[-1],
        input_length_forwarding=prefix[-12:],
        final_call_arguments=['internal state pointer', '200 bytes', 'saved output pointer', 'table index'],
        final_selection_instructions=selection,
        confidence='Partial static interface evidence; intervening slot preservation and complete callee/data/table semantics are not proven. No hash output was computed.'))
source = entry['modules'][0]['sources']['cryptonightnative.c']
text = (ROOT / source['saved']).read_text()
assert 'extra_hashes[ctx->state.hs.b[0] & 3](&ctx->state, 200, output);' in text
assert 'static void (* const extra_hashes[4])' in text
assert all(f'do_{n}_hash' in text for n in ['blake', 'groestl', 'jh', 'skein'])
report = dict(date='2026-10-08', modules=records, source=source,
    ordinary_finalization_control=dict(
        source_expression='extra_hashes[ctx->state.hs.b[0] & 3](&ctx->state, 200, output)',
        source_functions=['do_blake_hash', 'do_groestl_hash', 'do_jh_hash', 'do_skein_hash'],
        interpretation='The baseline already uses a state-dependent four-way final hash selection. An indirect call plus bitwise masking alone does not establish obfuscating call indirection or virtualization.',
        scope='Distributed source plus five candidate functions have consistent partial interface patterns; complete table-target recovery and source/binary equivalence remain unverified.'),
    unreviewed=['boguscf candidate has duplicated control paths and needs separate parameter/dataflow recovery',
                'encodearith has a different main/call organization; no f10 mapping is assumed'],
    next_step='After university execution permission, validate any export-only derivative against independent public vectors before timing; preserve original binary SHA and separately report the derivative SHA.',
    executed_hashes=0)
(OUT / 'cryptonight-hash-abi-review.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(dict(partial_abi_reviews=len(records), executed_hashes=0)))
