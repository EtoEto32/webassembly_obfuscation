"""Guard against falsely assigning generated binaries to a source program."""
import unittest
from audit_release_parents import parse_release_path
from summarize_corpus import annotate


class ReleaseProvenanceTests(unittest.TestCase):
    def test_transformation_and_filename_must_agree(self):
        categories={'game':'games'}
        valid=parse_release_path('binaries-opt/game/tigress/flatten/game.wasm',categories)
        self.assertEqual(valid['parent_id'],'wasm-obf/program/game')
        for bad in ['binaries/game/unobfuscated/other.wasm',
                    'binaries/unknown/unobfuscated/unknown.wasm',
                    'binaries/game/tigress/game.wasm',
                    'binaries/game/unobfuscated/extra/game.wasm']:
            with self.assertRaises(ValueError):
                parse_release_path(bad,categories)

    def test_android_apk_label_is_not_wasm_transform(self):
        row={'dataset':'androwasm','sha256':'example',
             'path':'itasec/case_studies/obfuscated/ransomware_stringEnc.apk!/assets/module_crypto_ransom.wasm'}
        result=annotate(row,{},set())
        self.assertEqual(result['author_label'],'ransomware_poc')
        self.assertEqual(result['transformation'],'unknown')
        self.assertEqual(result['provenance'],'author_generated_poc')

    def test_js_dependency_is_not_assumed_translated_malware(self):
        result=annotate({'dataset':'wobfuscator','sha256':'example','path':'project/node_modules/probe.js#1',
                         'source_js_path':'project/node_modules/probe.js','dependency_path':True}, {},set())
        self.assertEqual(result['author_label'],'unlabeled')
        self.assertEqual(result['provenance'],'packaged_dependency')


if __name__=='__main__':
    unittest.main()
