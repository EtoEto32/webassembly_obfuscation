"""Practical cost reassessment with known adaptive elimination attacks.

No new obfuscation algorithm is claimed. Attack functions receive public bytes,
not source fixtures, seeds, correspondence maps, or expected BDD hashes.
"""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import random
import statistics
import struct
import time
import traceback

import prototype as p
import recover as r


def decode(image, bdd):
    if len(image) < 52:
        raise ValueError('Short header')
    magic, version, n, nn, nv, ne, s, t, nb, eb, ib, vb, rb = struct.unpack_from('<13I', image)
    if magic != p.MAGIC or version != 1 or not 1 <= n <= 128:
        raise ValueError('Unsupported descriptor')
    if not 2 <= nv <= 1024 or not (0 <= s < nv and 0 <= t < nv and s != t):
        raise ValueError('Bad vertices or terminals')
    if nn > 100000 or ne > 100000 or not (52 <= nb <= eb and nb + 12*nn <= eb):
        raise ValueError('Bad descriptor bounds')
    if max(nb + nn*12, eb + ne*12) > len(image):
        raise ValueError('Truncated descriptor')
    labels = []
    for i in range(nn):
        op, a, c = struct.unpack_from('<3I', image, nb + 12*i)
        if op == 0 and a < n:
            value = bdd.mk(a, 0, 1)
        elif op == 1 and a in (0, p.MASK):
            value = int(a != 0)
        elif op in (2, 3, 4) and a < i and c < i:
            value = bdd.binary({2: 'and', 3: 'or', 4: 'xor'}[op], labels[a], labels[c])
        else:
            raise ValueError('Bad label')
        labels.append(value)
    adjacency = {v: {} for v in range(nv)}
    for i in range(ne):
        a, b, label = struct.unpack_from('<3I', image, eb + 12*i)
        if a >= nv or b >= nv or label >= nn:
            raise ValueError('Bad edge')
        if a != b and labels[label]:
            value = bdd.binary('or', adjacency[a].get(b, 0), labels[label])
            adjacency[a][b] = adjacency[b][a] = value
    return n, adjacency, s, t


def eliminate(image, bdd, strategy):
    n, adjacency, s, t = decode(image, bdd)
    if strategy not in ('min_degree', 'min_fill'):
        raise ValueError('Unknown strategy')
    updates = 0
    eliminated = 0
    while len(adjacency) > 2:
        candidates = [v for v in adjacency if v not in (s, t)]
        def score(v):
            neighbors = list(adjacency[v])
            if strategy == 'min_degree':
                return len(neighbors), v
            missing = sum(b not in adjacency[a] for i, a in enumerate(neighbors) for b in neighbors[i+1:])
            return missing, len(neighbors), v
        k = min(candidates, key=score)
        neighbors = list(adjacency[k].items())
        for i, (a, av) in enumerate(neighbors):
            for b, bv in neighbors[i+1:]:
                value = bdd.binary('or', adjacency[a].get(b, 0), bdd.binary('and', av, bv))
                updates += 1
                if value:
                    adjacency[a][b] = adjacency[b][a] = value
        for a, _ in neighbors:
            del adjacency[a][k]
        del adjacency[k]
        eliminated += 1
    return n, adjacency[s].get(t, 0), {'eliminated_vertices': eliminated, 'edge_pair_updates': updates}


def analyze(binary, mod, strategy):
    bdd = r.BDD()
    started = time.perf_counter()
    image = r.initial_memory(binary)
    if strategy == 'direct':
        if image:
            raise ValueError('Direct formula strategy on a graph')
        n, root, extra = r.plain_root(None, bdd, mod)
    elif strategy == 'propagation':
        n, root, extra = r.graph_root(image, bdd)
    else:
        n, root, extra = eliminate(image, bdd, strategy)
    elapsed = time.perf_counter() - started
    return n, root, bdd, elapsed, extra


def bdd_eval(bdd, root, bits):
    while root >= 2:
        var, lo, hi = bdd.nodes[root]
        root = hi if bits[var] else lo
    return root


