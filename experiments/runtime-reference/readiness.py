"""Offline integration check of publisher glue and existing Wasm; no hashes/jobs."""
import hashlib
import json
import threading
from pathlib import Path
from flask import Flask, Response
from werkzeug.serving import make_server
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

app = Flask(__name__)
MODULE = Path('/inputs/module.wasm')
ADAPTER = Path('/inputs/hash-adapter.js')
ASSETS = {}


def read_asset(path):
    with path.open('rb') as handle:
        return b''.join(iter(lambda: handle.read(4096), b''))


@app.route('/')
def page():
    return Response('''<!doctype html><meta charset="utf-8"><title>Wasm readiness only</title>
<p id="status">loading</p><script src="/readiness-client.js"></script>''', mimetype='text/html')


@app.route('/readiness-client.js')
def client():
    return Response('''const w = new Worker('/readiness-worker.js');
w.onmessage = e => { document.querySelector('#status').textContent = JSON.stringify(e.data); };
w.onerror = e => { document.querySelector('#status').textContent = JSON.stringify({status:'error',message:e.message}); };''', mimetype='application/javascript')


@app.route('/readiness-worker.js')
def worker():
    return Response('''importScripts('/hash-adapter.js');
createHashAdapter('/module.wasm').then(adapter => {
 postMessage({status:'ready', hash_export:typeof adapter.hash,
 wasm_exports:adapter.exports, wasm_executed:'initialization only; hash_cn not called'});
}).catch(error => postMessage({status:'error', message:String(error)}));''', mimetype='application/javascript')


@app.route('/module.wasm')
def wasm():
    return Response(ASSETS['module'], mimetype='application/wasm')


@app.route('/hash-adapter.js')
def adapter():
    return Response(ASSETS['adapter'], mimetype='application/javascript')


@app.after_request
def restrict(response):
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'wasm-unsafe-eval' 'unsafe-eval'; worker-src 'self'; connect-src 'self'"
    return response


def main():
    # Fail before starting if Docker networking is not disabled.
    routes = Path('/proc/net/route').read_text().splitlines()[1:]
    if any(line.split()[1] == '00000000' for line in routes):
        raise RuntimeError('Offline readiness check requires --network none')
    # Immutable inputs are loaded and digested before launching Chromium.
    try:
        ASSETS['module'] = read_asset(MODULE)
    except OSError as error:
        diagnostic = {'stage': 'module-read', 'errno': error.errno,
                      'message': str(error), 'hashes_measured': False,
                      'pool_connected': False, 'network': 'none'}
        try:
            diagnostic['module_stat_size'] = MODULE.stat().st_size
        except OSError:
            diagnostic['module_stat_size'] = None
        for name in ('memory.max', 'memory.current', 'memory.events'):
            path = Path('/sys/fs/cgroup') / name
            if path.exists():
                diagnostic[name] = path.read_text().strip()
        print(json.dumps(diagnostic), flush=True)
        raise
    ASSETS['adapter'] = read_asset(ADAPTER)
    server = make_server('127.0.0.1', 7676, app)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    options = webdriver.ChromeOptions()
    for arg in ('--headless=new', '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage',
                '--disable-background-networking', '--disable-extensions'):
        options.add_argument(arg)
    driver = webdriver.Chrome(options=options)
    try:
        driver.get('http://127.0.0.1:7676')
        WebDriverWait(driver, 45).until(lambda d: d.find_element(By.ID, 'status').text != 'loading')
        result = json.loads(driver.find_element(By.ID, 'status').text)
        result.update(module_sha256=hashlib.sha256(ASSETS['module']).hexdigest(),
                      adapter_sha256=hashlib.sha256(ASSETS['adapter']).hexdigest(),
                      browser_version=driver.capabilities.get('browserVersion'),
                      network='none', pool_connected=False, hashes_measured=False)
        print(json.dumps(result), flush=True)
        if result['status'] != 'ready':
            raise RuntimeError('Wasm/glue initialization failed')
    finally:
        driver.quit()
        server.shutdown()


if __name__ == '__main__':
    main()
