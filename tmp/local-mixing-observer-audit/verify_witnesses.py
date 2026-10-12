"""Independent Boolean-polynomial replay of the emitted reference gate tape."""
import importlib.util
import json
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / 'local-mixing-source-audit'
for name in ('security_tests', 'security_tests.gadgetization'):
    package = types.ModuleType(name)
    package.__path__ = []
    sys.modules[name] = package
for name, path in [('nonlinear193', 'nonlinear193.py'), ('nonlinear291', 'security_tests__gadgetization__nonlinear291.py')]:
    fullname = 'security_tests.gadgetization.' + name
    spec = importlib.util.spec_from_file_location(fullname, SOURCE / path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[fullname] = module
    spec.loader.exec_module(module)
reference = sys.modules['security_tests.gadgetization.nonlinear291']
circ, info = reference.run_gate(samples=1, seed=71)
assert len(circ.init) == 71 and len(circ.gate_log) == 291
other, _ = reference.run_gate(samples=1, seed=193)
assert circ.gate_log == other.gate_log
(ROOT / 'gate-tape.json').write_text(json.dumps(circ.gate_log), encoding='utf-8')

# From the constructor's explicit clean-scratch contract, not sampled zeroes.
free = list(range(35)) + list(range(40, 44))
state = [{1 << i} if i in free else set() for i in range(71)]
initial = [set(x) for x in state]
products = 0
peak_terms = 0

def mul(a, b):
    global products, peak_terms
    products += len(a) * len(b)
    if products > 10_000_000:
        raise RuntimeError('Symbolic budget exhausted; no proof claimed')
    out = set()
    for x in a:
        for y in b:
            z = x | y
            if z in out:
                out.remove(z)
            else:
                out.add(z)
    peak_terms = max(peak_terms, len(out))
    return out

for target, complement, controls in circ.gate_log:
    product = {0}
    for wire, polarity in controls:
        value = state[wire] if polarity else state[wire] ^ {0}
        product = mul(product, value)
    state[target] ^= product ^ ({0} if complement else set())

def decode(start):
    x = initial[start:start+5]
    return x[0] ^ x[1] ^ mul(x[2], x[3]) ^ mul(x[2], x[4]) ^ mul(x[3], x[4])

a = decode(15) ^ decode(20)
b = decode(25) ^ decode(30)
c = decode(0) ^ decode(5)
gate = {0} ^ b ^ mul(a, b)
expected = dict(a=a, b=b, c_in=c, gate_ab=gate, c_out=c ^ gate)
rows = []
results = json.loads((ROOT / 'results.json').read_text())
for run in results['runs']:
    targets = run['conditions']['encoded_final_quadratic']['targets']
    for name, want in expected.items():
        actual = set()
        witness = targets[name]['witness']
        for term in witness:
            value = {0}
            if term != '1':
                for factor in term.split('&'):
                    value = mul(value, state[int(factor[1:])])
            actual ^= value
        difference = actual ^ want
        rows.append(dict(seed=run['seed'], target=name, difference_terms=len(difference), witness_terms=len(witness)))
        assert not difference, (run['seed'], name)
proof = dict(method='Exact Boolean ANF replay; x*x=x; XOR as symmetric difference',
    free_input_wires=free, fixed_zero_wires=[i for i in range(71) if i not in free],
    free_bits=len(free), same_gate_tape_for_both_seeds=True,
    proofs=rows, multiplication_term_pairs=products, largest_product_terms=peak_terms)
(ROOT / 'proofs.json').write_text(json.dumps(proof, indent=2), encoding='utf-8')
print(json.dumps(proof, indent=2))
