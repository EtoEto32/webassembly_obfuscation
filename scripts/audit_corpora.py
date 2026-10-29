"""Offline corpus overlap audit and static first-pass analysis.

Git-tree identity and downloaded SHA-256 evidence are reported separately.
Neither a module nor an upstream loader is executed. WABT only validates and
disassembles bytes. Structural features are NOT obfuscation/malware labels.
"""
import collections
import csv
import hashlib
import itertools
import json
import re
import statistics
import subprocess
from pathlib import Path
from acquire import ROOT

OUT = ROOT / 'results' / 'pilot'
WABT = ROOT / '.tools' / 'wabt-1.0.42' / 'bin'


def write_csv(name, rows):
    if not rows:
        return
    fields = list(dict.fromkeys(k for r in rows for k in r))
    with (OUT / name).open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)


def uint32(data, pos):
    value = 0
    for i in range(5):
        if pos >= len(data):
            raise ValueError('truncated LEB128')
        byte = data[pos]; pos += 1
        if i == 4 and byte & 0xf0:
            raise ValueError('u32 LEB128 overflow')
        value |= (byte & 0x7f) << (7 * i)
        if not byte & 0x80:
            return value, pos
    raise ValueError('u32 LEB128 too long')


def sections(data):
    if data[:8] != b'\x00asm\x01\x00\x00\x00':
        raise ValueError('not a core Wasm v1 module')
    result = []
    pos = 8
    while pos < len(data):
        start = pos
        ident = data[pos]; pos += 1
        size, pos = uint32(data, pos)
        end = pos + size
        if end > len(data):
            raise ValueError('section extends beyond file')
        payload = data[pos:end]
        name = None
        if ident == 0:
            n, p = uint32(payload, 0)
            if p + n > len(payload):
                raise ValueError('custom-section name extends beyond payload')
            name = payload[p:p+n].decode('utf-8', errors='replace')
        result.append({'id': ident, 'bytes': size, 'payload': payload,
                       'raw': data[start:end], 'name': name})
        pos = end
    return result


