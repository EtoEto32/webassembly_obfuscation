"""Child-process watchdog; never runs the full upstream tool."""
import hashlib
import json
import platform
import subprocess
import time
from pathlib import Path

root = Path(__file__).resolve().parent
exe = root / 'target' / 'debug' / 'extraction-audit.exe'
output = root / 'results.json'
if output.exists():
    raise SystemExit('Preserve results; use a fresh directory.')
rows = []
for mode in ('positive', 'negative', 'one-rule', 'unmatched'):
    for repeat in range(2):
        start = time.perf_counter()
        p = subprocess.Popen([str(exe), mode], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        timed_out = False
        try:
            out, err = p.communicate(timeout=3)
        except subprocess.TimeoutExpired:
            timed_out = True
            p.kill()
            out, err = p.communicate()
        row = dict(mode=mode, repeat=repeat, timed_out=timed_out, returncode=p.returncode,
                   elapsed_s=time.perf_counter()-start,
                   stdout=out.decode('utf-8', errors='replace'), stderr=err.decode('utf-8', errors='replace'))
        rows.append(row)
        print(json.dumps({k: row[k] for k in ('mode', 'repeat', 'timed_out', 'returncode', 'elapsed_s')}), flush=True)
output.write_text(json.dumps(dict(python=platform.python_version(), timeout_s=3,
    exe_sha256=hashlib.sha256(exe.read_bytes()).hexdigest(), rows=rows), indent=2)+'\n', encoding='utf-8')
