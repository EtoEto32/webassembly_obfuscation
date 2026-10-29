"""Read-only diagnosis of the existing Docker bind mount; no Wasm execution."""
import json
import os
import hashlib
from pathlib import Path

module = Path('/inputs/module.wasm')
result = {'wasm_executed': False, 'network_used': False, 'security_settings_changed': False}
try:
    info = module.stat()
    result['stat_size'] = info.st_size
    result['mode'] = oct(info.st_mode)
    with module.open('rb') as stream:
        result['fstat_size'] = os.fstat(stream.fileno()).st_size
except OSError as error:
    result['read_error'] = {'errno': error.errno, 'message': str(error)}
for strategy in ('read-all', 'read-4096'):
    try:
        digest = hashlib.sha256()
        total = 0
        with module.open('rb') as stream:
            if strategy == 'read-all':
                data = stream.read()
                digest.update(data)
                total = len(data)
            else:
                while True:
                    data = stream.read(4096)
                    if not data:
                        break
                    digest.update(data)
                    total += len(data)
        result[strategy] = {'bytes': total, 'sha256': digest.hexdigest()}
    except OSError as error:
        result[strategy] = {'errno': error.errno, 'message': str(error)}
for name in ('memory.max', 'memory.current', 'memory.events'):
    source = Path('/sys/fs/cgroup') / name
    if source.exists():
        result[name] = source.read_text().strip()
print(json.dumps(result), flush=True)