def metadata_audit():
    inventories, membership = {}, []
    for file in sorted((ROOT / 'data/catalog').glob('*/tree.json')):
        tree = json.loads(file.read_text(encoding='utf-8'))
        if tree.get('truncated'):
            raise ValueError('Incomplete Git tree: ' + str(file))
        ident = file.parent.name
        blobs = [r for r in tree['tree'] if r['type'] == 'blob' and r['path'].endswith('.wasm')]
        inventories[ident] = blobs
        for r in blobs:
            membership.append({'dataset': ident, 'commit': tree['sha'], 'path': r['path'],
                               'git_blob': r['sha'], 'bytes': r['size']})
    write_csv('repository-membership.csv', membership)
    overlaps = []
    for a, b in itertools.combinations(sorted(inventories), 2):
        sa = {x['sha'] for x in inventories[a]}; sb = {x['sha'] for x in inventories[b]}
        overlaps.append({'dataset_a': a, 'dataset_b': b, 'unique_a': len(sa), 'unique_b': len(sb),
                         'shared_git_blob_ids': len(sa & sb),
                         'scope': 'repository .wasm paths only; not release archives or submodules'})
    write_csv('repository-overlap.csv', overlaps)
    wm = inventories['wasmmal']; sw = inventories['swamped']
    groups = {key: {r['sha'] for r in wm if r['path'].startswith(prefix)} for key, prefix in
              [('train','Data_NewSplit/train/'),('test','Data_NewSplit/test/'),('benign','benign/'),('malware','malware/')]}
    a = {r['sha'] for r in sw if r['path'].startswith('experimental_data/Cryptojackers_43/')}
    b = {r['sha'] for r in sw if r['path'].startswith('experimental_data/Malware_31/')}
    summary = {'wasmmal': {'path_count': len(wm), 'unique_git_blob_ids': len({x['sha'] for x in wm}),
               'groups': {k:len(v) for k,v in groups.items()},
               'train_test_exact_overlap': len(groups['train'] & groups['test']),
               'benign_malware_exact_overlap': len(groups['benign'] & groups['malware']),
               'root_and_split_same_content_set': groups['train'] | groups['test'] == groups['benign'] | groups['malware']},
               'swamped_seed_groups': {'cryptojackers': len(a), 'malware': len(b),
               'shared_exact': len(a & b), 'union_unique': len(a | b),
               'shared_with_wasmmal_malware': len((a|b) & groups['malware']),
               'shared_with_wasmmal_benign': len((a|b) & groups['benign'])}}
    (OUT / 'metadata-summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    return inventories, summary


def analyze(row):
    path = ROOT / row['object']
    result = {'sha256': row['sha256'], 'object': row['object']}
    try:
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != row['sha256']:
            raise ValueError('SHA-256 mismatch')
        result.update(bytes=len(data), magic=data[:4] == b'\0asm')
        parsed = sections(data)
        custom = [x for x in parsed if x['id'] == 0]
        result.update(section_count=len(parsed), custom_section_count=len(custom),
                      custom_payload_bytes=sum(x['bytes'] for x in custom),
                      custom_names=json.dumps([x['name'] for x in custom]),
                      name_section=any(x['name'] == 'name' for x in custom),
                      core_bytes_sha256=hashlib.sha256(data[:8] + b''.join(x['raw'] for x in parsed if x['id'] != 0)).hexdigest())
        code = [x for x in parsed if x['id'] == 10]
        result['code_payload_sha256'] = hashlib.sha256(code[0]['payload']).hexdigest() if len(code) == 1 else ''
        result['defined_functions'] = uint32(code[0]['payload'], 0)[0] if len(code) == 1 else 0
        valid = subprocess.run([str(WABT / 'wasm-validate.exe'), '--enable-all', str(path)],
                               capture_output=True, timeout=30)
        result['valid_wabt'] = valid.returncode == 0
        if valid.returncode:
            result['status'] = 'wabt_validation_failed'
            result['error'] = valid.stderr.decode('utf-8', errors='replace')[:1500]
            return result
        dis = subprocess.run([str(WABT / 'wasm-objdump.exe'), '-d', str(path)], capture_output=True, timeout=30)
        if dis.returncode:
            raise ValueError('disassembly failed: ' + dis.stderr.decode('utf-8',errors='replace')[:200])
        ops = collections.Counter()
        for line in dis.stdout.decode('utf-8', errors='replace').splitlines():
            m = re.match(r'^\s*[0-9a-f]+:\s+(?:[0-9a-f]{2}\s+)+\|\s+([a-z][a-z0-9_.]*)\b', line)
            if m and m[1] != 'local':
                ops[m[1]] += 1
        result['instruction_count'] = sum(ops.values())
        for op in ['br_table','call_indirect','call','loop','if','br','br_if','nop']:
            result[op + '_count'] = ops[op]
        result['status'] = 'ok'
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        result.update(status='unavailable_or_analysis_failed', error=str(exc))
    return result


def static_audit(inventories):
    manifest = ROOT / 'data/catalog/swamped/acquisition.jsonl'
    if not manifest.exists():
        manifest = manifest.with_suffix('.jsonl.partial')
    verified = [json.loads(line) for line in manifest.read_text(encoding='utf-8').splitlines()]
    by_blob = {r['git_blob']: r for r in verified}
    inputs, coverage = [], []
    for r in inventories['swamped']:
        if not r['path'].startswith('experimental_data/'):
            continue
        v = by_blob.get(r['sha'])
        rec = {'dataset': 'swamped', 'group': r['path'].split('/')[1], 'path': r['path'], 'git_blob': r['sha']}
        if v:
            rec.update(sha256=v['sha256'], object=v['object'], source_evidence='downloaded bytes verified against Git blob')
            inputs.append(rec)
        else:
            rec['source_evidence'] = 'tree only; acquisition interrupted before first copy verified'
        coverage.append(rec)
    for r in json.loads((ROOT / 'data/upstream/acquisition-manifest.json').read_text(encoding='utf-8')):
        if not r['path'].endswith('.wasm'):
            continue
        rec = {'dataset':'wasm-obf-controls', 'group':'flatten' if '/flatten/' in r['path'] else 'original',
               'path':r['archive_entry'], 'object':r['path'], 'sha256':r['sha256'],
               'source_evidence':'downloaded release entry SHA-256'}
        coverage.append(rec); inputs.append(rec)
    outputs = {key:analyze(r) for key,r in {x['sha256']:x for x in inputs}.items()}
    for r in coverage:
        r['status'] = outputs[r['sha256']]['status'] if r.get('sha256') else 'not_acquired'
    write_csv('binary-features.csv', list(outputs.values()))
    write_csv('analysis-membership.csv', coverage)
    summaries = []
    for ds, group in sorted({(x['dataset'],x['group']) for x in coverage}):
        members = [r for r in coverage if r['dataset'] == ds and r['group'] == group]
        ok = {r['sha256']:outputs[r['sha256']] for r in members if r['status'] == 'ok'}
        summaries.append({'dataset':ds, 'group':group, 'paths':len(members), 'analyzed_unique':len(ok),
                          'unavailable_paths':sum(r['status'] != 'ok' for r in members),
                          'name_section_present':sum(x['name_section'] for x in ok.values()),
                          'br_table_present':sum(x['br_table_count'] > 0 for x in ok.values()),
                          'indirect_call_present':sum(x['call_indirect_count'] > 0 for x in ok.values()),
                          'median_defined_functions':statistics.median([x['defined_functions'] for x in ok.values()]) if ok else None})
    write_csv('feature-summary.csv', summaries)
    return {'unique_inputs':len(outputs), 'status_counts':dict(collections.Counter(r['status'] for r in outputs.values())),
            'group_summaries':summaries}


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    inventories, metadata = metadata_audit()
    summary = {'metadata':metadata, 'static':static_audit(inventories)}
    (OUT / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))
