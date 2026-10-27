"""Sequential whole-application control; counts are executions, not new bugs."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def meaning(row):
    return [(x['name'], x['args'], x['code'], x['logs'], x.get('output')) for x in row['commands']]

def main(out):
    out.mkdir(parents=True, exist_ok=False)
    variants = {'original': ROOT/'.tools/state-witness-ffmpeg-0.12.10-v1/core-mt/ffmpeg-core.wasm',
                'retained': ROOT/'results/state-witness/post-start-live-input-v1/retained.wasm'}
    glue = ROOT/'.tools/state-witness-ffmpeg-glue-v2'
    summary = {'runs': [], 'comparisons': [], 'failures': [], 'naturalRestoreBug': False,
               'actualBrowserTest': False, 'wasmRestoreExecuted': False, 'performanceComparison': False}
    configurations = [(seed, 'counted') for seed in (1, 7, 29)] + [(1, 'unwrapped')]
    records = {}
    for seed, mode in configurations:
        for name, binary in variants.items():
            runname = f'{name}-{seed}-{mode}'
            command = ['node', str(HERE/'ffmpeg-workload.cjs'), str(glue), str(binary), str(out/runname), str(seed), mode]
            start = time.perf_counter()
            try:
                run = subprocess.run(command, capture_output=True, text=True, encoding='utf8', timeout=90)
                (out/(runname+'.stdout')).write_text(run.stdout, encoding='utf8')
                (out/(runname+'.stderr')).write_text(run.stderr, encoding='utf8')
                item = {'name': runname, 'returncode': run.returncode, 'elapsedSeconds': time.perf_counter()-start}
                if run.returncode != 0: summary['failures'].append(item)
                else:
                    result = json.loads((out/runname/'result.json').read_text())
                    assert result['status'] == 'passed'
                    records[name,seed,mode] = result
            except subprocess.TimeoutExpired:
                item = {'name': runname, 'status': 'timeout'}
                summary['failures'].append(item)
            summary['runs'].append(item)
    for seed, mode in configurations:
        left = records.get(('original',seed,mode)); right = records.get(('retained',seed,mode))
        if left and right:
            equal = meaning(left) == meaning(right)
            summary['comparisons'].append({'seed': seed, 'mode': mode, 'commands': len(left['commands']), 'same': equal})
            if not equal: summary['failures'].append({'seed': seed, 'mode': mode, 'status': 'observation-difference'})
    summary['wrapperControls'] = {name: meaning(records[name,1,'counted']) == meaning(records[name,1,'unwrapped'])
        for name in variants if (name,1,'counted') in records and (name,1,'unwrapped') in records}
    summary['inputSensitivity'] = {command: len({row['commands'][index]['output']['sha256']
        for (name,seed,mode),row in records.items() if name=='original' and mode=='counted'})
        for index,command in enumerate(('audio-resample','audio-lossless','audio-roundtrip','image-scale'))}
    summary['completedCommands'] = sum(len(row['commands']) for row in records.values())
    summary['mainThreadExportCalls'] = sum(sum(row['mainThreadExportCalls'].values()) for row in records.values())
    summary['countedFfmpegEntries'] = sum(row['mainThreadExportCalls'].get('Ma',0) for row in records.values())
    summary['workerCreations'] = sum(row['workersCreated'] for row in records.values())
    summary['roundtripsPassed'] = sum(row['roundtripMatchesOriginalPcm'] for row in records.values())
    summary['binarySha256'] = {name:digest(binary) for name,binary in variants.items()}
    if not all(summary['wrapperControls'].values()) or any(x != 3 for x in summary['inputSensitivity'].values()):
        summary['failures'].append({'status': 'control-failure'})
    summary['status'] = 'passed' if not summary['failures'] and len(records)==8 else 'failed'
    (out/'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf8')
    for name in ('masters-retest-plan.md', 'ffmpeg-workload.cjs', 'ffmpeg-worker-adapter.cjs', 'ffmpeg-workload-suite.py', 'ffmpeg-glue-fetch.py'):
        shutil.copy2(HERE/name, out/name)
    (out/'sha256.json').write_text(json.dumps({str(p.relative_to(out)).replace('\\','/'):digest(p)
        for p in sorted(out.rglob('*')) if p.is_file() and p.name!='sha256.json'}, indent=2))
    print(json.dumps(summary))
    if summary['status']!='passed': raise SystemExit(1)

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('out',type=Path); main(parser.parse_args().out)
