"""Recover initialized final-hash table and baseline wrapper argument patterns."""
import hashlib
import json
import re
import struct
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/runtime-mining/cross-dataset/proof-of-theft'
entry = json.loads((OUT / 'cryptonight-entrypoint-review.json').read_text())
rows = []
baseline_functions = None
for row in entry['modules']:
    if 'internal_hash_candidate' not in row:
        continue
    path = ROOT / 'data/objects' / (row['sha256'] + '.bin')
    assert hashlib.sha256(path.read_bytes()).hexdigest() == row['sha256']
    wat = subprocess.check_output([str(ROOT / '.tools/wabt-1.0.42/bin/wasm2wat.exe'),
                                   str(path), '--generate-names'], text=True)
    element = re.search(r'^  \(elem \$e0 \(i32.const (\d+)\) func ([^\n]+)\)', wat, re.M)
    data = re.search(r'^  \(data \$d0 \(i32.const (\d+)\) "([^\n]+)"\)', wat, re.M)
    assert element and data
    first = data[2][:48]
    assert re.fullmatch(r'(?:\\[0-9a-fA-F]{2}){16}', first)
    pointer_bytes = bytes(int(first[i+1:i+3], 16) for i in range(0, 48, 3))
    indices = list(struct.unpack('<4I', pointer_bytes))
    funcs = element[2].split()
    assert int(element[1]) == 1 and indices == [1, 2, 3, 4]
    assert funcs == ['$f20', '$f16', '$f21', '$f22']
    assert int(data[1]) == 536870912
    rows.append(dict(method=row['method'], sha256=row['sha256'],
        initialized_pointer_array_address=int(data[1]), initialized_table_indices=indices,
        initialized_table_targets=funcs, element_declaration=element[0],
        pointer_bytes_hex=pointer_bytes.hex(),
        limitation='Initialization mapping only; absence of later memory/table writes or runtime target changes is not established.'))
    if row['method'] == 'cryptonight-hash':
        baseline_functions = {name: body for body, name in re.findall(
            r'^  (\(func (\$[^\s()]+).*?)(?=\n  \(|\Z)', wat, re.M | re.S)}

source = entry['modules'][0]['sources']['cryptonightnative.c']
source_text = (ROOT / source['saved']).read_text()
assert 'blake256_hash((uint8_t*)output, input, len);' in source_text
assert 'groestl(input, len * 8, (uint8_t*)output);' in source_text
assert 'jh_hash(HASH_SIZE * 8, input, 8 * len, (uint8_t*)output);' in source_text
assert 'c_skein_hash(8 * HASH_SIZE, input, 8 * len, (uint8_t*)output);' in source_text

wrappers = []
specs = [('$f20', 'do_blake_hash', '$f31', ['output', 'input', 'byte length']),
         ('$f16', 'do_groestl_hash', '$f32', ['input', '8 * byte length', 'output']),
         ('$f21', 'do_jh_hash', '$f41', [256, 'input', '8 * byte length', 'output']),
         ('$f22', 'do_skein_hash', '$f50', [256, 'input', '8 * byte length', 'output'])]
for name, source_name, callee, expected in specs:
    body = baseline_functions[name]
    ls = [s.strip() for s in body.splitlines()[2:]]
    # A straight-line symbolic prefix, stopped BEFORE the algorithm call. No Wasm runs.
    stack = []; locals_ = {'$p0': 'input', '$p1': 'byte length', '$p2': 'output'}
    memory = {}; globals_ = {'$g0': 'entry stack'}; actual = None
    for instruction in ls:
        op, *args = instruction.split()
        if op == 'global.get': stack.append(globals_[args[0]])
        elif op == 'global.set': globals_[args[0]] = stack.pop()
        elif op == 'local.get': stack.append(locals_[args[0]])
        elif op == 'local.set': locals_[args[0]] = stack.pop()
        elif op == 'i32.const': stack.append(int(args[0]))
        elif op in ['i32.add', 'i32.sub']:
            b = stack.pop(); a = stack.pop(); stack.append((op, a, b))
        elif op == 'i32.store':
            value = stack.pop(); address = stack.pop()
            offset = int(args[0].split('=')[1]) if args else 0
            memory[(address, offset)] = value
        elif op == 'i32.load':
            address = stack.pop(); offset = int(args[0].split('=')[1]) if args else 0
            stack.append(memory[(address, offset)])
        elif op == 'i32.shl':
            bits = stack.pop(); value = stack.pop()
            assert value == 'byte length' and bits == 3
            stack.append('8 * byte length')
        elif op == 'i64.extend_i32_u': pass
        elif op == 'call':
            assert args[0] == callee
            actual = stack[:]
            break
        else: raise AssertionError(instruction)
    assert actual == expected, (name, actual)
    saved = OUT / f'cryptonight-baseline-final-{name[1:]}.wat.txt'
    saved.write_text(body + '\n')
    wrappers.append(dict(function=name, source_wrapper=source_name, direct_callee=callee,
        statically_forwarded_arguments=actual, saved_excerpt=str(saved.relative_to(ROOT)),
        excerpt_sha256=hashlib.sha256(saved.read_bytes()).hexdigest(),
        scope='Exact baseline straight-line forwarding up to the first call; source correspondence supported by argument order, length conversion, digest size and table order. Callee algorithm bodies not proved equivalent.'))
report = dict(date='2026-10-08', initialized_tables=rows, baseline_wrappers=wrappers,
    source=source, conclusion='Baseline and five transformed modules initialize the same four function-table destinations. Baseline wrappers forward arguments consistently with the four final hash wrappers in the distributed source. Natural algorithm finalization must be distinguished from obfuscating indirection.',
    limitations=['This static prefix analysis does not execute hash algorithms, prove whole-module equivalence, or validate output.',
                 'Transformed wrapper payloads and complete underlying cryptographic callee bodies are not covered by the baseline prefix analysis.',
                 'Initialization equality is not a proof that table entries or pointer arrays remain unchanged throughout execution.'],
    executed_hashes=0)
(OUT / 'cryptonight-final-table-review.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(dict(table_initializations=len(rows), baseline_wrapper_prefixes=len(wrappers), executed_hashes=0)))
