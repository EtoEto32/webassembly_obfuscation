# -*- coding: utf-8 -*-
"""Freeze the measured gate and its sources; no new-obfuscator success claim."""
import ast
import json
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import prototype as p


def main(main_dir, model_dir, runtime_dir, audit_dir, dest):
    dirs = [Path(x).resolve() for x in (main_dir, model_dir, runtime_dir, audit_dir)]
    out = Path(dest).resolve(); out.mkdir(parents=True, exist_ok=False)
    def read(i, name): return json.loads((dirs[i]/name).read_text(encoding='utf-8'))
    checks = read(0, 'checks.json'); model = read(1, 'model.json'); runtime = read(2, 'summary.json'); audit = read(3, 'audit.json')
    transforms = read(0, 'transformations.json'); attacks = read(0, 'attacks.json')
    rows = []
    for row in runtime['rows']:
        base = next(x for x in runtime['rows'] if x['name'] == row['name'] and x['mode'] == 'plain')
        rows.append(dict(**row, time_ratio=row['median_ns']/base['median_ns'], size_ratio=row['core_bytes']/base['core_bytes']))
    def interval(xs): return dict(min=min(xs), median=statistics.median(xs), max=max(xs))
    summary = dict(node_calls=checks['calls'], node_mismatches=checks['mismatches'], node_traps=checks['traps'],
                   negative_conditions=checks['negative'], positive_conditions=len(checks['rows']),
                   interpreter_positive_calls=audit['positive_calls'], interpreter_negative_calls=audit['negative_calls'],
                   interpreter_regression_calls=audit['tee_regression_calls'], rejected=len(audit['rejected']),
                   byte_replays=len(audit['replay']), recovered_byte_identity=len(audit['identities']),
                   small_model_cases=model['cases'], lemmas=model['lemmas'], witness=model['word32_witness'],
                   runtime=rows, processes=runtime['processes'], batches=runtime['batches'],
                   wrapper_checks=read(2, 'wrapper-check.json'), under_10ms=runtime['under_10ms'],
                   transform_ms=interval([x['ms'] for x in transforms]), recovery_ms=interval([x['ms'] for x in attacks]),
                   attack_status={s:sum(x['status']==s for x in attacks) for s in ('success','unsupported','crash','timeout')})
    p.q.save(out/'summary.json', summary)
    text = '''# 剰余表現の移植規則：実測結果

新発明の成功とは扱わない。oddは全条件で誤答し、正しいrepair/alignedは既知の構成。aligned全6条件はraw/O3とも元とbyte一致するWasmへ回復した。

正24条件101,208呼出しは値・trapとも一致。別WABTの正192・負48呼出しとlocal.tee回帰16呼出しも検査した。30本byte再生成、回復6本の元byte一致、8拒否対照、縮小幅524,256比較、6射影補題UNSATを保存した。同じ3人工式の派生条件であり、広いアプリケーション集合の評価や全入力の実装証明ではない。

|式|版|O3 core byte|実行中央値ns|元の時間倍率|process最大RSS KiB|
|---|---|---:|---:|---:|---:|
'''
    for r in rows:
        text += '|%s|%s|%d|%.3f|%.3f|%d|\n' % (r['name'],r['mode'],r['core_bytes'],r['median_ns'],r['time_ratio'],r['max_rss_kib'])
    text += '''
36 fresh process・252 batch。warmup16,384、20msへcalibration、全batchは10ms以上。wrapperをO3済みcoreに追加しWasm内で計時、Nodeは`--no-liftoff --no-wasm-lazy-compilation`。process中央値とbatch範囲はsummary.json、全batchはruntime側raw.json。RSSはNode全体であり保護の追加メモリとは断定しない。linear memoryは全条件0。無効なoddは性能比較から除いた。

変換35.80–38.64ms、回復36.56–39.45msは各条件1回の読取・出力・validation込み診断値。性能差の有意性検定・他CPU測定は行っていない。NotDec等の実逆コンパイラやrepairの自動解除は測定していない。

[設計と再現手順](../../../research/residue-wrap/README.md)。snapshotとSHA-256を本reportと各測定directoryに保存した。snapshotは実験後の凍結で、過去の実行開始時刻の暗号学的証明ではない。v1は射影器のlocal.tee処理不足による部分失敗として残し、保護成功に数えない。現形式の生成物から射影が回復できたことと、全てのRNS変換が解除可能なことは異なる。
'''
    (out/'report.md').write_text(text, encoding='utf-8')
    powershell = ['powershell','-NoProfile','-Command', 'Get-CimInstance Win32_Processor | Select-Object Name,NumberOfLogicalProcessors | ConvertTo-Json -Compress']
    cpu = subprocess.run(powershell, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=30)
    environment = dict(platform=platform.platform(), python=platform.python_version(),
                       node=subprocess.check_output(['node','--version'],text=True).strip(),
                       node_v8=checks['v8'], cpu=json.loads(cpu.stdout) if cpu.returncode==0 else 'unavailable',
                       wabt=p.q.w.tool('wasm-validate',['--version']).strip(),
                       binaryen=p.q.w.tool('wasm-opt',['--version']).strip(), z3=model['z3'],
                       measured_after_run=True, cpu_affinity=False)
    p.q.save(out/'environment.json', environment)
    sources = [f for f in p.HERE.iterdir() if f.suffix in ('.py','.cjs','.md')]
    sources += [p.ROOT/'research/isotope-swizzle/prototype.py', p.ROOT/'research/connectivity-elimination/prototype.py', p.ROOT/'research/span-mask/bench.cjs']
    pins = []
    for folder in dirs + [out]:
        if (folder/'provenance.json').exists(): raise FileExistsError('refuse to overwrite frozen provenance')
        for f in sources:
            if f.suffix == '.py': ast.parse(f.read_text(encoding='utf-8'))
            target = folder/'sources'/f.relative_to(p.ROOT)
            target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(f.read_bytes())
        entries = [dict(file=str(f.relative_to(folder)),sha256=p.q.digest(f)) for f in sorted(folder.rglob('*')) if f.is_file()]
        p.q.save(folder/'provenance.json', entries)
        pins.extend((folder, e) for e in entries)
    for folder, entry in pins:
        if p.q.digest(folder/entry['file']) != entry['sha256']: raise AssertionError('hash mismatch')
    print(json.dumps(dict(verified_hashes=len(pins), recovery=summary['attack_status'], node_calls=checks['calls'], environment=environment)))


if __name__ == '__main__': main(*sys.argv[1:])
