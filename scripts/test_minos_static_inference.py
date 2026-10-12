"""Independent NumPy forward calculation and preprocessing checks, no Wasm run."""
import json
from pathlib import Path
import hashlib
import h5py
import numpy as np
import PIL
from PIL import Image
from minos_static_inference import ROOT, OUT, model, pixels, tf


def numpy_forward(x):
    with h5py.File(OUT/'wasm-obf-original23.h5', 'r') as f:
        x = x.reshape(100, 100, 1)
        for name in ('conv2d', 'conv2d_1', 'conv2d_2'):
            group = f[f'model_weights/{name}/{name}']
            kernel, bias = group['kernel:0'][:], group['bias:0'][:]
            windows = np.lib.stride_tricks.sliding_window_view(x, (3, 3), axis=(0, 1))
            # window axes H,W,C,KH,KW; stored kernels KH,KW,C,F.
            x = np.maximum(np.einsum('hwcij,ijcf->hwf', windows, kernel, optimize=True)+bias, 0)
            h, w, c = x.shape
            x = x[:h//2*2, :w//2*2].reshape(h//2, 2, w//2, 2, c).max(axis=(1, 3))
        group = f['model_weights/dense/dense']
        logits = x.ravel() @ group['kernel:0'][:] + group['bias:0'][:]
        exp = np.exp(logits-logits.max())
        return exp/exp.sum()


def main():
    target = model()
    rng = np.random.default_rng(20261010)
    inputs = [np.zeros((1, 10000), np.float32), np.full((1, 10000), 255, np.float32),
              np.full((1, 10000), 127.5, np.float32)]
    inputs += [rng.random((1, 10000), dtype=np.float32)*255 for _ in range(5)]
    records = []
    for index, x in enumerate(inputs):
        a = target(x, training=False).numpy()[0]
        b = numpy_forward(x)
        error = float(np.max(np.abs(a-b)))
        assert np.allclose(a, b, rtol=1e-4, atol=1e-5), (index, a, b)
        assert int(np.argmax(a)) == int(np.argmax(b))
        records.append(dict(input_sha256=hashlib.sha256(x.tobytes()).hexdigest(),
                            tensorflow_scores=a.tolist(), numpy_scores=b.tolist(), max_absolute_error=error))
    preprocess_records = []
    for size in (8, 101, 10201, 74099):
        data = rng.integers(0, 256, size, dtype=np.uint8).tobytes()
        width = int(np.sqrt(size)); height = size//width
        raw = np.frombuffer(data[:width*height], dtype=np.uint8).reshape(height, width)
        expected = np.asarray(Image.fromarray(raw).resize((100, 100), resample=Image.Resampling.BICUBIC)).astype(np.float32).ravel()
        actual = pixels(data)[0]
        assert np.array_equal(actual, expected)
        preprocess_records.append(dict(bytes=size, unused_tail_bytes=size-width*height, equal=True))
    report = dict(passed=True, synthetic_forward_cases=records, preprocessing_cases=preprocess_records,
                  versions=dict(tensorflow=tf.__version__, keras=tf.keras.__version__, numpy=np.__version__, h5py=h5py.__version__, pillow=PIL.__version__),
                  adapter_sha256=hashlib.sha256((ROOT/'scripts/minos_static_inference.py').read_bytes()).hexdigest(),
                  model_sha256=hashlib.sha256((OUT/'wasm-obf-original23.h5').read_bytes()).hexdigest(),
                  target_wasm_executed=False, detector_performance_evaluated=False,
                  scope='Eight synthetic images compare reviewed TensorFlow reconstruction with independent NumPy convolution/pooling/dense calculation; four byte lengths check image encoding. Not equality to historical runtime, model training provenance, general accuracy or normalization benefit.')
    (OUT/'inference-adapter-checks.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('PASS: 8 independent forward cases and 4 byte-image checks; no Wasm execution')


if __name__ == '__main__':
    main()
