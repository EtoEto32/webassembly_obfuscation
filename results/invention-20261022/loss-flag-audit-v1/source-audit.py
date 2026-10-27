"""Byte replay, independent interpreter, profile rejection and paired recovery."""
import argparse
import copy
import json
import random
import re
import shutil
import subprocess
import time
from pathlib import Path
import prototype as p


def run(main, runtime, out):
    main, runtime, out = (Path(x).resolve() for x in (main, runtime, out))
    verified = []
    for root in (main, runtime):
        pins = json.loads((root / 'pins.json').read_text(encoding='utf-8'))
        for name, digest in pins.items():
            assert p.q.digest(root / name) == digest, name
        verified.append(dict(directory=str(root), count=len(pins)))
    out.mkdir(parents=True, exist_ok=False)
    manifest = json.loads((main / 'manifest.json').read_text(encoding='utf-8'))
    attacker = p.recovery()
    replay, interpreter = [], []
    for t in manifest['targets']:
        data = bytes(manifest['fixtures'][t['name']]['data'])
        ops = manifest['fixtures'][t['name']]['ops']
        dst = out / t['file']
        if t['mode'] == 'recovered':
            attacker.recover(out / t['file'].replace('.recovered.wasm', '.wasm'), dst)
        elif t['opt'] == 'raw':
            if t['mode'] == 'plain':
                p.q.compile(p.wat(data, ops), dst)
            else:
                p.transform(main / (t['name'] + '.source.wasm'), dst, t['mode'], t['seed'])
        else:
            raw = out / t['file'].replace('.O3.', '.raw.')
            p.q.tool('wasm-opt', [raw, '-O3', '--enable-bulk-memory', '-o', dst])
            p.q.w.tool('wasm-validate', [dst])
        assert dst.read_bytes() == (main / t['file']).read_bytes(), t['file']
        replay.append(t['file'])
        if t['mode'] == 'bad':
            continue
        actions = [0xffffffff, *range(len(ops)), len(ops), 0xffffffff]
        mod = p.q.read(dst)
        logical, expected = bytearray(data), []
        for j, fail in enumerate(actions):
            for k, (d, s, length) in enumerate(ops):
                if fail == k:
                    break
                logical[d:d+length] = logical[s:s+length]
            h = 2166136261
            for value in logical:
                h = ((h ^ value) * 16777619) & 0xffffffff
            expected.append(h)
            mod += p.q.w.parse(f'''(module
                (func (export "step{j}") (call 0 (i32.const {fail})))
                (func (export "state{j}") (result i32) (call 1)))''')[1:]
        physical = p.m.apply([int(v) for v in t['meta']['matrix']], logical)
        for index in [*range(len(logical)), len(logical), 65535]:
            mod += p.q.w.parse(f'''(module (func (export "byte{index}") (result i32)
                (i32.load8_u (i32.const {index}))))''')[1:]
        interp = out / (dst.stem + '.interp.wasm')
        p.q.compile(p.q.w.emit(mod), interp)
        result = subprocess.run([str(p.ROOT / '.tools/wabt-1.0.42/bin/wasm-interp.exe'),
                                 str(interp), '--run-all-exports'], capture_output=True, text=True, timeout=30)
        if result.returncode:
            raise RuntimeError(result.stderr)
        observed = [int(v) for v in re.findall(r'state\d+\(\) => i32:(\d+)', result.stdout)]
        assert observed == expected, t['file']
        traps = []
        for j, fail in enumerate(actions):
            line = next(x for x in result.stdout.splitlines() if x.startswith(f'step{j}()'))
            trap = 'error:' in line
            assert trap == (fail < len(ops)), line
            traps.append(trap)
        memory = [(int(i), int(v)) for i, v in re.findall(r'byte(\d+)\(\) => i32:(\d+)', result.stdout)]
        assert len(memory) == len(logical) + 2
        for index, value in memory:
            assert value == (physical[index] if index < len(physical) else 0)
        (out / (dst.stem + '.interp.log')).write_text(result.stdout + result.stderr, encoding='utf-8')
        interpreter.append(dict(file=t['file'], calls=len(actions), traps=sum(traps), memory_probes=len(memory)))
    controls = []
    original = p.q.read(main / 'swap16.source.wasm')
    for name in ('exported-memory', 'memory-grow', 'parameter-data'):
        mod = copy.deepcopy(original)
        function = next(x for x in mod[1:] if x[0] == 'func')
        if name == 'exported-memory':
            mod.append(['export', '"memory"', ['memory', '0']])
        elif name == 'memory-grow':
            function.append(['drop', ['memory.grow', ['i32.const', '1']]])
        else:
            function.append(['i32.store8', ['i32.const', '0'], ['local.get', '0']])
        source = out / (name + '.wasm')
        p.q.compile(p.q.w.emit(mod), source)
        try:
            p.transform(source, out / (name + '.transformed.wasm'))
        except ValueError as error:
            controls.append(dict(name=name, rejected=str(error)))
        else:
            raise AssertionError('unsupported profile accepted')
    # Deliberately mix a lost original byte into a survivor: no current-state repair exists.
    try:
        p.plan(3, [(1, 0, 1)], [3, 2, 4])
    except ValueError as error:
        controls.append(dict(name='lost-information-mixed-into-survivor', rejected=str(error)))
    else:
        raise AssertionError('unsafe encoding accepted')
    work = [(t, rep) for t in manifest['targets']
            if t['mode'] in ('basis', 'current') and t['seed'] == 221001 for rep in range(5)]
    random.Random(221004).shuffle(work)
    recovery = []
    for index, (t, rep) in enumerate(work):
        start = time.perf_counter()
        dst = out / f'recovery-{index:02}.wasm'
        result = attacker.recover(main / t['file'], dst)
        result.update(file=t['file'], name=t['name'], mode=t['mode'], opt=t['opt'], repeat=rep,
                      total_ms=(time.perf_counter() - start) * 1000, oracle_queries=0)
        assert dst.read_bytes() == (main / (t['name'] + '.source.wasm')).read_bytes()
        recovery.append(result)
    report = dict(verified=verified, replay=replay, interpreter=interpreter, controls=controls,
                  recovery=recovery, recovery_note='Same Python process, randomized ordering, includes WABT read/validate and emitted output compilation. Human development cost unmeasured.')
    p.q.save(out / 'audit.json', report)
    for name in ('audit.py', 'prototype.py'):
        shutil.copy2(Path(__file__).with_name(name), out / ('source-' + name))
    p.q.save(out / 'pins.json', {str(f.relative_to(out)): p.q.digest(f) for f in out.rglob('*') if f.is_file()})
    print(json.dumps(dict(replay=len(replay), interpreter_calls=sum(x['calls'] for x in interpreter),
                          interpreter_traps=sum(x['traps'] for x in interpreter),
                          memory_probes=sum(x['memory_probes'] for x in interpreter),
                          controls=len(controls), recoveries=len(recovery))))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    for name in ('main', 'runtime', 'output'):
        ap.add_argument(name)
    args = ap.parse_args()
    run(args.main, args.runtime, args.output)