def small_checks():
    rng = random.Random(0x454c494d)
    checks = 0
    graphs = 0
    # Independent concrete semantics for each label (not the BDD interpreter).
    labels = [(0, 0, 0), (0, 1, 0), (0, 2, 0), (1, 0, 0), (1, p.MASK, 0),
              (4, 0, 1), (2, 1, 2)]
    last_image = None
    for nv in range(2, 9):
        for _ in range(40):
            edges = [(rng.randrange(nv), rng.randrange(nv), rng.randrange(7)) for j in range(rng.randrange(3*nv))]
            nb, eb = 52, 52 + 12*len(labels)
            header = [p.MAGIC, 1, 3, len(labels), nv, len(edges), 0, nv-1, nb, eb, 0, 0, 0]
            words = header + [x for row in labels + edges for x in row]
            image = struct.pack('<'+'I'*len(words), *words)
            last_image = image
            models = []
            for strategy in ('min_degree', 'min_fill'):
                bdd = r.BDD()
                _, root, _ = eliminate(image, bdd, strategy)
                models.append((bdd, root))
            for assignment in range(8):
                bits = [(assignment >> j) & 1 for j in range(3)]
                values = bits + [0, 1, bits[0] ^ bits[1], bits[1] & bits[2]]
                reached, queue = {0}, [0]
                while queue:
                    here = queue.pop()
                    for a, b, label in edges:
                        if not values[label]:
                            continue
                        other = b if a == here else a if b == here else None
                        if other is not None and other not in reached:
                            reached.add(other)
                            queue.append(other)
                for bdd, root in models:
                    assert bdd_eval(bdd, root, bits) == int(nv-1 in reached)
                    checks += 1
            graphs += 1
    rejected = 0
    for data in (b'', last_image[:51], last_image[:52], b'BAD!' + last_image[4:]):
        try:
            eliminate(data, r.BDD(), 'min_degree')
        except ValueError:
            rejected += 1
        else:
            raise AssertionError('Invalid descriptor accepted')
    return {'random_graphs': graphs, 'exhaustive_assignments_per_graph': 8,
            'algorithm_comparisons': checks, 'mismatches': 0, 'invalid_descriptors_rejected': rejected}


