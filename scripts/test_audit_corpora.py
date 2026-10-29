"""Independent checks for the measurements used in the pilot."""
import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path
from audit_corpora import ROOT, WABT, analyze, sections, uint32


class StaticMeasurementTests(unittest.TestCase):
    def test_truncated_and_overflow_leb_rejected(self):
        for data in [b'\x80', b'\xff\xff\xff\xff\x10', b'\x80'*6]:
            with self.assertRaises(ValueError):
                uint32(data, 0)
        self.assertEqual(uint32(b'\xe5\x8e\x26', 0), (624485, 3))

    def test_invalid_boundaries_rejected(self):
        header = b'\0asm\x01\0\0\0'
        for data in [header + b'\x01\x10x', header + b'\x00\x01\x08']:
            with self.assertRaises(ValueError):
                sections(data)

    def test_against_wabt_generated_fixture_and_strip(self):
        temp_root = ROOT / 'data' / 'verification'
        temp_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temp_root) as folder:
            wat = Path(folder) / 'inc.wat'
            wasm = Path(folder) / 'inc.wasm'
            stripped = Path(folder) / 'stripped.wasm'
            wat.write_text('(module (func $inc (param $n i32) (result i32) local.get $n i32.const 1 i32.add) (export "inc" (func $inc)))')
            subprocess.run([str(WABT/'wat2wasm.exe'), '--debug-names', str(wat), '-o', str(wasm)], check=True, capture_output=True)
            data = wasm.read_bytes()
            measured = analyze({'object':str(wasm.relative_to(ROOT)), 'sha256':hashlib.sha256(data).hexdigest()})
            self.assertEqual(measured['status'], 'ok')
            self.assertEqual(measured['instruction_count'], 4)
            self.assertEqual(measured['defined_functions'], 1)
            self.assertEqual(measured['call_indirect_count'], 0)
            self.assertEqual(measured['br_table_count'], 0)
            self.assertTrue(measured['name_section'])
            subprocess.run([str(WABT/'wasm-strip.exe'), str(wasm), '-o', str(stripped)], check=True, capture_output=True)
            self.assertEqual(measured['core_bytes_sha256'], hashlib.sha256(stripped.read_bytes()).hexdigest())


if __name__ == '__main__':
    unittest.main()
