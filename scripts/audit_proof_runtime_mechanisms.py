"""Join build provenance, static features, reviewed mechanism and runtime evidence."""
import collections
import hashlib
import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/runtime-mining/cross-dataset/proof-of-theft'


def function_excerpt(file, name):
    text = file.read_text()
    start = text.index('  (func $' + name + ' ')
    end = text.find('\n  (func ', start + 1)
    return text[start:end], text[:start].count('\n') + 1


def main():
    spec = json.loads((OUT / 'glue-control-input.json').read_text())
    checks = json.loads((OUT / 'original-glue-public-vector-check-corrected-20261008.json').read_text())
    by_sha = {x['sha256']: x for x in checks['results']}
    rows = []
    with zipfile.ZipFile(ROOT / 'data/archives/proof-of-theft.zip') as archive:
        for module in spec['modules']:
            cache = json.loads((ROOT / 'data/analysis-v2' / (module['sha256'] + '.json')).read_text())
            build = module['path'].rsplit('/', 1)[0] + '/Makefile'
            data = archive.read(build)
            flags = sorted(set(re.findall(r'-enable-[A-Za-z0-9_-]+', data.decode(errors='replace'))))
            expected = next((v for k, v in [('flattening', '-enable-cffobf'), ('substitution', '-enable-subobf'),
                            ('split', '-enable-splitobf'), ('boguscf', '-enable-bcfobf')]
                            if 'emccobf-' + k in module['method']), None)
            conflict = (expected is not None and bool(flags) and expected not in flags)
            if module['method'] == 'webminerpoolhashcn' and flags:
                conflict = True
            check = by_sha[module['sha256']]
            rows.append(dict(path=module['path'], sha256=module['sha256'], family=module['family'],
                             declared_directory=module['method'], build_source=build,
                             build_sha256=hashlib.sha256(data).hexdigest(), build_flags=flags,
                             optimization_flags=re.findall(r'-O[0-3szg]', data.decode(errors='replace')),
                             expected_flag_from_directory=expected, label_build_conflict=conflict,
                             interpretation='directory/build inconsistency; actual transformation unresolved' if conflict
                             else ('build setting corroborated; inspect binary mechanism separately' if flags
                                   else 'no transformation flag established by this Makefile; inspect other build scripts'),
                             bytes=cache['bytes'], instructions=cache['instruction_count'],
                             br_table_in_loop=cache['br_table_in_loop_count'],
                             wasabi_hook_imports=any(i['module'] == '__wasabi_hooks' for i in cache['imports']),
                             public_vector_status=check['status'], public_vectors_checked=len(check['outputs']),
                             mechanism_status='not independently confirmed for this complete module'))
    original, _ = function_excerpt(OUT / 'xmr-original.wat', 'hash')
    flattened, first = function_excerpt(OUT / 'xmr-flattening.wat', 'hash')
    # These are witnesses for a manually reviewed path, not a generic classifier.
    witnesses = ['i32.const -518616621', 'i32.store offset=8', 'loop $L0',
                 'i32.load offset=8', 'i32.load offset=4', 'i32.const 573433544', 'br $L0']
    assert all(w in flattened for w in witnesses)
    assert 'i32.const -518616621' not in original
    excerpt_path = OUT / 'xmr-hash-flattening-reviewed.wat.txt'
    excerpt_path.write_text(flattened + '\n')
    evidence = dict(sha256='5335175e6c9a0e9c0374391e372063b20877d70db921fc3ea802b3926df788e1',
                    function='hash', wat_first_line=first, excerpt=excerpt_path.name,
                    scope='Exported mining wrapper only; not a complete review of all transformed functions',
                    observed='Stack offset 8 stores dispatcher state. Offset 4 stores its address; branches write states through that pointer and return to loop L0.',
                    contrast='Original wrapper follows the source nonce/target loop without the reviewed generated state-dispatch mechanism.',
                    witnesses=witnesses, branch_table_in_reviewed_function='br_table' in flattened,
                    correctness='Three applicable public CN/0 vectors matched using original generated glue',
                    limitation='This is path/mechanism inspection plus finite output checks, not a proof of semantic equivalence for all inputs.')
    for row in rows:
        if row['sha256'] == evidence['sha256']:
            row['mechanism_status'] = 'state-based flattening confirmed in exported hash wrapper'
            row['mechanism_evidence'] = 'runtime-mechanism-audit.json:reviewed_flattening'
    result = dict(modules=rows, reviewed_flattening=evidence,
                  main_findings=['Five webminerpoolhashcn Makefiles carry the same -enable-bcfobf flag, including the reference directory.',
                                 'Folder names do not establish four distinct transformations or an unobfuscated reference.',
                                 'xmr-wasm flattening wrapper has a verified state dispatcher but no br_table in the inspected function.'],
                  historical_control_evidence='results/rq-validation/instrumentation-removal-check.json')
    (OUT / 'runtime-mechanism-audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'reviewed_modules': len(rows), 'label_build_conflicts': sum(r['label_build_conflict'] for r in rows),
                      'confirmed_flattening_sha': evidence['sha256'], 'reviewed_function_has_br_table': evidence['branch_table_in_reviewed_function']}))


if __name__ == '__main__':
    main()
