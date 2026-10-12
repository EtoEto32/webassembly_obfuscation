"""Trace saved straight-line f35 WAT with symbolic parameter values; no Wasm execution.

The callee is an uninterpreted void call. Its global state is deliberately
unknown afterwards. This is a bounded wrapper dataflow review, not hashing,
runtime profiling, or a whole-program equivalence proof.
"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/runtime-mining/cross-dataset/proof-of-theft'
G = 65536  # A nonwrapping, aligned coordinate for relative stack addresses.


def trace(name):
    path = OUT / f'xmr-{name}-f35-complete.wat.txt'
    text = path.read_text()
    full = (OUT / f'xmr-{name}.wat').read_text()
    assert text.rstrip() in full, 'Excerpt must match saved module verbatim.'
    assert re.search(r'\(func \$f111 .*?\(param \$p5 i64\)', full)
    header = text.splitlines()[0]
    assert re.findall(r'\(param (\$p\d+) (i32|i64)\)', header) == [
        ('$p0', 'i32'), ('$p1', 'i32'), ('$p2', 'i32'),
        ('$p3', 'i32'), ('$p4', 'i64')]
    stack, memory, writes, loads, updates, calls = [], {}, [], [], [], []
    locals_ = {f'$p{i}': f'p{i}' for i in range(5)}
    global_ = G
    for line_no, line in enumerate(text.splitlines()[2:], 3):
        instruction = line.strip().removesuffix(')')
        if not instruction:
            continue
        parts = instruction.split()
        op = parts[0]
        if op == 'global.get':
            assert parts[1] == '$g0'
            stack.append(global_)
        elif op == 'global.set':
            assert parts[1] == '$g0'
            global_ = stack.pop()
            updates.append(dict(line=line_no, relative_to_entry_global=global_ - G))
        elif op == 'local.get':
            stack.append(locals_[parts[1]])
        elif op == 'local.set':
            locals_[parts[1]] = stack.pop()
        elif op == 'i32.const':
            stack.append(int(parts[1]))
        elif op in ('i32.add', 'i32.sub'):
            b, a = stack.pop(), stack.pop()
            assert isinstance(a, int) and isinstance(b, int)
            stack.append((a + b if op.endswith('add') else a - b) & 0xffffffff)
        elif op in ('i32.store', 'i64.store', 'i32.load', 'i64.load'):
            width = 4 if op.startswith('i32') else 8
            offset = int(parts[1].split('=')[1]) if len(parts) > 1 else 0
            if op.endswith('store'):
                value = stack.pop()
                address = stack.pop() + offset
                assert not any(address + j in memory for j in range(width))
                for j in range(width):
                    memory[address + j] = (value, j, width)
                writes.append(dict(line=line_no, value=value, bytes=width,
                                   address_relative_to_entry_global=address - G))
            else:
                address = stack.pop() + offset
                value = memory[address][0]
                assert all(memory[address + j] == (value, j, width) for j in range(width))
                stack.append(value)
                loads.append(dict(line=line_no, value=value,
                                  address_relative_to_entry_global=address - G))
        elif op == 'call':
            assert parts[1] == '$f111' and len(stack) == 6
            calls.append(dict(line=line_no, callee=parts[1], arguments=stack[:],
                              global_relative_to_entry=global_ - G))
            stack.clear()
            global_ = 'unknown_after_uninterpreted_callee'
        elif op == 'return':
            assert not stack
        else:
            raise AssertionError(f'Unsupported instruction at {line_no}: {instruction}')
    assert len(calls) == 1 and calls[0]['arguments'] == ['p0', 'p1', 'p2', 'p3', 0, 'p4']
    assert global_ == G and len(writes) == len(loads) == 5
    return dict(variant=name, excerpt=str(path),
                excerpt_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                module_sha256=hashlib.sha256((OUT / f'xmr-{name}.wat').read_bytes()).hexdigest(),
                global_updates=updates, stores=writes, loads=loads, calls=calls,
                entry_global_restored_after_unknown_callee_global=True)


rows = [trace('original'), trace('split')]
assert [x['relative_to_entry_global'] for x in rows[0]['global_updates']] == [-32, 0]
assert [x['relative_to_entry_global'] for x in rows[1]['global_updates']] == [-16, -32, -48, 0]
assert [x['address_relative_to_entry_global'] for x in rows[0]['stores']] == [-4, -8, -12, -16, -24]
assert [x['address_relative_to_entry_global'] for x in rows[1]['stores']] == [-4, -8, -12, -32, -48]
report = dict(scope='Saved f35 straight-line wrapper dataflow only; symbolic parameters and a nonwrapping stack coordinate. No hashing or Wasm execution.',
              reviewed_functions=rows,
              findings=['Reference reserves 32 bytes in one update; split-setting wrapper reserves 48 bytes in three 16-byte updates.',
                        'p0/p1/p2 store addresses match; p3/p4 store addresses differ.',
                        'Both wrappers forward p0,p1,p2,p3,0,p4 to f111 and restore the entry global after return.',
                        'No branch, loop, dispatcher, indirect call, or additional callee appears in these wrappers.'],
              interpretation='Observed stack-frame allocation/layout change; insufficient to confirm basic-block or function splitting as an obfuscation mechanism.',
              limitations=['The callee is not evaluated; its visible stack pointer differs between wrappers.',
                           'Changed memory writes, aliases, callees, and other functions prevent a whole-program equivalence claim.',
                           'No dynamic path coverage, instruction timing, or causal explanation of measured throughput.'])
(OUT / 'xmr-split-wrapper-review.json').write_text(json.dumps(report, indent=2) + '\n')
print('Two saved wrappers traced: allocation 32 -> 48 bytes; forwarded arguments and restoration match. Splitting mechanism remains unconfirmed.')