def report_markdown(out, report, prior):
    lines = ['# 解析費用の再評価', '',
             '新しい難読化方式ではなく、既存試作の適応的解析と評価訂正。全測定値はanalysis.jsonに保存。', '',
             '## 既存O3実測の読み直し', '',
             '同じ測定系の中で倍率を計算する。解析と実行の異なる言語・環境を直接割らない。微小な時間差の有意性は主張しない。', '',
             '|式|graph / plain 解析時間|graph / plain 実行時間|graph / plain bytes|80%消去 / graph 解析時間|',
             '|---|---:|---:|---:|---:|']
    for kernel in ('ch', 'maj', 'mixed12', 'parity16', 'blend24'):
        rows = {x['mode']: x for x in prior['O3'] if x['kernel'] == kernel}
        a, g, e = rows['plain'], rows['graph'], rows['elim80']
        lines.append(f"|{kernel}|{g['analysis_ms']/a['analysis_ms']:.2f}x|{g['median_ns']/a['median_ns']:.2f}x|{g['bytes']/a['bytes']:.2f}x|{e['analysis_ms']/g['analysis_ms']:.2f}x|")
    lines += ['', '## 今回の同一測定範囲によるO3追試', '',
              'モデル構築とBDD処理。WABT逆アセンブル・結果hash・出力コンパイルは除外。1回warmup後5回。同一プロセス、cacheは毎回作り直す。', '',
              '|式|方式|伝播 ms|最小次数 ms|最小fill ms|', '|---|---|---:|---:|---:|']
    for kernel in ('ch', 'maj', 'mixed12', 'parity16', 'blend24'):
        for mode in ('graph', 'elim50', 'elim80'):
            rows = {x['strategy']: x for x in report['measurements'] if x['kernel'] == kernel and x['mode'] == mode and x['opt'] == 'O3'}
            values = [f"{1000*rows[s]['median_seconds']:.4f}" if rows[s]['status'] == 'recovered' else rows[s]['status'] for s in ('propagation', 'min_degree', 'min_fill')]
            lines.append('|'+ '|'.join([kernel, mode] + values) + '|')
    lines += ['', '全件回復しても解析費用の差は記録する。新しい解析法の開発工数、人間の解析時間、現実的な保護対象への有効性は測定していない。既存75条件への再解析であり、新しい独立ベンチマーク75件ではない。', '']
    (out / 'summary.md').write_text('\n'.join(lines), encoding='utf-8')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('prior', type=Path)
    ap.add_argument('output', type=Path)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    build = json.loads((args.prior / 'build.json').read_text())
    expected = {x['file']: x for x in json.loads((args.prior / 'recovery-v2.json').read_text())['results']}
    prior = json.loads((args.prior / 'summary.json').read_text())
    prepared = {}
    jobs = []
    for row in build['conditions']:
        src = args.prior / row['file']
        binary = src.read_bytes()
        assert hashlib.sha256(binary).hexdigest() == row['sha256']
        mod = p.parse(p.tool('wasm2wat', [src, '--fold-exprs']))
        prepared[row['file']] = (binary, mod)
        methods = ('direct',) if row['mode'] in ('plain', 'mba') else ('propagation', 'min_degree', 'min_fill')
        jobs.extend((row, strategy) for strategy in methods)
    random.Random(2026101807).shuffle(jobs)
    report = {'status': 'running', 'python': platform.python_version(), 'platform': platform.platform(),
              'timing_scope': 'Model construction and BDD; excludes disassembly, digest, code generation. One warmup and five independent-cache samples.',
              'prior_directory': str(args.prior.resolve()), 'small_checks': small_checks(), 'measurements': [], 'recovered_binaries': []}
    for name in ('cost_reassessment.py', 'cost-reassessment-plan.md', 'prototype.py', 'recover.py', 'cost_verify.cjs'):
        (args.output / ('source-' + name)).write_bytes(Path(__file__).with_name(name).read_bytes())
    try:
        for row, strategy in jobs:
            binary, mod = prepared[row['file']]
            record = {**row, 'strategy': strategy}
            samples = []
            try:
                for repeat in range(6):
                    n, root, bdd, seconds, extra = analyze(binary, mod, strategy)
                    digest = bdd.digest(root)
                    if digest != expected[row['file']]['normalized_sha256']:
                        raise AssertionError('Semantic hash mismatch')
                    if repeat:
                        samples.append(seconds)
                record.update(status='recovered', samples_seconds=samples,
                              median_seconds=statistics.median(samples), allocated_nodes=len(bdd.nodes),
                              normalized_sha256=digest, **extra)
                if strategy in ('min_degree', 'min_fill'):
                    name = [x for x in mod[1:] if x[0] == 'export'][0][1]
                    wat, count = r.bdd_wat(n, name, bdd, root)
                    directory = args.output / ('recovered-' + strategy)
                    directory.mkdir(exist_ok=True)
                    out = directory / row['file']
                    wp = out.with_suffix('.wat')
                    wp.write_text(wat, encoding='utf-8')
                    p.tool('wat2wasm', [wp, '-o', out])
                    p.tool('wasm-opt', [out, '-O3', '-o', out.with_suffix('.optimized.wasm')])
                    optimized = out.with_suffix('.optimized.wasm')
                    p.tool('wasm-validate', [optimized])
                    sha = hashlib.sha256(optimized.read_bytes()).hexdigest()
                    report['recovered_binaries'].append({**row, 'strategy': strategy,
                        'path': str(optimized.relative_to(args.output)), 'sha256': sha,
                        'same_bytes_as_previous_recovery': sha == expected[row['file']]['output_sha256'], 'result_nodes': count})
            except OverflowError as exc:
                record.update(status='budget_exhausted', error=str(exc))
            except (ValueError, RuntimeError) as exc:
                record.update(status='unsupported_or_error', error=str(exc))
            report['measurements'].append(record)
        report['status'] = 'finished'
        report_markdown(args.output, report, prior)
    except Exception:
        report['status'] = 'failed'
        report['error'] = traceback.format_exc()
        raise
    finally:
        (args.output / 'analysis.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'status': report['status'], 'measurements': len(report['measurements']),
                      'new_recovered_binaries': len(report['recovered_binaries']), 'small_checks': report['small_checks']}))


if __name__ == '__main__':
    main()
