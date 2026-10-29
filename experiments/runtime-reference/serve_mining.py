"""Serve a local hash_cn ABI adaptation. No external pool is started here."""
import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from flask import Flask, Response, jsonify, request


def read_asset(path):
    with path.open('rb') as handle:
        return b''.join(iter(lambda: handle.read(4096), b''))


def create_app(module, module_sha256, threads, output, program):
    if hashlib.sha256(module).hexdigest() != module_sha256:
        raise ValueError('Input module digest mismatch')
    source = Path(__file__).resolve().parent
    root = source.parents[1]
    contracts = json.loads((root / 'results/runtime-mining/algorithm-contracts.json').read_text())
    contract = contracts[program]
    with (root / 'results/mining-methods/input-manifest.csv').open(encoding='utf-8') as handle:
        matches = [row for row in csv.DictReader(handle)
                   if row['sha256'] == module_sha256 and row['program'] == program]
    if not matches:
        raise ValueError('Module is not paired with the declared program in the source manifest')
    assets = {'module.wasm':(module, 'application/wasm')}
    for filename in ['hash-adapter.js', 'mining-worker.js', 'mining-client.js']:
        assets[filename] = (read_asset(source / filename), 'text/javascript')
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = 65536
    output.mkdir(parents=True, exist_ok=True)

    @app.after_request
    def restrict(response):
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; script-src 'self' 'wasm-unsafe-eval'; "
            "worker-src 'self'; connect-src 'self' ws://127.0.0.1:8892")
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.get('/')
    def page():
        return Response('<!doctype html><meta charset="utf-8"><title>Local Wasm mining experiment</title>'
            '<button id="mining-button-text">Start local experiment</button>'
            '<button id="stop-mining">Stop</button>'
            '<p>Status: <span id="runtime-status">idle</span></p>'
            '<p>Total hashes: <span id="hashes-total">0</span></p>'
            '<script src="/mining-client.js"></script>', mimetype='text/html')

    @app.get('/runtime-config.json')
    def config():
        return jsonify(threads=threads, algorithm=contract['algorithm'], contract=contract,
                       module_sha256=module_sha256, program=program)

    @app.get('/<filename>')
    def asset(filename):
        if filename not in assets:
            return Response(status=404)
        data, mime = assets[filename]
        return Response(data, mimetype=mime)

    @app.post('/events')
    def record():
        data = request.get_json()
        if not isinstance(data, dict):
            return Response(status=400)
        with (output / 'browser-events.jsonl').open('a', encoding='utf-8') as handle:
            handle.write(json.dumps({'utc':datetime.now(timezone.utc).isoformat(), 'data':data}) + '\n')
        return Response(status=204)

    return app


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--module', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--threads', type=int, required=True)
    parser.add_argument('--program', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--operator-confirmed-algorithm', action='store_true',
                        help='Only after the selected pool was verified to serve the selected program algorithm')
    args = parser.parse_args()
    if args.threads < 1 or not args.operator_confirmed_algorithm:
        parser.error('Explicit threads and operator-confirmed matching pool are required')
    create_app(read_asset(args.module), args.sha256, args.threads, args.output, args.program).run(
        host='127.0.0.1', port=7676, threaded=False, use_reloader=False)
