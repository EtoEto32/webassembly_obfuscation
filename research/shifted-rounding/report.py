"""Summarize saved evidence; pin inputs and a reproducible source snapshot."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NAMES = {
    'main': 'shifted-rounding-main-v1',
    'recovery': 'shifted-rounding-recovery-v3',
    'runtime': 'shifted-rounding-runtime-v1',
    'underflow': 'shifted-rounding-underflow-v1',
    'audit': 'shifted-rounding-audit-v1',
}


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('output', type=Path)
    ap.add_argument('--results', type=Path, default=ROOT/'results/invention-20261021')
    args = ap.parse_args()
    dirs = {k: args.results.resolve()/v for k, v in NAMES.items()}
    out = args.output.resolve()
    if any(out == d or d in out.parents for d in dirs.values()):
        raise ValueError('Report must be outside the immutable experiment directories')
    out.mkdir(parents=True, exist_ok=False)
    checks = read(dirs['main']/'checks.json')
    recovered_checks = read(dirs['recovery']/'checks.json')
    recovered = read(dirs['recovery']/'recovery.json')
    manifest = read(dirs['main']/'manifest.json')
    times = read(dirs['audit']/'attack-timing.json')
    runtime = read(dirs['runtime']/'summary.json')+read(dirs['underflow']/'summary.json')
    assert len(manifest) == 32 and checks['calls'] == 204800
    assert recovered_checks['calls'] == 102400
    assert all(x['mismatches'] == 0 for c in (checks, recovered_checks) for x in c['records'])
    assert len(recovered) == 16 and all(x['status'] == 'recovered' and x['same_ordered_dag'] for x in recovered)
    original_pins = read(dirs['main']/'hashes.json')
    assert all(digest(dirs['main']/f) == h for f, h in original_pins.items())
    for row in manifest:
        assert digest(dirs['main']/row['file']) == row['sha256']
    replay = read(dirs['audit']/'replay.json')
    for name in replay:
        original = dirs['recovery' if '-recovered' in name else 'main']/name
        assert original.read_bytes() == (dirs['audit']/name).read_bytes()
    rejections = read(dirs['audit']/'rejections.json')
    assert len(rejections) == 5 and all(x['rejected'] and x['validated'] for x in rejections)
    negative = read(dirs['audit']/'negative-no-rounding.json')
    assert negative['actual'] != negative['expected']
    def span(values):
        values = list(values)
        return [min(values), max(values)]
    stats = {
        'classification': 'negative protection result; retained implementation and limited numerical effect',
        'inputs': NAMES,
        'main_checks': read(dirs['main']/'check-stdout.txt'),
        'recovered_checks': read(dirs['recovery']/'check-stdout.txt'),
        'quantizer_probe_note': '16380 initial probes; repeated during recovery, not an independent extra corpus',
        'recovered_conditions': len(recovered), 'ordered_dag_matches': len(recovered),
        'shifted_conditions': sum('-shifted-' in x['file'] for x in recovered),
        'byte_replays': len(replay), 'rejections': len(rejections),
        'interpreter_calls': read(dirs['audit']/'interpreter.json')['calls'],
        'negative_no_rounding': negative,
        'runtime_processes': sum(len(read(dirs[k]/'runtime.json')) for k in ('runtime', 'underflow')),
        'runtime_conditions': len(runtime),
        'runtime': runtime,
        'recovery_median_ms_range': span(x['median_ms'] for x in times),
        'reader_median_ms_range': span(x['read_median_ms'] for x in times),
        'transform_single_sample_ms_range': span(x['transform']['total_ms'] for x in manifest if x['opt'] == 'raw'),
        'peak_process_rss_kib_range': span(r for x in runtime for r in x['peak_rss_kib']),
        'initial_hashes_verified': len(original_pins),
        'environment': read(dirs['audit']/'environment.json'),
    }
    save(out/'summary.json', stats)
    lines = ['# 倍率に合わせた丸め格子：保存値の集計', '',
             '4個の合成DAGを使う限定実験。復元成功を記録し、難読化としての優位は主張しない。', '',
             '主32条件204,800呼出し、復元16条件102,400呼出しが一致。',
             '量子化器16,380 probe、WABT 384 probe、48 binary再生成一致、5拒否対照。', '',
             '## O3の実行時間（ns/呼出し）', '',
             '各値は3 fresh processの中央値。各process内は9 batchの中央値。', '',
             '| 入力分布 | kernel | plain | eager | grid0 | shifted | shifted / plain |',
             '|---|---|---:|---:|---:|---:|---:|']
    for dist in ('normal', 'zero', 'underflow'):
        for kernel in ('multiply-add', 'horner6', 'butterfly4'):
            cell = {x['mode']: x for x in runtime if x['distribution'] == dist and x['kernel'] == kernel}
            v = [cell[m]['median_ns'] for m in ('plain', 'eager', 'grid0', 'shifted')]
            lines.append('| '+dist+' | '+kernel+' | '+' | '.join(f'{n:.3f}' for n in v)+f' | {v[-1]/v[0]:.3f} |')
    lines += ['', '## サイズと測定の限界', '',
              '| kernel | plain bytes | eager bytes | grid0 bytes | shifted bytes |',
              '|---|---:|---:|---:|---:|']
    for kernel in ('multiply-add', 'horner6', 'butterfly4', 'cancellation'):
        cell = {x['mode']: x for x in manifest if x['opt'] == 'O3' and x['kernel'] == kernel}
        lines.append('| '+kernel+' | '+' | '.join(str(cell[m]['bytes']) for m in ('plain', 'eager', 'grid0', 'shifted'))+' |')
    lines += ['', '下記の範囲は条件ごとの中央値（変換時間のみ各条件1回）。', '',
              f"- 復元本体: {stats['recovery_median_ms_range']} ms。WABT読取: {stats['reader_median_ms_range']} ms。",
              f"- 読取・生成・compile/validateの合計: {stats['transform_single_sample_ms_range']} ms。O3時間は含まない。",
              f"- 最大process RSS: {stats['peak_process_rss_kib_range']} KiB。linear memoryは未使用だが、stack/JIT/heapの費用はある。",
              '- 量子化器の再実行を独立した追加検体に数えない。4個のkernelを多数の実アプリと読み替えない。',
              '- 高速な条件は呼出し数の上限に達して目標10ms未満のbatchを含む。細かな速度差は断定しない。',
              '- underflow条件ではgrid0もshiftedより速い。倍率変更による保護効果や新規な高速化原理は示していない。',
              '- CPU固定・周波数固定・hardware counter測定なし。CPFloatそのものとの性能比較ではない。',
              '- [実験と再現手順](../../../research/shifted-rounding/README.md)、[先行性の対応](../../../research/shifted-rounding/prior-art.md)。', '']
    (out/'comparison.md').write_text('\n'.join(lines), encoding='utf-8')
    sources = list(Path(__file__).parent.glob('*.py'))+list(Path(__file__).parent.glob('*.cjs'))+list(Path(__file__).parent.glob('*.md'))
    sources += [ROOT/f for f in (
        'research/zero-sign-transport/prototype.py', 'research/zero-sign-transport/model.py',
        'research/zero-sign-transport/bench.cjs', 'research/isotope-swizzle/prototype.py',
        'research/connectivity-elimination/prototype.py')]
    for source in sources:
        target = out/'source-snapshot'/source.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    save(out/'input-hashes.json', {
        str(f.relative_to(args.results.resolve())).replace('\\', '/'): digest(f)
        for d in dirs.values() for f in sorted(d.rglob('*')) if f.is_file()
    })
    save(out/'hashes.json', {
        str(f.relative_to(out)).replace('\\', '/'): digest(f)
        for f in sorted(out.rglob('*')) if f.is_file()
    })
    print(json.dumps({k: stats[k] for k in ('recovered_conditions', 'byte_replays', 'runtime_processes', 'initial_hashes_verified')}))


if __name__ == '__main__':
    main()
