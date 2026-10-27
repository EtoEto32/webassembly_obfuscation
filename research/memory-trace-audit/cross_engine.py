"""Independent WABT-interpreter checks of the uninstrumented controls."""
import argparse
import json
from pathlib import Path
import re
import instrument as I


def expected(t, start, limit):
    if start >= t['nodes']:
        return {'trap': 'unreachable'}
    p, acc = t['addresses'][start], 0
    for _ in range(limit & 255):
        if not p:
            break
        i = (p - 256) // 16
        acc = (((acc << 5) | (acc >> 27)) ^ t['values'][i]) & 0xffffffff
        p = t['next'][i]
    return {'value_u32': acc}


def main(folder):
    output = folder / 'cross-engine.json'
    if output.exists():
        raise ValueError('Refuse overwrite')
    m = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
    records = []
    for row in m['rows']:
        p = folder / row['wasm']
        if I.sha(p) != row['sha256']:
            raise ValueError('Hash mismatch')
        t = m['truth'][row['family']]
        for a, b in [(t['head_index'], 0), (t['head_index'], 255), (t['nodes'] - 1, 123), (t['nodes'], 255)]:
            out = I.tool('wasm-interp', [p, '-r', 'run', '-a', 'i32:' + str(a), '-a', 'i32:' + str(b)]).strip()
            match = re.search(r'=> i32:(\d+)$', out)
            got = {'value_u32': int(match.group(1))} if match else (
                {'trap': 'unreachable'} if out.endswith('=> error: unreachable executed') else {'unparsed': out})
            want = expected(t, a, b)
            records.append({'wasm': row['wasm'], 'args': [a, b], 'stdout': out,
                            'expected': want, 'got': got, 'equal': got == want})
    result = {'executions': len(records), 'mismatches': sum(not x['equal'] for x in records),
              'engine': I.tool('wasm-interp', ['--version']).strip(),
              'script_sha256': I.sha(__file__), 'manifest_sha256': I.sha(folder / 'manifest.json'),
              'scope': 'Uninstrumented controls only; Python reference independent of JS checker.', 'records': records}
    output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('executions', 'mismatches', 'engine')}))
    if result['mismatches']:
        raise SystemExit(1)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('folder', type=Path)
    main(ap.parse_args().folder)
