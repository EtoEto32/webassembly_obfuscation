"""Independent small WAT fixtures for resource audit, never instantiated."""
import json
import subprocess
from pathlib import Path
from audit_corpora import WABT
from audit_normalization_resources import resources
from evaluate_local_normalization import ROOT, sha


def main():
    out = ROOT/'results/countermeasures/resource-audit-tests'
    out.mkdir(exist_ok=True)
    fixtures = {
        'baseline': '(module (memory (export "m") 1 2) (table (export "t") 1 3 funcref) (global (export "g") (mut i32) (i32.const 11)))',
        'memory_max': '(module (memory (export "m") 1 4) (table (export "t") 1 3 funcref) (global (export "g") (mut i32) (i32.const 11)))',
        'table_min': '(module (memory (export "m") 1 2) (table (export "t") 2 3 funcref) (global (export "g") (mut i32) (i32.const 11)))',
        'global_mutability': '(module (memory (export "m") 1 2) (table (export "t") 1 3 funcref) (global (export "g") i32 (i32.const 11)))',
        'global_type': '(module (memory (export "m") 1 2) (table (export "t") 1 3 funcref) (global (export "g") (mut i64) (i64.const 11)))',
        'initializer_only': '(module (memory (export "m") 1 2) (table (export "t") 1 3 funcref) (global (export "g") (mut i32) (i32.const 12)))',
        'import_offset': '(module (import "env" "a" (global i32)) (global (export "g") (mut i64) (i64.const 11)))',
    }
    parsed, records = {}, []
    for name, text in fixtures.items():
        wat, wasm = out/(name+'.wat'), out/(name+'.wasm')
        wat.write_text(text, encoding='utf-8')
        subprocess.run([str(WABT/'wat2wasm.exe'), str(wat), '-o', str(wasm)], check=True, capture_output=True)
        subprocess.run([str(WABT/'wasm-validate.exe'), str(wasm)], check=True, capture_output=True)
        parsed[name] = resources(wasm.read_bytes())
        records.append(dict(name=name, sha256=sha(wasm), resources=parsed[name]))
    base = parsed['baseline']['exported_resources']
    for name in ('memory_max', 'table_min', 'global_mutability', 'global_type'):
        assert parsed[name]['exported_resources'] != base, name
    assert parsed['initializer_only']['exported_resources'] == base
    assert parsed['import_offset']['exported_resources'][0]['type'] == dict(value_type='i64', mutable=True)
    for payload in (b'\x04\x00', b'\x02\x00'):
        from analyze_corpus import Reader
        from audit_normalization_resources import limits
        try:
            limits(Reader(payload))
        except ValueError:
            pass
        else:
            raise AssertionError('unsupported limits accepted')
    (out/'checks.json').write_text(json.dumps(dict(passed=True, records=records, runtime_executed=False,
        assertions=8, test_sha256=sha(Path(__file__)), evaluator_sha256=sha(ROOT/'scripts/audit_normalization_resources.py'),
        scope='Four changed resource declarations detected; initializer changes deliberately outside scope; global export index includes imported global; unsupported limits rejected.'), indent=2), encoding='utf-8')
    print('PASS: 7 WABT-validated fixtures, 8 assertions, no module execution')


if __name__ == '__main__':
    main()
