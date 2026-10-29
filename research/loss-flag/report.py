import argparse
import json
import platform
import shutil
import statistics
import sys
from pathlib import Path
import prototype as p


def read(root, file):
    return json.loads((root / file).read_text(encoding='utf-8'))


def run(main, runtime, audit, out):
    main, runtime, audit, out = (Path(x).resolve() for x in (main, runtime, audit, out))
    verified = []
    for directory in (main, runtime, audit):
        pins = read(directory, 'pins.json')
        for name, digest in pins.items():
            assert p.q.digest(directory / name) == digest, name
        verified.append(dict(directory=str(directory), files=len(pins)))
    out.mkdir(parents=True, exist_ok=False)
    manifest, checks = read(main, 'manifest.json'), read(main, 'checks.json')
    perf, audited = read(runtime, 'runtime.json'), read(audit, 'audit.json')
    attacks = []
    for name in manifest['fixtures']:
        for opt in ('raw', 'O3'):
            row = dict(name=name, opt=opt)
            for mode in ('basis', 'current'):
                subset = [r for r in audited['recovery'] if r['name'] == name and r['opt'] == opt and r['mode'] == mode]
                row[mode] = dict(total_median_ms=statistics.median(r['total_ms'] for r in subset),
                                 analysis_median_ms=statistics.median(r['analysis_ms'] for r in subset),
                                 total_range_ms=[min(r['total_ms'] for r in subset), max(r['total_ms'] for r in subset)])
            row['total_ratio'] = row['current']['total_median_ms'] / row['basis']['total_median_ms']
            row['analysis_ratio'] = row['current']['analysis_median_ms'] / row['basis']['analysis_median_ms']
            attacks.append(row)
    rows = []
    for group in perf['summaries']:
        t = next(t for t in manifest['targets'] if t['name'] == group['name'] and t['mode'] == 'current'
                 and t['opt'] == 'raw' and t['seed'] == 221001)
        rows.append(dict(name=group['name'], old_entry_values=t['meta']['joint_rank'],
                         current_entry_values=0, current_repair_temporaries=t['meta']['repair_temporary_values'],
                         transform_ms=t['meta']['transform_ms'], runtime=group))
    result = dict(verified=verified, positive_conditions=len(checks['rows']),
                  unique_positive_binaries=len({t['sha256'] for t in manifest['targets'] if t['mode'] != 'bad'}),
                  calls=checks['calls'], traps=checks['traps'], negative_conditions=len(checks['negative']),
                  recovered_conditions=len(read(main, 'analysis.json')), replayed=len(audited['replay']),
                  interpreter_calls=sum(r['calls'] for r in audited['interpreter']),
                  interpreter_traps=sum(r['traps'] for r in audited['interpreter']),
                  memory_probes=sum(r['memory_probes'] for r in audited['interpreter']),
                  profile_rejections=audited['controls'], attacks=attacks, rows=rows,
                  environment=dict(python=sys.version, os=platform.platform(),
                                   node=perf['rows'][0]['node'], v8=perf['rows'][0]['v8'],
                                   cpu=perf['rows'][0]['cpu'], flags=perf['rows'][0]['flags'],
                                   wabt=p.q.w.tool('wasm-interp', ['--version']).strip(),
                                   binaryen=p.q.tool('wasm-opt', ['--version']).strip()))
    p.q.save(out / 'facts.json', result)
    lines = ['# 現memoryを使う修復の実測', '',
             '性能は別moduleからのimport呼出し、正常出口、seed 221001、O3。各3 fresh process×7 batch。中央値はprocess中央値の中央値。', '',
             '| profile | plain ns | eager ns | basis ns | current ns | current/basis | current/plain | basis/current bytes | 入口保存値 basis→current |',
             '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for r in rows:
        g = r['runtime']
        lines.append(f"| {r['name']} | {g['plain']['median_ns']:.3f} | {g['eager']['median_ns']:.3f} | {g['basis']['median_ns']:.3f} | {g['current']['median_ns']:.3f} | {g['current_over_basis']:.3f} | {g['current_over_plain']:.3f} | {g['basis']['bytes']}/{g['current']['bytes']} | {r['old_entry_values']}→0 |")
    lines += ['', '保存値は8bit情報を持つi32 localの個数であり、実際のstack/register割当byte数ではない。currentにも出口の一時値がある。全modeの線形memoryは64KiB。', '',
              '| profile | form | basis回復 ms | current回復 ms | total比 | 解析本体比 |', '|---|---|---:|---:|---:|---:|']
    for a in attacks:
        lines.append(f"| {a['name']} | {a['opt']} | {a['basis']['total_median_ms']:.3f} | {a['current']['total_median_ms']:.3f} | {a['total_ratio']:.3f} | {a['analysis_ratio']:.3f} |")
    lines += ['', '回復は既存prefix-repair/recover.pyを未変更で使用。各5反復、同一Python process、ランダム順。元sourceやmanifestを回復器へ渡さず、生成物が元binaryと一致するかを回復後に判定。全条件で一致。人間の解析器開発時間は未測定。', '',
              f"正{result['positive_conditions']}条件、{result['calls']:,}呼出し、期待trap {result['traps']:,}。unique positive binaryは{result['unique_positive_binaries']}。再生成{result['replayed']}本はbyte一致。WABT別実行器{result['interpreter_calls']}呼出し・{result['memory_probes']} memory probe一致。", '',
              '正常出口の速度改善は副次的な成果。追加の保護効果と独立した新規性を確立した結果ではなく、主発明に採用しない。']
    (out / 'comparison.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    shutil.copy2(Path(__file__), out / 'source-report.py')
    p.q.save(out / 'pins.json', {str(f.relative_to(out)): p.q.digest(f) for f in out.rglob('*') if f.is_file()})
    print(json.dumps(dict(positive=result['positive_conditions'], unique=result['unique_positive_binaries'],
                          attacks=attacks, environment=result['environment'])))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    for name in ('main', 'runtime', 'audit', 'output'):
        ap.add_argument(name)
    a = ap.parse_args()
    run(a.main, a.runtime, a.audit, a.output)
