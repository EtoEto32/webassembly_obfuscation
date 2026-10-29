"""Known-answer checks against small independently specified WAT modules."""
import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path
from analyze_corpus import ROOT, WABT, analyze, entropy


class CorpusMeasurements(unittest.TestCase):
    def make_and_measure(self, wat, malformed_custom=False):
        with tempfile.TemporaryDirectory(dir=ROOT/'data') as folder:
            p = Path(folder)/'test.wat'; binary=p.with_suffix('.wasm')
            p.write_text(wat,encoding='utf-8')
            subprocess.run([str(WABT/'wat2wasm.exe'),'--debug-names',str(p),'-o',str(binary)],
                           check=True,capture_output=True)
            if malformed_custom:
                name = b'target_features'
                payload = bytes([len(name)])+name+b'\x01\x2b\x7f'
                with binary.open('ab') as out:
                    out.write(b'\x00'+bytes([len(payload)])+payload)
            return analyze({'object':str(binary.relative_to(ROOT)),
                            'sha256':hashlib.sha256(binary.read_bytes()).hexdigest()})

    def test_known_interfaces_and_control_structure(self):
        result=self.make_and_measure('''(module
          (import "env" "log" (func $log (param i32)))
          (memory (export "mem") 1) (data (i32.const 0) "hello world")
          (func (export "f") (param i32)
            (block (loop local.get 0 br_table 0 1))
            i32.const 3 call $log))''')
        self.assertEqual(result['status'],'ok')
        self.assertEqual(result['defined_functions'],1)
        self.assertEqual(result['opcodes']['br_table'],1)
        self.assertEqual(result['br_table_in_loop_count'],1)
        self.assertEqual(result['max_br_table_targets'],2)
        self.assertEqual(result['max_control_depth'],2)
        # block, loop, local.get, br_table, end, end, const, call, function end
        self.assertEqual(result['instruction_count'],9)
        self.assertEqual(result['imports'][0]['name'],'log')
        self.assertEqual([x['name'] for x in result['exports']],['mem','f'])
        self.assertIn('hello world',result['data_ascii_strings_preview'])

    def test_malformed_custom_metadata_kept_distinct_from_core(self):
        result=self.make_and_measure('(module (func (export "f") nop))',True)
        self.assertEqual(result['status'],'ok')
        self.assertFalse(result['valid_wabt'])
        self.assertTrue(result['valid_wabt_without_custom_sections'])
        self.assertEqual(result['opcodes']['nop'],1)
        self.assertEqual(result['disassembly_input'],'without_custom_sections_offsets_differ')

    def test_entropy_known_values(self):
        self.assertEqual(entropy(b'aaaa'),0)
        self.assertEqual(entropy(bytes(range(256))),8)
        self.assertIsNone(entropy(b''))


if __name__=='__main__': unittest.main()
