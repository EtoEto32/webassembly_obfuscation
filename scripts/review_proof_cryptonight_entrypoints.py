"""Inspect published entry points and build sources; never execute Wasm/glue."""
import hashlib
import json
import re
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/runtime-mining/cross-dataset/proof-of-theft'
manifest = json.loads((OUT / 'glue-control-input.json').read_text())
sha = lambda b: hashlib.sha256(b).hexdigest()
records = []
with zipfile.ZipFile(ROOT / 'data/archives/proof-of-theft.zip') as archive:
    names = set(archive.namelist())
    for row in manifest['modules']:
        if row['family'] != 'cryptonight-hash':
            continue
        binary = (ROOT / row['object']).read_bytes()
        assert sha(binary) == row['sha256']
        prefix = row['path'].rsplit('/', 1)[0] + '/'
        sources = {}
        for name in ['build.sh', 'cryptonightnative.c', 'cryptonight.c', 'Makefile']:
            if prefix + name not in names:
                continue
            data = archive.read(prefix + name)
            text = data.decode('utf-8')
            target = OUT / 'cryptonight-entrypoint-sources' / sha(data)
            target.parent.mkdir(exist_ok=True)
            target.write_bytes(data)
            sources[name] = dict(archive_path=prefix + name, sha256=sha(data),
                                 saved=str(target.relative_to(ROOT)))
            if name == 'build.sh':
                sources[name]['command'] = text
            if name.endswith('.c'):
                match = re.search(r'int main\s*\([^)]*\)\s*\{', text)
                if match:
                    level = 1
                    end = match.end()
                    while level:
                        level += (text[end] == '{') - (text[end] == '}')
                        end += 1
                    sources[name]['main_source'] = text[match.start():end]
        wat = subprocess.check_output([
            str(ROOT / '.tools/wabt-1.0.42/bin/wasm2wat.exe'),
            str(ROOT / row['object']), '--generate-names'], text=True)
        functions = dict(re.findall(r'^  (\(func (\$[^\s()]+).*?)(?=\n  \(|\Z)',
                                     wat, flags=re.M | re.S))
        # Above regex pairs body/name; invert to use generated identifier keys.
        functions = {name: body for body, name in functions.items()}
        export = re.search(r'\(export "main" \(func (\$[^\s()]+)\)\)', wat)
        assert export
        main = functions[export[1]]
        calls = re.findall(r'\bcall (\$[^\s()]+)', main)
        inspected = [export[1]]
        if len(calls) == 1:
            inspected.append(calls[0])
        if '$f10' in functions and '$f10' in re.findall(
                r'\bcall (\$[^\s()]+)', functions[inspected[-1]]):
            inspected.append('$f10')
        bodies = []
        for name in inspected:
            body = functions[name]
            target = OUT / f"cryptonight-{row['sha256'][:12]}-{name[1:]}.wat.txt"
            target.write_text(body + '\n', encoding='utf-8')
            bodies.append(dict(function=name, declaration=body.splitlines()[0],
                text_lines=len(body.splitlines()),
                direct_calls=re.findall(r'\bcall (\$[^\s()]+)', body),
                excerpt=str(target.relative_to(ROOT)), excerpt_sha256=sha(target.read_bytes())))
        glue = (ROOT / row['glue']).read_bytes()
        assert sha(glue) == row['glue_sha256']
        record = dict(method=row['method'], path=row['path'], sha256=row['sha256'],
            sources=sources, exports=row['exports'], glue_sha256=sha(glue),
            glue_literal_hash_name_occurrences=glue.count(b'cryptonight_hash'),
            inspected_functions=bodies,
            conclusion='No exported per-input hash interface or literal cryptonight_hash wrapper was found. main is a distinct workload, not a substitute for public-vector validation.',
            next_step='After execution permission, establish the internal hash function correspondence and ABI, then evaluate a separately identified export-only derivative or controlled rebuild. Do not relabel the derivative as the unchanged published binary.')
        if len(inspected) == 3:
            record['internal_hash_candidate'] = dict(function='$f10',
                basis='main calls a no-argument wrapper, which calls f10; f10 has three i32 parameters, consistent with the distributed pointer/pointer/length hash declaration.',
                status='candidate only: full source-to-binary correspondence, input/output ABI, and independent hash output validation remain unproven')
        records.append(record)
report = dict(date='2026-10-08', scope='Seven selected uninstrumented published cryptonight-hash modules; static disassembly and archived sources only.',
    modules=records, limitations=[
        'No Wasm main, hash function, generated JavaScript, build script, or HTML was executed.',
        'Distributed build scripts specify cryptonightnative.c with an internal randomized 84-byte input loop; the separate cryptonight.c has an empty main and is not the listed build input.',
        'Distributed source/build commands do not alone prove the historical binary build or complete function equivalence.',
        'Missing a per-input export is an evaluation-interface limitation, not a wrong hash result or proof that internal hash code is absent.',
        'The encodearith main is structurally different and needs separate function/ABI recovery; no common function index is assumed.'])
(OUT / 'cryptonight-entrypoint-review.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(dict(modules=len(records), internal_candidates=sum('internal_hash_candidate' in x for x in records), executed_hashes=0)))
