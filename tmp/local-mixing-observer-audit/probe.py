"""Supervised representation diagnostic; not a blind deobfuscation attack."""
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import sys
import time
import types
import numpy as np

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / 'local-mixing-source-audit'
for entry in json.loads((SOURCE / 'source-verification.json').read_text()):
    assert hashlib.sha256((SOURCE / entry['local']).read_bytes()).hexdigest() == entry['sha256']
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

TRAIN, TEST = 4096, 8192

def packed(a):
    return int.from_bytes(np.packbits(a, bitorder='little').tobytes(), 'little')

def fit(features, labels):
    """Exact GF(2) column elimination. Input includes TRAIN samples only."""
    basis = {}
    for i, vector in enumerate(features):
        value, expression = packed(vector), 1 << i
        while value:
            pivot = value.bit_length() - 1
            if pivot not in basis:
                basis[pivot] = (value, expression)
                break
            old, rep = basis[pivot]
            value ^= old
            expression ^= rep
    witnesses = []
    for target in labels:
        value, expression = packed(target), 0
        while value:
            pivot = value.bit_length() - 1
            if pivot not in basis:
                expression = None
                break
            old, rep = basis[pivot]
            value ^= old
            expression ^= rep
        witnesses.append(None if expression is None else [i for i in range(len(features)) if expression >> i & 1])
    return len(basis), witnesses

def features_for(wires, degree):
    features = [np.ones(len(wires[0]), np.uint8)] + list(wires)
    names = ['1'] + [f'w{i}' for i in range(len(wires))]
    if degree == 2:
        for i in range(len(wires)):
            for j in range(i):
                features.append(wires[i] & wires[j])
                names.append(f'w{i}&w{j}')
    return np.array(features), names

def audit(wires, degree, labels, names):
    features, feature_names = features_for(wires, degree)
    start = time.perf_counter()
    rank, witnesses = fit(features[:, :TRAIN], labels[:, :TRAIN])
    elapsed = time.perf_counter() - start
    out = dict(features=len(features), rank=rank, fit_seconds=elapsed, targets={})
    for name, expected, witness in zip(names, labels, witnesses):
        if witness is None:
            out['targets'][name] = dict(train_fit=False)
        else:
            actual = np.bitwise_xor.reduce(features[witness], axis=0) if witness else np.zeros(TRAIN + TEST, np.uint8)
            train_errors = int(np.count_nonzero(actual[:TRAIN] != expected[:TRAIN]))
            assert train_errors == 0
            out['targets'][name] = dict(train_fit=True, train_errors=train_errors,
                test_errors=int(np.count_nonzero(actual[TRAIN:] != expected[TRAIN:])),
                witness=[feature_names[i] for i in witness])
    return out

results = dict(scope='single unmixed canonical reference gadget; supervised labels',
    source_commit='5ce6daab669f50665f0c9aecf958f4066f407d01',
    python=platform.python_version(), numpy=np.__version__, train=TRAIN, test=TEST, runs=[])
if (ROOT / 'results.json').exists():
    raise SystemExit('Refusing to overwrite existing results')
for seed in (71, 193):
    circ, info = reference.run_gate(samples=TRAIN + TEST, seed=seed)
    assert info['correct'] and info['required_ancillas_restored']
    names = ['a', 'b', 'c_in', 'gate_ab', 'c_out', 'independent_noise']
    labels = np.array([info[name] for name in names[:-1]] + [np.random.default_rng(seed + 9000).integers(0, 2, TRAIN + TEST, dtype=np.uint8)])
    initial, final, flips = map(np.array, (circ.init, circ.s, circ.flips))
    np.savez_compressed(ROOT / f'observations-{seed}.npz', initial=initial, final=final, flips=flips, labels=labels)
    run = dict(seed=seed, wires=len(circ.init), gates=len(circ.gate_log), conditions={})
    conditions = [
        ('plain_affine', [info['a'], info['b'], info['c_in'], info['c_out']], 1),
        ('encoded_final_affine', final, 1),
        ('encoded_fulltrace_affine', np.concatenate([initial, flips]), 1),
        ('encoded_final_quadratic', final, 2),
    ]
    for name, wires, degree in conditions:
        run['conditions'][name] = audit(wires, degree, labels, names)
        print(seed, name, {k: v.get('test_errors', 'no fit') for k, v in run['conditions'][name]['targets'].items()}, flush=True)
    results['runs'].append(run)
(ROOT / 'results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
