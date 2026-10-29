"""Analyze a real .wasm file for the restricted candidate-B host contract.

The JSON is a locally derived analysis result, not a cryptographic proof.
The embedding must still enforce single-thread/exclusive-memory assumptions.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import time
import tempfile
import effects

HERE = Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('boundary',HERE/'boundary.py')
b=importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('wasm',type=Path)
    ap.add_argument('output',type=Path)
    ap.add_argument('--analyzer',choices=['acyclic-v1','restricted-v1'],default='acyclic-v1')
    a=ap.parse_args()
    start=time.perf_counter()
    # Read exactly once: validation, analysis and the digest concern the same
    # bytes even if the original pathname is replaced during certification.
    data=a.wasm.read_bytes()
    with tempfile.TemporaryDirectory(prefix='wasm-contract-',dir=a.output.resolve().parent) as tmp:
        binary=Path(tmp)/'input.wasm';binary.write_bytes(data)
        b.p.w.tool('wasm-validate',[binary])
        module=b.p.w.parse(b.p.w.tool('wasm2wat',[binary,'--fold-exprs']))
        result=(effects.summary if a.analyzer=='acyclic-v1' else b.summary)(module)
    analyzer_path=HERE/('effects.py' if a.analyzer=='acyclic-v1' else 'boundary.py')
    value={'schema':'restricted-snapshot-contract-v1','wasm_sha256':hashlib.sha256(data).hexdigest(),
           'analyzer':a.analyzer,'analyzer_source_sha256':b.p.digest(analyzer_path),
           'export':'callback','signature':'(i32,i32,i32)->()','memory_export':'memory',
           'required_embedding':['nonshared memory32','exclusive writer interval through view consumption','trusted host','frozen read set and arguments','instantiate the exact certified bytes','recheck untrusted summaries'],
           'analysis':result,'validation_and_analysis_ms':(time.perf_counter()-start)*1000}
    with a.output.open('x',encoding='utf8') as f:
        json.dump(value,f,indent=2)
    print(json.dumps(value))
