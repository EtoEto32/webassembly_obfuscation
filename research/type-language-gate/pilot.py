"""Bounded research probe of published type recovery; not an obfuscator."""
import argparse
import collections
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
PYTHON = ROOT / '.tools/retypd-python/Scripts/python.exe'
SOURCE = ROOT / '.tools/retypd-source'


def load_retypd():
    spec = importlib.util.spec_from_file_location('retypd', SOURCE / 'src/__init__.py',
                                                submodule_search_locations=[str(SOURCE / 'src')])
    mod = importlib.util.module_from_spec(spec)
    sys.modules['retypd'] = mod
    spec.loader.exec_module(mod)
    return mod


def family(n, control=False):
    # Read capabilities are covariant. No stores or input type contradictions.
    cs = ['F.in_0 <= q0', 'q0.load.sigma4@0 <= q0', 'q0.load.sigma4@4 <= q0']
    if not control:
        cs.append('q0.load.sigma4@4 <= q1')
        for i in range(1, n):
            for off in (0, 4):
                cs.append(f'q{i}.load.sigma4@{off} <= q{i+1}')
        cs.append(f'q{n}.load.sigma4@8 <= int')
    else:
        cs.append('q0.load.sigma4@8 <= int')
    cs.append('int <= F.out')
    return [c.replace('<=', '\u2291').replace('sigma', '\u03c3') for c in cs]


def automaton(n):
    todo = collections.deque([frozenset([0])])
    seen = set(todo)
    while todo:
        state = todo.popleft()
        for bit in (0, 1):
            target = {0}
            target.update(i + 1 for i in state if 0 < i < n)
            if bit:
                target.add(1)
            target = frozenset(target)
            if target not in seen:
                seen.add(target)
                todo.append(target)
    assert len(seen) == 2**n
    return len(seen)


def worker(n, mode, control, supplied=None):
    r = load_retypd()
    from retypd.fast_enfa import FastENFA
    # Measure existing determinization calls, without altering their results.
    events = []
    original = FastENFA.to_deterministic
    def observed(self, *args, **kwargs):
        start = time.perf_counter()
        result = original(self, *args, **kwargs)
        events.append({'nfa_states': len(self.states), 'dfa_states': len(result.states),
                       'ms': (time.perf_counter() - start) * 1000})
        return result
    FastENFA.to_deterministic = observed
    texts = family(n, control) if supplied is None else supplied
    constraints = r.SchemaParser.parse_constraint_set(texts)
    f = r.DerivedTypeVariable('F')
    start = time.perf_counter()
    solver = r.Solver(r.Program(r.DummyLattice(), set(), {f: constraints}, {f: []}),
                      config=r.SolverConfig(graph_solver=mode))
    generated, sketches = solver()
    elapsed = (time.perf_counter() - start) * 1000
    # Public result and stable printable constraints, not private algorithm assumptions.
    sketch = sketches[f]
    g = sketch.sketches
    return {'n': n, 'mode': mode, 'control': control, 'status': 'ok',
            'input_constraints': len(constraints), 'solver_ms': elapsed,
            'output_constraints': sorted(str(c) for c in generated[f]),
            'sketch_nodes': len(g.nodes), 'sketch_edges': len(g.edges),
            'determinization': events, 'constraints': texts}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--worker', type=int)
    p.add_argument('--mode', choices=['dfa', 'pathexpr'], default='dfa')
    p.add_argument('--control', action='store_true')
    p.add_argument('--constraints', type=Path)
    p.add_argument('out', nargs='?')
    args = p.parse_args()
    if args.worker is not None:
        if not 1 <= args.worker <= 8:
            raise ValueError('bounded pilot: n=1..8')
        supplied = json.loads(args.constraints.read_text(encoding='utf-8')) if args.constraints else None
        print(json.dumps(worker(args.worker, args.mode, args.control, supplied), ensure_ascii=True))
        return
    if not args.out:
        p.error('output directory required')
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=False)
    rows = []
    for control, ns in ((True, [1]), (False, range(1, 9))):
        for n in ns:
            for mode in ('dfa', 'pathexpr'):
                cmd = [str(PYTHON), str(Path(__file__).resolve()), '--worker', str(n), '--mode', mode]
                if control:
                    cmd.append('--control')
                try:
                    env = dict(os.environ, PYTHONHASHSEED='0', PYTHONIOENCODING='utf-8')
                    run = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8',
                                         timeout=30, env=env)
                    name = f'{"control" if control else "probe"}-{n}-{mode}'
                    (out / f'{name}.stdout.txt').write_text(run.stdout, encoding='utf-8')
                    (out / f'{name}.stderr.txt').write_text(run.stderr, encoding='utf-8')
                    row = json.loads(run.stdout) if run.returncode == 0 else {
                        'n': n, 'mode': mode, 'control': control,
                        'status': 'error', 'exit_code': run.returncode}
                except subprocess.TimeoutExpired:
                    row = {'n': n, 'mode': mode, 'control': control, 'status': 'timeout'}
                rows.append(row)
                print(json.dumps({k: row.get(k) for k in ('n', 'mode', 'control', 'status', 'solver_ms', 'sketch_nodes')}), flush=True)
                # Stop on interface failure rather than collect meaningless repetitions.
                if row['status'] == 'error':
                    break
            if rows[-1]['status'] == 'error':
                break
        if rows[-1]['status'] == 'error':
            break
    result = {'scope': 'constraints only; not NotDec or a Wasm frontend',
              'retpy_commit': subprocess.check_output(['git', '-C', str(SOURCE), 'rev-parse', 'HEAD'], text=True).strip(),
              'abstract_nfa': [{'n': n, 'dfa_states': automaton(n)} for n in range(1, 9)],
              'rows': rows, 'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (out / 'result.json').write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    freeze = subprocess.check_output([str(PYTHON), '-m', 'pip', 'freeze'], text=True)
    (out / 'requirements-freeze.txt').write_text(freeze, encoding='utf-8')


if __name__ == '__main__':
    main()
