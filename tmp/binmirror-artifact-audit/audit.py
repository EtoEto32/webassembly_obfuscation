"""Read the pinned ZIP as data; never import or execute archive modules."""
import ast
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent
ARCHIVE = ROOT / 'Project_BinMirror.zip'
EXPECTED = 'f605218124e927f9bf446442601dac060505e84c13e8ef6a7768af334c1bcb42'
SELECTED = [
    'README.md', 'config.yaml', 'binmirror/models.py',
    'binmirror/utils/binary_parser.py', 'binmirror/utils/emulator.py',
    'binmirror/phase4_verify/harness.py', 'binmirror/phase4_verify/differ.py',
    'binmirror/phase4_verify/verifier.py', 'experiments/run_evaluation.py',
]


def function(source, name):
    return next(n for n in ast.walk(ast.parse(source))
                if isinstance(n, ast.FunctionDef) and n.name == name)


def dict_keys(node):
    return sorted({key.value for d in ast.walk(node) if isinstance(d, ast.Dict)
                   for key in d.keys if isinstance(key, ast.Constant)
                   and isinstance(key.value, str)})


def main():
    archive = ARCHIVE.read_bytes()
    assert hashlib.sha256(archive).hexdigest() == EXPECTED
    assert hashlib.md5(archive).hexdigest() == 'ca648d22980449425282530d771b3387'
    with zipfile.ZipFile(ARCHIVE) as z:
        members = [{'name': i.filename, 'bytes': i.file_size} for i in z.infolist()]
        sources = {n: z.read('Project_BinMirror/' + n).decode('utf-8') for n in SELECTED}
        # Search all core Python source, rather than just selected snippets.
        core = {n: z.read(n).decode('utf-8') for n in z.namelist()
                if n.startswith('Project_BinMirror/binmirror/') and n.endswith('.py')}
    evidence = ROOT / 'source-text'
    evidence.mkdir(exist_ok=True)
    for name, source in sources.items():
        (evidence / (name.replace('/', '__') + '.txt')).write_text(source, encoding='utf-8')
    emitted = dict_keys(function(sources['binmirror/phase4_verify/verifier.py'], 'save_results'))
    metric = function(sources['experiments/run_evaluation.py'], 'compute_pass_at_1')
    metric_keys = sorted({n.args[0].value for n in ast.walk(metric)
                         if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                         and n.func.attr == 'get' and n.args
                         and isinstance(n.args[0], ast.Constant)})
    tests = function(sources['experiments/run_evaluation.py'], 'run_unit_tests')
    attrs = sorted({n.attr for n in ast.walk(tests) if isinstance(n, ast.Attribute)})
    assert 'unit_test_passed' in metric_keys and 'unit_test_passed' not in emitted
    assert 'stdout' not in attrs and 'stderr' not in attrs
    result = {
        'kind': 'static-source-audit-not-runtime-test',
        'archive_sha256': EXPECTED, 'archive_bytes': len(archive),
        'member_count': len(members),
        'uncompressed_bytes': sum(m['bytes'] for m in members),
        'selected_source_sha256': {n: hashlib.sha256(s.encode()).hexdigest() for n,s in sources.items()},
        'metadata_emitted_keys': emitted, 'pass_at_1_consumed_keys': metric_keys,
        'missing_metric_keys': sorted(set(metric_keys) - set(emitted)),
        'unit_test_function_attribute_names': attrs,
        'core_python_files_searched': len(core),
        'wasm_webassembly_text_hits': [n for n,s in core.items() if 'wasm' in s.lower() or 'webassembly' in s.lower()],
        'decision': 'Do not use unmodified artifact as Wasm attack comparator or published-result reproduction.',
        'limits': 'No author code, model, emulator, or dataset was executed. Static audit does not invalidate all paper results.',
    }
    (ROOT / 'members.json').write_text(json.dumps(members, indent=2), encoding='utf-8')
    (ROOT / 'results.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
