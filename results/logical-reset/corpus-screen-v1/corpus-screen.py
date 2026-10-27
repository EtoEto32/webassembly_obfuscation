"""Read-only coarse applicability screen; never executes third-party modules."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time
import prototype as p


class Reader:
    def __init__(self, data): self.data, self.i = data, 0
    def byte(self):
        if self.i >= len(self.data): raise ValueError('truncated')
        v = self.data[self.i]; self.i += 1; return v
    def leb(self):
        value = 0
        for shift in range(0, 35, 7):
            b = self.byte(); value |= (b & 127) << shift
            if b < 128: return value
        raise ValueError('u32 LEB too long')
    def take(self, n):
        if self.i+n > len(self.data): raise ValueError('truncated')
        v = self.data[self.i:self.i+n]; self.i += n; return v


def screen(data):
    r = Reader(data)
    if r.take(8) != b'\0asm\1\0\0\0': raise ValueError('not core v1')
    sections = {}
    while r.i < len(data):
        kind = r.byte(); payload = r.take(r.leb())
        if kind: sections[kind] = payload
    reasons = []
    if 2 in sections and Reader(sections[2]).leb(): reasons.append('imports')
    if 8 in sections: reasons.append('start')
    if 7 in sections:
        ex = Reader(sections[7])
        for _ in range(ex.leb()):
            name = ex.take(ex.leb()); kind = ex.byte(); ex.leb()
            if kind != 0: reasons.append('state-export')
            if name.startswith(b'__lr_'): reasons.append('reserved-export')
    mem = Reader(sections.get(5, b'\0'))
    if mem.leb() != 1: reasons.append('memory-count')
    else:
        flags = mem.leb()
        if flags != 1: reasons.append('unbounded-or-non-memory32')
        else:
            lo, hi = mem.leb(), mem.leb()
            if not 0 <= lo <= hi <= 256: reasons.append('memory-cap')
    return sorted(set(reasons))


def main(corpus, out):
    out.mkdir(parents=True, exist_ok=False)
    shutil.copy2(__file__, out/'corpus-screen.py')
    rows = []; start = time.perf_counter()
    # Cross-check the coarse parser against accepted and unsupported local examples.
    examples = {'(module (memory 0 1))': [],
                '(module (memory (export "m") 0 1))': ['state-export'],
                '(module (memory 0))': ['unbounded-or-non-memory32']}
    for i, (wat, reasons) in enumerate(examples.items()):
        path = out/f'parser-control-{i}.wasm'; p.compile_wat(wat, path)
        assert screen(path.read_bytes()) == reasons
    for src in sorted(corpus.glob('*.wasm')):
        data = src.read_bytes()
        row = {'file': src.name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
        command = [str(p.w.WABT/'wasm-validate.exe'), str(src)]
        try:
            result = subprocess.run(command, capture_output=True, text=True, encoding='utf8', timeout=30)
            row.update(validationReturncode=result.returncode, validationDiagnostic=result.stderr)
            if result.returncode:
                row['status'] = 'validator-rejected'
            else:
                row['reasons'] = screen(data)
                row['status'] = 'unsupported-interface' if row['reasons'] else 'needs-full-transform'
        except subprocess.TimeoutExpired:
            row['status'] = 'validation-timeout'
        except ValueError as error:
            row.update(status='screen-parser-error', error=str(error))
        rows.append(row)
    counts = dict(Counter(x['status'] for x in rows))
    reasons = dict(Counter(k for x in rows for k in x.get('reasons', [])))
    result = {'counts': counts, 'reasonCounts': reasons, 'rows': rows,
              'seconds': time.perf_counter()-start,
              'note': 'Only interface/memory coarse rejection; passing is not accepted support. No module execution or edits. Validator diagnostics are separate from unsupported scope.'}
    (out/'results.json').write_text(json.dumps(result, indent=2), encoding='utf8')
    (out/'sha256.json').write_text(json.dumps({x.name: hashlib.sha256(x.read_bytes()).hexdigest() for x in out.iterdir() if x.is_file()}, indent=2), encoding='utf8')
    print(json.dumps({'counts': counts, 'reasonCounts': reasons}))


if __name__ == '__main__':
    a = argparse.ArgumentParser(); a.add_argument('corpus', type=Path); a.add_argument('out', type=Path)
    v = a.parse_args(); main(v.corpus, v.out)
