"""Review saved XOR helpers' scratch layout and structured branches; no execution."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/runtime-mining/cross-dataset/proof-of-theft'


def extract(module, function):
    fields = list(re.finditer(r'^  \(', module, re.M))
    for i, match in enumerate(fields):
        end = fields[i+1].start() if i+1 < len(fields) else len(module)
        body = module[match.start():end].rstrip()
        if body.startswith(f'  (func ${function} '):
            return body
    raise AssertionError(function)


def review(variant, function, bound):
    module_path = OUT / f'xmr-{variant}.wat'
    body = extract(module_path.read_text(), function)
    path = OUT / f'xmr-{variant}-{function}-split-review.wat.txt'
    path.write_text(body + '\n')
    lines = body.splitlines()
    locals_ = {'$p0': 'p0', '$p1': 'p1'}
    stack, stores, controls, branches = [], [], [], []
    prefix = True
    for number, line in enumerate(lines[2:], 3):
        words = line.strip().removesuffix(')').split()
        if not words:
            continue
        op = words[0]
        if op in ('block', 'loop'):
            prefix = False
            controls.append(dict(kind=op, label=words[1], line=number))
        elif op == 'end':
            assert controls
            controls.pop()
        elif op in ('br', 'br_if'):
            target = next(c for c in reversed(controls) if c['label'] == words[1])
            branches.append(dict(line=number, operation=op, target=target.copy(),
                                 enclosing=[c.copy() for c in controls]))
        if not prefix:
            continue
        if op == 'global.get':
            assert words[1] == '$g0'
            stack.append(65536)
        elif op == 'local.set':
            locals_[words[1]] = stack.pop()
        elif op == 'local.get':
            stack.append(locals_[words[1]])
        elif op == 'i32.const':
            stack.append(int(words[1]))
        elif op in ('i32.add', 'i32.sub'):
            b, a = stack.pop(), stack.pop()
            stack.append((a+b if op == 'i32.add' else a-b) & 0xffffffff)
        elif op == 'i32.store':
            value, base = stack.pop(), stack.pop()
            offset = int(words[1].split('=')[1]) if len(words) > 1 else 0
            stores.append(dict(line=number, value=value, address_relative_to_entry_global=base+offset-65536))
        else:
            raise AssertionError(f'Unexpected prefix operation: {op}')
    assert not stack and not controls and len(stores) == 3
    assert [s['value'] for s in stores] == ['p0', 'p1', 0]
    assert [b['operation'] for b in branches] == ['br_if', 'br']
    assert 'global.set' not in body and 'call ' not in body
    assert len(re.findall(r'\bi32\.xor\b', body)) == 1
    assert len(re.findall(r'\bi32\.load8_u\b', body)) == 2
    assert len(re.findall(r'\bi32\.store8\b', body)) == 1
    assert f'i32.const {bound}\n' in body
    assert re.search(r'i32\.const 1\n\s+local.set \$\w+\n\s+local.get \$\w+\n\s+local.get \$\w+\n\s+i32.add', body)
    if variant == 'original':
        assert [c['kind'] for c in branches[0]['enclosing']] == ['block', 'loop']
        assert branches[0]['target']['kind'] == 'block'
        assert re.search(r'br \$L1\n\s+end\n\s+unreachable\n\s+end\n\s+return\)', body)
    else:
        assert [c['kind'] for c in branches[0]['enclosing']] == ['loop', 'block']
        assert branches[0]['target']['kind'] == 'block'
        assert re.search(r'br \$L0\n\s+end\n\s+end\n\s+return\)', body)
    return dict(variant=variant, function=function, excerpt=str(path),
                excerpt_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                module_sha256=hashlib.sha256(module_path.read_bytes()).hexdigest(),
                scratch_initialization=stores, branches=branches,
                manually_reviewed_loop=dict(bound=bound, increment=1,
                  payload='p0[i] = p0[i] XOR p1[i], byte store',
                  condition='unsigned i < bound',
                  control='On false, exit the block and return; on true, update byte/index and branch to the loop.'))


rows = [review(v, f, n) for f, n in [('f112', 8), ('f118', 16)] for v in ['original', 'split']]
assert [[s['address_relative_to_entry_global'] for s in r['scratch_initialization']] for r in rows] == [
    [-4, -8, -12], [-4, -8, -32], [-4, -8, -12], [-4, -32, -48]]
report = dict(scope='Static scratch-address prefix and structured branch targets in saved f112/f118; no Wasm, hashing, or helper payload execution.',
              functions=rows,
              findings=['Both helpers retain two pointer parameters and their byte-XOR loop with bounds 8/16 and increment 1.',
                        'Reference uses an outer block containing a loop; split-setting version uses a loop containing the exit block.',
                        'The false predicate reaches return in both layouts; the true path returns to the loop after payload and increment.',
                        'Scratch locations differ without updating the global stack pointer. No new call or dispatcher is introduced here.'],
              interpretation='Corresponding XOR payload with changed scratch layout and structured branch encoding. These observations do not establish the historical LLVM basic-block splitting transformation.',
              limitations=['Wasm block constructs are not LLVM basic blocks; matching their counts does not verify a split pass.',
                           'Changing scratch addresses can affect aliasing; no universal semantic-equivalence claim.',
                           'Full f111 transformations, compiler provenance, dynamic execution counts, and performance causality remain unresolved.'])
(OUT / 'xmr-split-helper-review.json').write_text(json.dumps(report, indent=2) + '\n')
print('Four helper bodies reviewed: same XOR loop bounds and branch roles, changed scratch layout and structured branch nesting; no execution.')
