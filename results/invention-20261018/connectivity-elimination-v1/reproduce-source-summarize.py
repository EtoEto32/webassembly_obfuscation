"""Summarize the recorded results; does not infer unmeasured security."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics

ap = argparse.ArgumentParser()
ap.add_argument('directory', type=Path)
a = ap.parse_args()
read = lambda name: json.loads((a.directory / name).read_text(encoding='utf-8'))
build = read('build.json')
recovery = read('recovery-v2.json')['results']
timing = read('timing.json')['results']
analysis = read('analysis-timing.json')['results']
correct = read('correctness.json')
interpreter = read('interpreter.json')
rows = []
canonical = {}
for kernel in ('ch', 'maj', 'mixed12', 'parity16', 'blend24'):
    attacks = [r for r in recovery if r['file'].startswith(kernel+'-')]
    assert len(attacks) == 15 and all(r['status'] == 'recovered' for r in attacks)
    signatures = {r['normalized_sha256'] for r in attacks}
    binaries = {r['output_sha256'] for r in attacks}
    assert len(signatures) == len(binaries) == 1
    canonical[kernel] = {'bdd_hash_count': len(signatures), 'output_binary_hash_count': len(binaries),
                         'bdd_nodes': attacks[0]['bdd_result_nodes']}
    for mode in ('plain', 'mba', 'graph', 'elim50', 'elim80'):
        perf = next(x for x in timing if (x['kernel'], x['mode'], x['opt']) == (kernel, mode, 'O3'))
        attack = next(x for x in analysis if x['file'] == perf['file'])
        rows.append({'kernel': kernel, 'mode': mode, 'bytes': perf['bytes'],
                     'median_ns': perf['median_ns'], 'iqr_ns': [perf['q1_ns'], perf['q3_ns']],
                     'analysis_ms': attack['median_seconds']*1000,
                     'linear_memory_bytes': 65536 if mode in ('graph', 'elim50', 'elim80') else 0,
                     'max_rss_kib': perf['max_rss_kib']})
summary = {'conditions': len(build['conditions']), 'recovered': len(recovery),
           'correctness_calls': correct['comparisons'], 'correctness_mismatches': correct['mismatches'],
           'interpreter_calls': interpreter['calls'], 'interpreter_mismatches': interpreter['mismatches'],
           'canonical': canonical, 'O3': rows,
           'conclusion': 'Reject this prototype for the invention goal: all variants normalize to identical recovered Wasm per kernel, and elimination usually makes both execution and this recovery faster. Known switching algebra; no independent new principle established.'}
with (a.directory / 'summary.json').open('x', encoding='utf-8') as f:
    json.dump(summary, f, indent=2)
table = ['# 接続表現試作の実測', '',
         'O3。実行時間はJS呼出しを含む9回の中央値。解析時間はモデル構築とBDD計算の3回の中央値。異なる仕事なので倍率を直接比較しない。', '',
         '|kernel|mode|bytes|ns/call|解析ms|linear memory bytes|', '|---|---|---:|---:|---:|---:|']
for r in rows:
    table.append(f"|{r['kernel']}|{r['mode']}|{r['bytes']}|{r['median_ns']:.1f}|{r['analysis_ms']:.3f}|{r['linear_memory_bytes']}|")
(a.directory / 'summary.md').write_text('\n'.join(table)+'\n', encoding='utf-8')
# Snapshot current reproduction sources separately from the historical versions.
source = Path(__file__).parent
for name in ('prototype.py', 'recover.py', 'build.py', 'finish.py', 'verify.cjs', 'edge_cases.py', 'analysis_timing.py', 'summarize.py', 'reproduce.ps1', 'plan.md'):
    (a.directory / ('reproduce-source-' + name)).write_bytes((source / name).read_bytes())
files = []
for path in sorted(a.directory.rglob('*')):
    if path.is_file() and path.name != 'inventory.json':
        files.append({'path': path.relative_to(a.directory).as_posix(), 'bytes': path.stat().st_size,
                      'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
with (a.directory / 'inventory.json').open('x', encoding='utf-8') as f:
    json.dump({'files': files}, f, indent=2)
print(json.dumps({'conditions': len(build['conditions']), 'recovered': len(recovery), 'inventory_files': len(files)}))
