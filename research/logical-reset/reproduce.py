"""Re-run the supported differential, ablation and performance experiments."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def main(out):
    out = out.resolve(); out.mkdir(parents=True, exist_ok=False)
    sources = out/'sources'; sources.mkdir()
    for path in HERE.iterdir():
        if path.is_file(): shutil.copy2(path, sources/path.name)
    shutil.copy2(ROOT/'research/connectivity-elimination/prototype.py', sources/'wat-common.py')
    steps = [('run.py', out/'probe'), ('cross.py', out/'probe', out/'cross'),
             ('boundary.py', out/'boundary'), ('bench-inputs.py', out/'probe', out/'bench-inputs'),
             ('bench.py', out/'bench-inputs', out/'performance')]
    logs = []
    try:
        for script, *args in steps:
            cmd = [sys.executable, str(HERE/script), *map(str,args)]
            run = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding='utf8', timeout=600)
            logs.append({'command':cmd, 'returncode':run.returncode, 'stdout':run.stdout, 'stderr':run.stderr})
            (out/'steps.json').write_text(json.dumps(logs, indent=2), encoding='utf8')
            print(json.dumps({'step':script, 'returncode':run.returncode}), flush=True)
            if run.returncode: raise RuntimeError(script+' failed; see steps.json')
    finally:
        hashes = {x.relative_to(out).as_posix(): hashlib.sha256(x.read_bytes()).hexdigest()
                  for x in out.rglob('*') if x.is_file()}
        (out/'sha256.json').write_text(json.dumps(hashes, indent=2), encoding='utf8')


if __name__ == '__main__':
    a = argparse.ArgumentParser(); a.add_argument('out', type=Path); main(a.parse_args().out)
