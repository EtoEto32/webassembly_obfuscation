"""Offline fixed-architecture MINOS inference; never instantiate target Wasm.

Rebuild reviewed layers explicitly; read numeric HDF5 weights, not model code.
This adapter fixes argmax interpretation; it does not reproduce integer exit codes.
"""
import os
os.environ.setdefault('CUDA_VISIBLE_DEVICES', '-1')
os.environ.setdefault('TF_NUM_INTRAOP_THREADS', '1')
os.environ.setdefault('TF_NUM_INTEROP_THREADS', '1')
os.environ.setdefault('TF_ENABLE_ONEDNN_OPTS', '0')
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '2')
import hashlib
import json
import math
from pathlib import Path
import h5py
import numpy as np
from PIL import Image
import tensorflow as tf

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results/countermeasures/detector-feasibility'
CLASSES = ('MALIGN', 'BENIGN')


def pixels(data):
    if not 8 <= len(data) <= 32*1024*1024:
        raise ValueError('Unsupported byte length')
    width = math.isqrt(len(data))
    height = len(data)//width
    # Reproduce reviewed source: bytes beyond width*height are not represented.
    image = Image.frombuffer('L', (width, height), data)
    image = image.resize((100, 100))
    # The reviewed single-file path calls get_pixels, which returns uint8,
    # not encode(), which divides by 255. Preserve that source path's scale.
    return np.asarray(image).astype(np.float32).reshape(1, 10000)


def model():
    report = json.loads((OUT/'model-inspection.json').read_text(encoding='utf-8'))
    path = OUT/'wasm-obf-original23.h5'
    assert hashlib.sha256(path.read_bytes()).hexdigest() == report['sha256']
    layers = report['model_config']['config']['layers']
    with h5py.File(path, 'r') as f:
        assert json.loads(f.attrs['model_config']) == report['model_config']
    assert [x['class_name'] for x in layers] == ['InputLayer', 'Reshape', 'Conv2D', 'MaxPooling2D', 'Conv2D', 'MaxPooling2D', 'Conv2D', 'MaxPooling2D', 'Flatten', 'Dense']
    assert layers[0]['config']['batch_input_shape'] == [None, 10000]
    assert layers[1]['config']['target_shape'] == [100, 100, 1]
    result = tf.keras.Sequential([tf.keras.Input(shape=(10000,)), tf.keras.layers.Reshape((100, 100, 1))])
    for index, filters in enumerate((16, 32, 64)):
        config = layers[2+index*2]['config']
        assert config['filters'] == filters and config['kernel_size'] == [3, 3]
        assert config['padding'] == 'valid' and config['activation'] == 'relu'
        assert config['strides'] == [1, 1] and config['dilation_rate'] == [1, 1]
        assert config['groups'] == 1 and config['use_bias'] and config['data_format'] == 'channels_last'
        pool = layers[3+index*2]['config']
        assert pool['pool_size'] == [2, 2] and pool['strides'] == [2, 2]
        assert pool['padding'] == 'valid' and pool['data_format'] == 'channels_last'
        result.add(tf.keras.layers.Conv2D(filters, 3, activation='relu', name=config['name']))
        result.add(tf.keras.layers.MaxPooling2D(2))
    assert layers[8]['config']['data_format'] == 'channels_last'
    assert layers[9]['config']['units'] == 2 and layers[9]['config']['activation'] == 'softmax' and layers[9]['config']['use_bias']
    result.add(tf.keras.layers.Flatten())
    result.add(tf.keras.layers.Dense(2, activation='softmax', name='dense'))
    with h5py.File(path, 'r') as f:
        for name in ('conv2d', 'conv2d_1', 'conv2d_2', 'dense'):
            group = f[f'model_weights/{name}/{name}']
            arrays = [np.asarray(group[k]) for k in ('kernel:0', 'bias:0')]
            assert all(a.dtype == np.float32 and np.isfinite(a).all() for a in arrays)
            result.get_layer(name).set_weights(arrays)
    return result


def predict(model, data):
    image = pixels(data)
    scores = model(image, training=False).numpy()[0]
    features = tf.keras.Model(model.inputs, model.layers[-2].output)(image, training=False)
    dense = model.layers[-1]
    logits = (tf.linalg.matmul(features, dense.kernel)+dense.bias).numpy()[0]
    assert np.isfinite(logits).all()
    assert np.isfinite(scores).all() and abs(float(scores.sum())-1) < 1e-5
    index = int(np.argmax(scores))
    return dict(probabilities={name: float(value) for name, value in zip(CLASSES, scores)},
                logits={name: float(value) for name, value in zip(CLASSES, logits)},
                malign_minus_benign_logit=float(logits[0]-logits[1]),
                predicted_class=CLASSES[index], decision='argmax; ties use first class MALIGN',
                target_wasm_executed=False)
