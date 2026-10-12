"""Source/dependency feasibility review; no detector or target execution."""
import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results/countermeasures/detector-feasibility'


def main():
    files = json.loads((OUT/'source-manifest.json').read_text(encoding='utf-8'))
    for row in files:
        assert hashlib.sha256((ROOT/row['local_path']).read_bytes()).hexdigest() == row['sha256']
    modules = ['tensorflow', 'keras', 'PIL', 'numpy', 'h5py', 'sklearn', 'pandas', 'modin', 'pymongo']
    environment = dict(python=sys.version, executable=sys.executable,
                       modules={m: importlib.util.find_spec(m) is not None for m in modules},
                       docker_cli=shutil.which('docker'), redis_server=shutil.which('redis-server'),
                       scope='Availability check only. CLI presence does not prove a live service or image.')
    find = lambda name: next(r for r in files if r['local_path'].endswith('/'+name))
    source = find('wasm-obf-detection-minos-src-minio.py')
    text = (ROOT/source['local_path']).read_text(encoding='utf-8')
    assert "activation='softmax'" in text and "exit(int(predictions['MALIGN'].values[-1]))" in text
    examples = [dict(probability=p, integer_exit=int(p), argmax_class='MALIGN' if p > .5 else 'BENIGN' if p < .5 else 'TIE') for p in (.1, .49, .5, .51, .9, .999, 1.0)]
    assert int(.9) == 0
    lfs = find('wasim-Classifier_Modules-neuralNetwork.h5')
    pointer = (ROOT/lfs['local_path']).read_text(encoding='utf-8')
    assert pointer.startswith('version https://git-lfs.github.com/spec/v1')
    model_inventory = []
    for name, paths in [('wasm-obf', ['detection/minos/src/original23.h5']),
                        ('diversification2022', ['oracles/minos/original23.h5'])]:
        tree = json.loads((ROOT/'data/catalog'/name/'tree.json').read_text(encoding='utf-8'))
        for path in paths:
            item = next(r for r in tree['tree'] if r['path'] == path)
            model_inventory.append(dict(dataset=name, commit=tree['sha'], path=path,
                                        git_blob_sha1=item['sha'], catalog_bytes=item['size'],
                                        downloaded=False, model_load_checked=False))
    report = dict(environment=environment, source_manifest_sha256=hashlib.sha256((OUT/'source-manifest.json').read_bytes()).hexdigest(),
                  model_inventory=model_inventory,
                  minos_exit_review=dict(source=source, numerical_examples=examples,
                      finding='int(probability) is not argmax or a 0.5 decision. This source review does not establish how all published experiments were run or whether a particular model produces exact 0/1.'),
                  wasim_lfs_pointer=dict(source=lfs, text=pointer, actual_model_downloaded=False),
                  candidates=[
                      dict(name='MINOS reproduction', status='model catalog available; native dependencies missing; isolated inference adapter and model/threshold validation remain',
                           next='Retrieve and verify weights; pin inference dependencies separately; review architecture/preprocessing; report scores and labels separately from errors. Establish baseline validity and training/evaluation overlap before measuring improvement.'),
                      dict(name='MinerRay', status='parser source and dependency list available; Redis service/dependencies not prepared or verified',
                           next='Review parser side effects and acceptance criteria; run only offline WAT parsing in bounded isolated environment. Do not invoke URL crawling or consent checks.'),
                      dict(name='WASim', status='repository documents Ubuntu-specific Chromium and database/queue services; model catalog entry is LFS pointer',
                           next='Resolve model artifacts and service/version requirements; inspect whether feature extraction starts target Wasm before choosing a permitted offline route.'),
                      dict(name='VirusTotal', status='external upload/service is outside this local goal; not selected')],
                  detector_evaluated=False, target_wasm_executed=False,
                  scope='Feasibility/source review only. Missing dependencies are current setup facts, not proof that detectors are unreproducible. No accuracy, precision/recall or normalization benefit measured.')
    (OUT/'assessment.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('PASS: 14 source digests, dependency inventory, MINOS exit review and WASim LFS pointer; no detector executed')


if __name__ == '__main__':
    main()
