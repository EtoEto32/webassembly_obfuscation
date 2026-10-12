"""Load only the pinned pure Python modules; no repository startup hooks."""
import importlib.util
import pathlib
import sys
import types
import unittest

root = pathlib.Path(__file__).resolve().parent
for name in ('security_tests', 'security_tests.gadgetization'):
    mod = types.ModuleType(name)
    mod.__path__ = []
    sys.modules[name] = mod

def load(name, file):
    spec = importlib.util.spec_from_file_location(name, root / file)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

load('security_tests.gadgetization.nonlinear193', 'nonlinear193.py')
load('security_tests.gadgetization.nonlinear291', 'security_tests__gadgetization__nonlinear291.py')
tests = load('pinned_author_tests', 'tests__python__gadgetization__test_nonlinear_gadgets.py')
suite = unittest.defaultTestLoader.loadTestsFromModule(tests)
with (root / 'author-tests.txt').open('w', encoding='utf-8') as stream:
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
print((root / 'author-tests.txt').read_text(encoding='utf-8'))
raise SystemExit(0 if result.wasSuccessful() else 1)
