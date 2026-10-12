"""Static, resumable measurements for every acquired core-Wasm object.

Only WABT validators/disassemblers run; modules and upstream scripts never run.
All features are observations, not malware or obfuscation verdicts.
"""
import argparse
import collections
import concurrent.futures
import datetime
import hashlib
import json
import math
import re
import subprocess
import tempfile
import time
from pathlib import Path
from audit_corpora import ROOT, WABT, sections, uint32

VERSION = '2.1.0'
CACHE = ROOT / 'data' / 'analysis-v2'
OUT = ROOT / 'results' / 'corpus'
OP = re.compile(r'^\s*([0-9a-f]+):\s+(?:[0-9a-f]{2}\s+)+\|\s+([a-z][a-z0-9_.]*)\b(.*)$')
FUNC = re.compile(r'^([0-9a-f]+) func\[(\d+)\](.*):$')
STRINGS = re.compile(rb'[\x20-\x7e]{6,}')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def entropy(data):
    if not data:
        return None
    n = len(data)
    return -sum((v/n)*math.log2(v/n) for v in collections.Counter(data).values())


class Reader:
    def __init__(self, data):
        self.data, self.pos = data, 0

    def byte(self):
        if self.pos >= len(self.data):
            raise ValueError('truncated field')
        val = self.data[self.pos]
        self.pos += 1
        return val

    def uint(self):
        val, self.pos = uint32(self.data, self.pos)
        return val

    def text(self):
        n = self.uint()
        end = self.pos + n
        if end > len(self.data):
            raise ValueError('truncated string')
        val = self.data[self.pos:end].decode('utf-8')
        self.pos = end
        return val

    def leb(self):
        for _ in range(10):
            if not self.byte() & 128:
                return
        raise ValueError('oversized LEB')

    def limits(self):
        flags = self.uint()
        if flags & ~7:
            raise ValueError('unsupported limits flags')
        self.leb()
        if flags & 1:
            self.leb()

    def value_type(self):
        typ = self.byte()
        if typ in (0x63, 0x64):
            self.leb()


def interfaces(parsed):
    result = {'imports': [], 'exports': []}
    for sec in parsed:
        if sec['id'] not in (2, 7):
            continue
        r = Reader(sec['payload'])
        count = r.uint()
        for _ in range(count):
            if sec['id'] == 7:
                result['exports'].append({'name': r.text(), 'kind': r.byte(), 'index': r.uint()})
                continue
            item = {'module': r.text(), 'name': r.text(), 'kind': r.byte()}
            kind = item['kind']
            if kind == 0:
                item['type_index'] = r.uint()
            elif kind == 1:
                r.value_type(); r.limits()
            elif kind == 2:
                r.limits()
            elif kind == 3:
                r.value_type(); r.byte()
            elif kind == 4:
                r.byte(); r.uint()
            else:
                raise ValueError('unsupported import kind')
            result['imports'].append(item)
        if r.pos != len(r.data):
            raise ValueError('interface section not completely consumed')
    return result


def code_bodies(payload):
    n, pos = uint32(payload, 0)
    bodies = []
    for _ in range(n):
        size, pos = uint32(payload, pos)
        if pos + size > len(payload):
            raise ValueError('function body out of bounds')
        body = payload[pos:pos+size]
        bodies.append({'body_bytes': size, 'body_sha256': digest(body)})
        pos += size
    if pos != len(payload):
        raise ValueError('code section not completely consumed')
    return bodies


def parse_disassembly(lines):
    total, functions = collections.Counter(), []
    current, depth, loop_depth, seq, fops = None, 0, [], [], collections.Counter()

    def finish():
        if current is not None:
            current['instruction_count'] = sum(fops.values())
            current['opcodes'] = dict(fops)
            current['opcode_sequence_sha256'] = digest('\n'.join(seq).encode())
            functions.append(current.copy())

    for line in lines:
        fm = FUNC.match(line.strip())
        if fm:
            finish()
            current = {'function_index': int(fm[2]), 'offset': fm[1],
                       'max_control_depth': 0, 'br_table_in_loop': 0,
                       'max_br_table_targets': 0}
            depth, loop_depth, seq, fops = 0, [], [], collections.Counter()
            continue
        m = OP.match(line)
        if not m or m[2] == 'local':
            continue
        if current is None:
            raise ValueError('instruction before function header')
        op, args = m[2], m[3].strip()
        total[op] += 1; fops[op] += 1; seq.append(op)
        if op in ('block', 'loop', 'if', 'try', 'try_table'):
            depth += 1
            if op == 'loop':
                loop_depth.append(depth)
            current['max_control_depth'] = max(depth, current['max_control_depth'])
        elif op == 'end':
            if loop_depth and loop_depth[-1] == depth:
                loop_depth.pop()
            depth -= 1
        elif op == 'br_table':
            current['br_table_in_loop'] += bool(loop_depth)
            # WABT emits decoded target labels, including the default label.
            targets = sum(x.isdecimal() for x in args.split())
            current['max_br_table_targets'] = max(targets, current['max_br_table_targets'])
    finish()
    return dict(total), functions


