"""Retrieve fixed small HDF5 weights; inspect JSON metadata without deserialization.

No Keras load_model, pickle, upstream script or target Wasm execution.
"""
import hashlib
import json
import sys
import urllib.request
from pathlib import Path
import h5py
import numpy as np
import PIL

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results/countermeasures/detector-feasibility'
MODEL_PATH = 'detection/minos/src/original23.h5'


def main():
    tree = json.loads((ROOT/'data/catalog/wasm-obf/tree.json').read_text(encoding='utf-8'))
    item = next(x for x in tree['tree'] if x['path'] == MODEL_PATH)
    target = OUT/'wasm-obf-original23.h5'
    url = f'https://raw.githubusercontent.com/hakonharnes/wasm-obf/{tree["sha"]}/{MODEL_PATH}'
    if target.exists():
        data = target.read_bytes()
    else:
        assert item['size'] < 1000000
        with urllib.request.urlopen(url, timeout=30) as response:
            data = response.read(1000001)
    assert len(data) == item['size']
    blob = hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    assert blob == item['sha'] and data.startswith(b'\x89HDF\r\n\x1a\n')
    target.write_bytes(data)
    with h5py.File(target, 'r') as model:
        config = json.loads(model.attrs['model_config'])
        tensors = []
        def visit(name, value):
            if isinstance(value, h5py.Dataset):
                tensors.append(dict(path=name, shape=list(value.shape), dtype=str(value.dtype)))
        model.visititems(visit)
        attributes = {k: str(model.attrs[k]) for k in model.attrs if k != 'model_config'}
    layers = config['config']['layers']
    allowed = {'InputLayer', 'Reshape', 'Conv2D', 'MaxPooling2D', 'Flatten', 'Dense'}
    assert all(layer['class_name'] in allowed for layer in layers)
    report = dict(repository='hakonharnes/wasm-obf', commit=tree['sha'], path=MODEL_PATH,
                  url=url, git_blob_sha1=blob, sha256=hashlib.sha256(data).hexdigest(),
                  bytes=len(data), model_config=config, attributes=attributes, tensors=tensors,
                  environment=dict(python=sys.version, h5py=h5py.__version__, numpy=np.__version__, pillow=PIL.__version__),
                  model_inference_executed=False, target_wasm_executed=False,
                  scope='HDF5 metadata and dataset shapes only. No model deserialization, TensorFlow inference or target instantiation. Architecture allowlist is a prerequisite, not a compatibility proof.')
    (OUT/'model-inspection.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(dict(bytes=len(data), layers=[x['class_name'] for x in layers], tensors=tensors)))


if __name__ == '__main__':
    main()
