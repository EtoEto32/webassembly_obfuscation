"""One command generates binaries, checks equivalence, attacks and measures them."""
import argparse
from collections import deque
import hashlib
import json
from pathlib import Path
import platform
import random
import re
import shutil
import statistics
import subprocess
import time
import prototype as p

HERE = Path(__file__).resolve().parent


def save(path, obj):
    with Path(path).open('x', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write('\n')


def models():
    ans = {}
    for n in [4, 8, 16]:
        delta = [[(q+1+a) % n for q in range(n)] for a in range(2)]
        ans[f'cycle{n}'] = dict(delta=[t+[0]*(16-n) for t in delta], final=1, intended_states=n)
        rng = random.Random(20261018+n)
        for trial in range(10000):
            delta = [[rng.randrange(n) for _ in range(n)] for _ in range(2)]
            final = rng.randrange(1, (1 << n)-1)
            if len(p.canonical(delta, final)[0][0]) == n:
                break
        else:
            raise RuntimeError('Model generation exhausted')
        ans[f'general{n}'] = dict(delta=[t+[0]*(16-n) for t in delta], final=final,
                                intended_states=n, generation_attempt=trial+1)
    return ans


def language_equivalence(left, right):
    da, fa = left
    db, fb = right
    todo, seen = deque([(0, 0)]), {(0, 0)}
    while todo:
        a, b = todo.popleft()
        if (fa >> a) & 1 != (fb >> b) & 1:
            return dict(equivalent=False, product_states=len(seen))
        for c in range(2):
            nxt = da[c][a], db[c][b]
            if nxt not in seen:
                seen.add(nxt)
                todo.append(nxt)
    return dict(equivalent=True, product_states=len(seen))


def backward_orbit(delta, final):
    todo, seen = deque([final]), {final}
    start = time.perf_counter()
    while todo:
        v = todo.popleft()
        for row in delta:
            nxt = sum(((v >> q) & 1) << i for i, q in enumerate(row))
            if nxt not in seen:
                seen.add(nxt)
                todo.append(nxt)
    return dict(states=len(seen), ms=(time.perf_counter()-start)*1000)


def command(cmd, timeout=60):
    r = subprocess.run(list(map(str, cmd)), capture_output=True, text=True, timeout=timeout)
    if r.returncode:
        raise RuntimeError(json.dumps(dict(command=list(map(str, cmd)), stdout=r.stdout, stderr=r.stderr)))
    return r.stdout


def node_check(out):
    s = command(['node', HERE/'check.cjs', out], timeout=120)
    (out/'node-check.log').write_text(s, encoding='utf-8')
    print(s.strip(), flush=True)


def interpreter_checks(out, manifest):
    folder = out/'interpreter'
    folder.mkdir()
    rows = []
    data = bytes([0, 1, 2, 3, 254, 255, 128, 127])
    for item in manifest['files']:
        wat = p.w.tool('wasm2wat', [out/item['path'], '--fold-exprs', '--no-debug-names'])
        escaped = ''.join('\\%02x' % b for b in data)
        tail = f'(data (i32.const 0) "{escaped}")'
        for j, length in enumerate([0, 1, 3, 8]):
            tail += f'(func (export "check{j}") (result i32) (call 0 (i32.const 0) (i32.const {length})))'
        target = folder/Path(item['path']).name
        p.compile_wat(wat.rstrip()[:-1]+tail+')', target)
        log = p.w.tool('wasm-interp', [target, '--run-all-exports'])
        target.with_suffix('.log').write_text(log, encoding='utf-8')
        got = [int(x) for x in re.findall(r'check\d+\(\) => i32:(\d+)', log)]
        model = manifest['models'][item['benchmark']]
        expected = []
        for length in [0, 1, 3, 8]:
            q = 0
            for a in data[:length]:
                q = model['delta'][a & 1][q]
            expected.append((model['final'] >> q) & 1)
        assert got == expected, (item['path'], got, expected, log)
        rows.append(dict(path=item['path'], got=got, expected=expected))
    save(out/'interpreter.json', dict(calls=4*len(rows), mismatches=0, records=rows))


def negative_controls(out, manifest):
    source = out/'general16.mixed.raw.wasm'
    wat = p.w.tool('wasm2wat', [source, '--fold-exprs', '--no-debug-names'])
    wrong = out/'wrong-or.wasm'
    p.compile_wat(wat.replace('(v128.xor', '(v128.or', 1), wrong)
    records = []
    for label, target in [('nonlinear_or', wrong)]:
        try:
            p.recover(p.read(target))
        except ValueError as e:
            records.append(dict(control=label, rejected=True, reason=str(e)))
        else:
            raise AssertionError('Invalid linearity assumption accepted')
    suffix = p.w.tool('wasm2wat', [out/'general16.suffix.raw.wasm', '--fold-exprs', '--no-debug-names'])
    mod = p.w.parse(suffix)
    changed = 0
    for x in p.descendants(mod):
        if x[0] == 'i32.sub' and x[-1] == ['i32.const', '1']:
            x[-1] = ['i32.const', '2']
            changed += 1
    assert changed == 1
    stride = out/'wrong-stride.wasm'
    p.compile_wat(p.w.emit(mod), stride)
    try:
        p.recover(p.read(stride))
    except ValueError as e:
        records.append(dict(control='wrong_stride', rejected=True, reason=str(e)))
    else:
        raise AssertionError('Wrong iteration scheme accepted')
    source_wat = p.w.tool('wasm2wat', [out/'general16.plain.raw.wasm', '--fold-exprs', '--no-debug-names'])
    source_mod = p.w.parse(source_wat)
    func = next(x for x in source_mod[1:] if x[0] == 'func')
    func.insert(len(func)-1, ['i32.store8', ['i32.const', '0'], ['i32.const', '42']])
    effect = out/'unsupported-store.wasm'
    p.compile_wat(p.w.emit(source_mod), effect)
    try:
        p.transform(effect, out/'must-not-exist.wasm', 'suffix', 0)
    except ValueError as e:
        records.append(dict(control='source_memory_write', rejected=True, reason=str(e)))
    else:
        raise AssertionError('Side-effecting source template accepted')
    assert not (out/'must-not-exist.wasm').exists()
    save(out/'negative-analysis.json', records)
    manifest['negative_control'] = dict(path=wrong.name, benchmark='general16')


def measure(out, files):
    schedule = [(item, trial) for item in files if not item['recovered'] for trial in range(3)]
    random.Random(20261018).shuffle(schedule)
    records = []
    for j, (item, trial) in enumerate(schedule):
        result = json.loads(command(['node', HERE/'bench.cjs', out/item['path']]))
        result.update(path=item['path'], trial=trial)
        records.append(result)
        if (j+1) % 27 == 0:
            print(json.dumps(dict(benchmark_processes=j+1, total=len(schedule))), flush=True)
    save(out/'timings.json', dict(fresh_processes=len(schedule), records=records))
    return records


def summarize(out, manifest, analysis, timings):
    checks = json.loads((out/'checks.json').read_text())
    rows = []
    for item in manifest['files']:
        if item['recovered']:
            continue
        runs = [r for r in timings if r['path'] == item['path']]
        attack = next(r for r in analysis if r['path'] == item['path'])
        times = {}
        for length in [32, 512]:
            meds = [statistics.median(next(x['samples_ns_per_call'] for x in r['rows'] if x['length'] == length)) for r in runs]
            times[str(length)] = dict(median_ns=statistics.median(meds), min_process_ns=min(meds), max_process_ns=max(meds))
        rows.append(dict(**item, bytes=(out/item['path']).stat().st_size, times=times,
                         analysis_ms=statistics.median(attack['analysis_samples_ms']),
                         parse_validate_ms=attack['parse_validate_ms'],
                         orbit_states=attack['report']['orbit_states'],
                         max_rss_kib=[r['max_rss_kib'] for r in runs]))
    save(out/'summary.json', dict(calls=checks['calls'], mismatches=checks['mismatches'],
                                 memory_mismatches=checks['memory_mismatches'], rows=rows))
    text = '# 実測表\n\nO3。ns/callは3 fresh processの中央値の中央値。各processの中央値の範囲も併記。\n\n'
    text += '|benchmark|form|bytes|32byte ns|512byte ns|解析ms|双対/元状態数|\n|---|---|---:|---:|---:|---:|---:|\n'
    for r in rows:
        if r['opt'] == 'O3':
            cells = []
            for length in ['32', '512']:
                t = r['times'][length]
                cells.append(f"{t['median_ns']:.1f} ({t['min_process_ns']:.1f}–{t['max_process_ns']:.1f})")
            text += f"|{r['benchmark']}|{r['mode']}|{r['bytes']}|{cells[0]}|{cells[1]}|{r['analysis_ms']:.3f}|{r['orbit_states']}|\n"
    (out/'comparison.md').write_text(text, encoding='utf-8')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('output', type=Path)
    ap.add_argument('--compare', type=Path)
    args = ap.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    data, files, transforms, analysis = models(), [], [], []
    save(out/'design-models.json', data)
    for bi, (name, model) in enumerate(data.items()):
        original = out/(name+'.plain.raw.wasm')
        p.compile_wat(p.plain(model['delta'], model['final']), original)
        model['canonical'] = p.canonical(model['delta'], model['final'])
        model['backward_orbit'] = backward_orbit(model['delta'], model['final'])
        for mode in ['plain', 'suffix', 'mixed']:
            raw = out/(name+'.'+mode+'.raw.wasm')
            if mode != 'plain':
                t = p.transform(original, raw, mode, 20261018+bi)
                transforms.append(dict(benchmark=name, **t))
            for opt in ['raw', 'O2', 'O3']:
                target = raw if opt == 'raw' else out/(name+'.'+mode+'.'+opt+'.wasm')
                if opt != 'raw':
                    p.w.tool('wasm-opt', [raw, '-'+opt, '--enable-simd', '-o', target])
                program = p.read(target)
                report = p.recover(program)  # warmup, no source/seed/manifest passed
                samples = [p.recover(program)['analysis_ms'] for _ in range(9)]
                proof = language_equivalence((model['delta'], model['final']), (report['delta'], report['final']))
                assert proof['equivalent']
                assert model['canonical'] == (report['delta'], report['final'])
                record = dict(benchmark=name, mode=mode, opt=opt, path=target.name, recovered=False)
                files.append(record)
                analysis.append(dict(path=target.name, status='success', parse_validate_ms=program['parse_validate_ms'],
                                     analysis_samples_ms=samples, report=report, dfa_equivalence=proof))
                recovered = out/(target.stem+'.recovered.wasm')
                p.emit_recovered(report, recovered)
                files.append(dict(record, path=recovered.name, recovered=True))
        print(json.dumps(dict(generated=name, reverse_states=model['backward_orbit']['states'])), flush=True)
    manifest = dict(models=data, files=files)
    negative_controls(out, manifest)
    save(out/'manifest.json', manifest)
    save(out/'transforms.json', transforms)
    save(out/'analysis.json', analysis)
    algebra = []
    for row in analysis:
        name, mode, _, _ = row['path'].split('.')
        if mode == 'plain':
            continue
        design = next(t for t in transforms if t['benchmark'] == name and t['mode'] == mode)
        actual = row['report']
        assert actual['matrices'] == design['matrices']
        assert actual['initial'] == design['initial'] and actual['output'] == design['output']
        a = [[1 << q for q in t] for t in data[name]['delta']]
        l = design['basis']
        for c in range(2):
            assert p.compose(actual['matrices'][c], l) == p.compose(l, a[c])
        assert p.apply(l, data[name]['final']) == actual['initial']
        assert p.xor_all(l[j] for j in range(16) if actual['output'] >> j & 1) == 1
        algebra.append(dict(path=row['path'], update_initial_output_match=True, conjugacy=True))
    save(out/'algebra-audit.json', dict(conditions=len(algebra), mismatches=0, records=algebra))
    node_check(out)
    interpreter_checks(out, manifest)
    timings = measure(out, files)
    summarize(out, manifest, analysis, timings)
    env = dict(python=platform.python_version(), platform=platform.platform(),
               wabt=p.w.tool('wasm2wat', ['--version']).strip(), binaryen=p.w.tool('wasm-opt', ['--version']).strip(),
               node=timings[0]['node'], v8=timings[0]['v8'], cpu=timings[0]['cpu'])
    save(out/'environment.json', env)
    snap = out/'sources'
    snap.mkdir()
    for source in ['prototype.py', 'run.py', 'check.cjs', 'bench.cjs', 'plan.md']:
        shutil.copy2(HERE/source, snap/source)
    shutil.copy2(p.w.__file__, snap/'common-prototype.py')
    hashes = {f['path']: hashlib.sha256((out/f['path']).read_bytes()).hexdigest() for f in files}
    save(out/'binary-sha256.json', hashes)
    audit = dict(primary_conditions=len(analysis), recovered_binaries=len(analysis),
                 recovery_successes=sum(x['status'] == 'success' for x in analysis),
                 main_status_counts={'success':len(analysis),'unsupported':0,'crash':0,'timeout':0,'analysis_failure':0},
                 source_sha256={s.name:hashlib.sha256(s.read_bytes()).hexdigest() for s in snap.iterdir()})
    if args.compare:
        old = json.loads((args.compare/'binary-sha256.json').read_text())
        audit['comparison'] = dict(old=str(args.compare), equal_binaries=sum(old.get(k) == v for k, v in hashes.items()),
                                   total=len(hashes), exact_same_set=set(old) == set(hashes))
        assert audit['comparison']['equal_binaries'] == len(hashes) and audit['comparison']['exact_same_set']
    save(out/'audit.json', audit)
    print(json.dumps(audit), flush=True)


if __name__ == '__main__':
    main()
