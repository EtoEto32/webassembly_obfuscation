"""Reconstruct distributed RQ3 WAT and check named binary identity; no execution."""
import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'data/upstream/wasm_evasion/malware_reproduction/rq3/replace_experiments/coinhive-32bits'
DEST = ROOT / 'data/reconstructed/rq3'
OUT = ROOT / 'results/runtime-mining'


def main():
    compiler = ROOT / '.tools/wabt-1.0.42/bin/wat2wasm.exe'
    candidates = (sorted((SRC / 'allmal/works_here').glob('*.wat'))
                  + sorted((SRC / 'variants').rglob('*.wat'))
                  + sorted((SRC / 'mcmc').rglob('*.wat')))
    rows = []
    for wat in candidates:
        named = re.match(r'([a-f0-9]{64})\.', wat.name)
        relative = wat.relative_to(SRC)
        is_mcmc = relative.parts[0] == 'mcmc'
        if not named and not is_mcmc:
            continue
        expected = named.group(1) if named else None
        wasm = DEST / relative.with_suffix('')
        wasm.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run([str(compiler), str(wat), '-o', str(wasm)], capture_output=True, text=True)
        actual = hashlib.sha256(wasm.read_bytes()).hexdigest() if result.returncode == 0 else None
        row = dict(source=str(relative), source_sha256=hashlib.sha256(wat.read_bytes()).hexdigest(),
                   object=str(wasm.relative_to(ROOT)), named_sha256=expected, actual_sha256=actual,
                   matches_named_binary=actual == expected if expected else None, compiler_status=result.returncode,
                   compiler_diagnostic=result.stderr[:2000],
                   role='original' if relative.parts[0] == 'allmal' else 'variant',
                   parent_prefix=relative.parts[1] if relative.parts[0] in ('variants', 'mcmc') else expected[:8],
                   source_commit='6e41bb3fa0f9d06619758709094b0e2a13beb593',
                   execution_status='not run',
                   algorithm_group='MCMC' if is_mcmc else 'baseline collection branch' if relative.parts[0] == 'variants' else 'original',
                   sigma=relative.parts[2] if is_mcmc else '',
                   group_evidence='collect_mcmc.sh: mcmc/$ORIG, sigma-specific filename selection' if is_mcmc else
                       'collect.sh: variants/$ORIG; plot.sh passes out/$ORIG to baselines argument' if relative.parts[0] == 'variants' else 'collect.sh ORIGINALS')
        rows.append(row)
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / 'reference-reconstruction.csv').open('w', encoding='utf-8', newline='') as h:
        w = csv.DictWriter(h, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    summary = dict(candidates=len(rows), originals=sum(r['role'] == 'original' for r in rows),
                   variants=sum(r['role'] == 'variant' for r in rows),
                   successful_compilations=sum(r['compiler_status'] == 0 for r in rows),
                   exact_named_binary_matches=sum(r['matches_named_binary'] is True for r in rows),
                   mcmc_candidates=sum(r['algorithm_group'] == 'MCMC' for r in rows),
                   mcmc_sigma_03_candidates=sum(r['sigma'] == '0.3' for r in rows),
                   limitations=['Original six-program 120-variant evaluation is not yet fully matched.',
                                'Collection-branch labels do not prove all generation parameters or the complete ten-variant groups.',
                                'Reconstruction does not establish mining correctness.'])
    (OUT / 'reference-reconstruction-summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