def analyze(row, timeout=120):
    started = time.monotonic()
    result = {'sha256': row['sha256'], 'object': row['object'],
              'analyzer_version': VERSION, 'wabt_version': '1.0.42',
              'analyzed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    stage = 'read'
    temporary_input = None
    try:
        data = (ROOT / row['object']).read_bytes()
        if digest(data) != row['sha256']:
            raise ValueError('SHA-256 mismatch')
        result['bytes'] = len(data)
        stage = 'sections'
        parsed = sections(data)
        result['sections'] = [{k:s[k] for k in ('id','name','bytes')} for s in parsed]
        custom = [s for s in parsed if s['id'] == 0]
        result['name_section'] = any(s['name'] == 'name' for s in custom)
        result['custom_section_count'] = len(custom)
        result['custom_payload_bytes'] = sum(s['bytes'] for s in custom)
        core = data[:8] + b''.join(s['raw'] for s in parsed if s['id'] != 0)
        result['core_bytes_sha256'] = digest(core)
        code = b''.join(s['payload'] for s in parsed if s['id'] == 10)
        dp = b''.join(s['payload'] for s in parsed if s['id'] == 11)
        result.update(code_section_bytes=len(code), data_section_bytes=len(dp),
                      code_section_entropy=entropy(code), data_section_entropy=entropy(dp),
                      code_payload_sha256=digest(code), data_payload_sha256=digest(dp))
        strs = STRINGS.findall(dp)
        result.update(data_ascii_strings_count=len(strs), data_ascii_string_bytes=sum(map(len,strs)),
                      data_ascii_strings_preview=[s[:200].decode('ascii') for s in strs[:40]])
        try:
            result.update(interfaces(parsed)); result['interfaces_status'] = 'ok'
        except (ValueError, UnicodeError) as exc:
            result['interfaces_status'] = str(exc)
        bodies = code_bodies(code) if code else []
        result['defined_functions'] = len(bodies)
        stage = 'validation'
        valid = subprocess.run([str(WABT/'wasm-validate.exe'), '--enable-all', str(ROOT/row['object'])],
                               capture_output=True, timeout=timeout)
        result['valid_wabt'] = valid.returncode == 0
        disassembly_input = ROOT/row['object']
        result['disassembly_input'] = 'original'
        if valid.returncode:
            result['original_validation_error'] = valid.stderr.decode('utf-8',errors='replace')[:3000]
            # A custom-section convention can be malformed even when the core
            # module is valid. Preserve the original finding and test core bytes
            # separately; never call the original module valid on this basis.
            if custom:
                temporary_input = tempfile.TemporaryDirectory()
                disassembly_input = Path(temporary_input.name)/'core.wasm'
                disassembly_input.write_bytes(core)
                retry = subprocess.run([str(WABT/'wasm-validate.exe'),'--enable-all',str(disassembly_input)],
                                       capture_output=True,timeout=timeout)
                result['valid_wabt_without_custom_sections'] = retry.returncode == 0
                if retry.returncode == 0:
                    result['disassembly_input'] = 'without_custom_sections_offsets_differ'
                else:
                    result['core_validation_error'] = retry.stderr.decode('utf-8',errors='replace')[:3000]
            if result['disassembly_input'] == 'original':
                result.update(status='validation_failed', error=result['original_validation_error'])
                return result
        stage = 'disassembly'
        with tempfile.TemporaryFile(mode='w+b') as out:
            dis = subprocess.run([str(WABT/'wasm-objdump.exe'), '-d', str(disassembly_input)],
                                 stdout=out, stderr=subprocess.PIPE, timeout=timeout)
            if dis.returncode:
                raise ValueError(dis.stderr.decode('utf-8',errors='replace')[:3000])
            out.seek(0)
            ops, functions = parse_disassembly(line.decode('utf-8',errors='replace') for line in out)
        if len(functions) != len(bodies):
            raise ValueError(f'disassembly function count {len(functions)} != code section {len(bodies)}')
        for f, b in zip(functions, bodies):
            f.update(b)
        result.update(opcodes=ops, functions=functions, instruction_count=sum(ops.values()), status='ok')
        result['br_table_in_loop_count'] = sum(f['br_table_in_loop'] for f in functions)
        result['max_br_table_targets'] = max((f['max_br_table_targets'] for f in functions), default=0)
        result['max_control_depth'] = max((f['max_control_depth'] for f in functions), default=0)
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        result.update(status=stage+'_failed', error=str(exc))
    finally:
        if temporary_input is not None:
            temporary_input.cleanup()
        result['analysis_seconds'] = round(time.monotonic()-started, 4)
    return result


def acquired_rows(datasets=None, include_unhashed=False):
    rows = []
    for path in sorted((ROOT/'data/catalog').glob('*/acquisition.jsonl')):
        for line in path.read_text(encoding='utf-8').splitlines():
            row = json.loads(line)
            if datasets and row['dataset'] not in datasets and path.parent.name not in datasets:
                continue
            if row['path'].lower().endswith('.wasm') or row.get('wasm_magic'):
                if row.get('sha256') or include_unhashed:
                    rows.append(row)
    # Historical control extraction is a subset, explicitly kept separate.
    old = ROOT/'data/upstream/acquisition-manifest.json'
    if old.exists() and (not datasets or 'wasm-obf-controls' in datasets):
        for r in json.loads(old.read_text(encoding='utf-8')):
            if r['path'].endswith('.wasm'):
                rows.append({'dataset':'wasm-obf-controls','path':r['archive_entry'],
                             'object':r['path'],'sha256':r['sha256'],
                             'acquisition_status':'stored_verified'})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--datasets', nargs='*')
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--executor', choices=('threads','processes'), default='threads',
                    help='Processes permit CPU-bound parsing on several cores; measurements are unchanged')
    ap.add_argument('--timeout', type=int, default=120)
    ap.add_argument('--limit', type=int, help='Debug only; recorded as incomplete')
    ap.add_argument('--sha256-file', type=Path, help='Explicit hash selection; record scope in named run receipt')
    ap.add_argument('--run-name', help='Separate run receipt, so disjoint jobs do not overwrite each other')
    args = ap.parse_args()
    if args.run_name and not re.fullmatch(r'[a-zA-Z0-9_-]+',args.run_name):
        ap.error('--run-name must contain only letters, digits, underscores, and hyphens')
    if args.sha256_file and not args.run_name:
        ap.error('--sha256-file requires --run-name for an auditable partial-scope run')
    CACHE.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)
    allrows = acquired_rows(args.datasets)
    source_occurrences=len(allrows)
    selection_hash=None
    if args.sha256_file:
        selection_bytes=args.sha256_file.read_bytes()
        hashes=json.loads(selection_bytes)
        if not isinstance(hashes,list) or not all(isinstance(s,str) and re.fullmatch(r'[0-9a-f]{64}',s) for s in hashes):
            ap.error('hash selection must be a JSON list of SHA-256 strings')
        hashes=set(hashes)
        missing=hashes-{r['sha256'] for r in allrows}
        if missing:
            ap.error(f'{len(missing)} selected hashes are absent from acquired dataset scope')
        allrows=[r for r in allrows if r['sha256'] in hashes]
        selection_hash=digest(selection_bytes)
    unique = {r['sha256']:r for r in allrows}
    selected = list(unique.values())
    if args.limit:
        selected = selected[:args.limit]
    started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()
    receipt=OUT/'analysis-run.json'
    if args.run_name:
        receipt=OUT/'runs'/(args.run_name+'.json')
        receipt.parent.mkdir(parents=True,exist_ok=True)
        input_file=receipt.with_suffix('.inputs.jsonl')
        input_bytes=''.join(json.dumps(r)+'\n' for r in allrows).encode('utf-8')
        input_file.write_bytes(input_bytes)
    pending, counts = [], collections.Counter()
    for row in selected:
        dest = CACHE/(row['sha256']+'.json')
        if dest.exists():
            old = json.loads(dest.read_text(encoding='utf-8'))
            if old.get('analyzer_version') == VERSION or (old.get('analyzer_version') == '2.0.0' and old['status'] == 'ok'):
                counts[old['status']] += 1
                continue
        pending.append(row)
    print(f'{len(allrows)} occurrences; {len(unique)} unique; {len(pending)} pending',flush=True)
    last, done = time.monotonic(), len(selected)-len(pending)
    executor=(concurrent.futures.ProcessPoolExecutor if args.executor=='processes'
              else concurrent.futures.ThreadPoolExecutor)
    with executor(max_workers=args.workers) as pool:
        # Release completed Future results after persisting them. Retaining all
        # function-level dictionaries until the corpus finishes costs many GB.
        futures = {pool.submit(analyze, r, args.timeout) for r in pending}
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            dest = CACHE/(result['sha256']+'.json')
            temp = dest.with_suffix('.partial')
            temp.write_text(json.dumps(result,ensure_ascii=True), encoding='utf-8'); temp.replace(dest)
            counts[result['status']] += 1; done += 1
            futures.remove(future)
            if time.monotonic()-last > 20:
                print(f'{done}/{len(selected)} analyzed: {dict(counts)}',flush=True)
                last = time.monotonic()
    summary = {'analyzer_version':VERSION,'datasets_filter':args.datasets,
               'executor':args.executor,'workers':args.workers,'subprocess_timeout_seconds':args.timeout,
               'occurrences':len(allrows),'unique':len(unique),'attempted':len(selected),
               'debug_limit':args.limit,'status_counts':dict(counts),
               'started_utc':started_utc,'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'source_occurrences_before_hash_selection':source_occurrences,
               'selection_sha256':selection_hash,'selection_file':str(args.sha256_file) if args.sha256_file else None}
    if args.run_name:
        summary.update(input_manifest=input_file.relative_to(ROOT).as_posix(),input_manifest_sha256=digest(input_bytes))
    receipt.write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary),flush=True)


if __name__ == '__main__':
    main()
