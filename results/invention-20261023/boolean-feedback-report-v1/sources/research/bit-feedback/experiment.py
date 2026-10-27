import argparse
import itertools
import json
from pathlib import Path
import random
import subprocess
import sys
import time
import transform as t
import recover


KERNELS = {
 'arx': '''(local.set 2 (i32.add (local.get 0) (local.get 1)))
 (local.set 2 (i32.xor (i32.rotl (local.get 2) (i32.const 7)) (local.get 0)))
 (local.set 3 (i32.add (local.get 2) (i32.const 2654435769)))
 (local.set 3 (i32.xor (local.get 3) (i32.shr_u (local.get 3) (i32.const 11))))
 (local.set 2 (i32.add (local.get 3) (i32.rotr (local.get 2) (i32.const 13))))
 (i32.xor (i32.rotl (local.get 2) (i32.const 5)) (local.get 3))''',
 'blend': '''(local.set 2 (i32.xor (local.get 0) (i32.shr_u (local.get 1) (i32.const 8))))
 (local.set 3 (i32.and (local.get 2) (i32.const 16711935)))
 (local.set 3 (i32.mul (local.get 3) (i32.const 257)))
 (local.set 2 (i32.or (i32.shl (local.get 2) (i32.const 16)) (i32.shr_u (local.get 3) (i32.const 8))))
 (i32.xor (i32.add (local.get 2) (local.get 1)) (i32.rotr (local.get 3) (i32.const 3)))''',
 'carry': '''(local.set 2 (i32.add (local.get 0) (local.get 1)))
 (local.set 3 (i32.sub (local.get 2) (i32.shl (local.get 0) (i32.const 3))))
 (local.set 2 (i32.xor (local.get 3) (i32.and (local.get 1) (i32.const 2863311530))))
 (local.set 3 (i32.mul (local.get 2) (i32.const 33)))
 (i32.add (i32.xor (local.get 3) (i32.shr_s (local.get 2) (i32.const 9))) (local.get 0))'''
}


def small_checks():
    cases = 0; mismatch = 0; bound_violation = 0
    # Includes shifts against the bit direction, arithmetic carry, arbitrary starts.
    for width in (2, 3, 4):
        nodes = [('add', ('p', 0), ('c', 1)), ('rotr', ('n', 0), ('c', 1)), ('xor', ('n', 1), ('p', 0))]
        for mode in ('none', 'uniform', 'masked'):
            p = t.plan(nodes, mode, width=width, extra_depth=6)
            for x in range(1 << width):
                expected = []
                for node in nodes: expected.append(t.calc(node, expected, [x], width))
                for initial in itertools.product(range(1 << width), repeat=len(nodes)):
                    state = list(initial)
                    for _ in range(p['rounds']):
                        f = [t.calc(node, state, [x], width) for node in nodes]; nxt = list(f)
                        for i, j, k, m in p['feedback']: nxt[i] ^= ((state[j] ^ f[j]) << k) & m
                        state = nxt
                    cases += 1; mismatch += state != expected
    return {'cases': cases, 'mismatches': mismatch}


def run(out):
    if out.exists(): raise ValueError('Refuse overwrite output directory')
    out.mkdir(parents=True); records = []; planning = []; attacks = []
    checks = small_checks(); (out/'small-checks.json').write_text(json.dumps(checks, indent=2))
    if checks['mismatches']: raise AssertionError(checks)
    for kernel, body in KERNELS.items():
        text = '(module (func (export "run") (param i32 i32) (result i32) (local i32 i32) '+body+'))'
        wp = out/(kernel+'-plain.wat'); src = wp.with_suffix('.wasm'); wp.write_text(text)
        t.w.tool('wat2wasm', [wp, '-o', src]); variants = [('plain', src)]
        for mode, seed in [('none', 0), ('uniform', 17), ('masked', 17), ('uniform', 29), ('masked', 29)]:
            tag = mode+str(seed); binary = out/(kernel+'-'+tag+'.wasm')
            p = t.transform(src, binary, mode, seed); planning.append({'kernel':kernel, 'variant':tag, **p})
            variants.append((tag, binary))
            if mode == 'masked':
                match = out/(kernel+'-matched'+str(seed)+'.wasm')
                q = t.transform(src, match, 'none', seed, rounds=p['rounds'])
                planning.append({'kernel':kernel, 'variant':'matched'+str(seed), **q})
                variants.append(('matched'+str(seed), match))
        for tag, raw in variants:
            for opt in ('raw', 'O2', 'O3'):
                binary = raw if opt == 'raw' else out/(raw.stem+'-'+opt+'.wasm')
                if opt != 'raw': t.w.tool('wasm-opt', [raw, '-'+opt, '-o', binary])
                t.w.tool('wasm-validate', [binary])
                rec = {'kernel':kernel, 'variant':tag, 'opt':opt, 'path':str(binary.resolve()), 'bytes':binary.stat().st_size}
                records.append(rec)
                try:
                    recovered = out/(binary.stem+'-recovered.wasm')
                    a = recover.recover(binary, recovered)
                    attacks.append({**rec, **a, 'recovered':str(recovered.resolve())})
                except ValueError as e: attacks.append({**rec, 'status':'unsupported', 'error':str(e)})
                except RuntimeError as e: attacks.append({**rec, 'status':'analysis_failure', 'error':str(e)})
                except Exception as e: attacks.append({**rec, 'status':'crash', 'error':repr(e)})
                print(json.dumps({'case':binary.name, 'attack':attacks[-1]['status']}), flush=True)
    for a in attacks:
        baseline = next(x for x in attacks if x['kernel']==a['kernel'] and x['variant']=='plain' and x['opt']==a['opt'])
        a['same_boolean_dag'] = a.get('digest') == baseline.get('digest') if a['status']=='ok' and baseline['status']=='ok' else None
    payload = {'records': records, 'planning':planning, 'attacks':attacks}
    (out/'manifest.json').write_text(json.dumps(payload, indent=2), encoding='utf-8')
    cp = subprocess.run(['node', str(Path(__file__).with_name('check.cjs')), str(out/'manifest.json')], capture_output=True, text=True, timeout=240)
    (out/'node.stdout.txt').write_text(cp.stdout); (out/'node.stderr.txt').write_text(cp.stderr)
    if cp.returncode: raise RuntimeError(cp.stderr)
    print(cp.stdout)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('output', type=Path); a = ap.parse_args(); run(a.output)
