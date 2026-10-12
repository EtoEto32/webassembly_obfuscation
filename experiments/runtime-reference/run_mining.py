"""One reference-method mining run, after explicit pool verification.

Run in the prepared Linux environment. This script does not select a pool,
create wallets, change the input Wasm, or weaken host security settings.
"""
import argparse
import csv
import hashlib
import json
import os
import platform
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

SOURCE = Path(__file__).resolve().parent
ROOT = SOURCE.parents[1]


def save(path, value):
    path.write_text(json.dumps(value, indent=2), encoding='utf-8')


def digest_file(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(4096), b''):
            digest.update(block)
    return digest.hexdigest()


def configuration(path, digest, threads):
    config = json.loads(path.read_text(encoding='utf-8-sig'))
    if threads < 1:
        raise ValueError('An explicit positive thread count is required')
    if config.get('operator_verified') is not True:
        raise ValueError('Current operator conditions and algorithm must be verified first')
    if not config.get('operator_source_url') or not config.get('verified_date'):
        raise ValueError('Record the operator source and verification date')
    if (config.get('user_owned_identifier') is not True
            or not isinstance(config.get('address'), str) or not config['address'].strip()):
        raise ValueError('The user must supply their own public payout identifier')
    if not isinstance(config.get('port'), int) or not 1 <= config['port'] <= 65535:
        raise ValueError('Invalid pool port')
    if not isinstance(config.get('host'), str) or not config['host'].strip():
        raise ValueError('Missing pool hostname')
    if '://' in config['host'] or '/' in config['host']:
        raise ValueError('Provide a hostname, not a URL')
    with (ROOT / 'results/mining-methods/input-manifest.csv').open(encoding='utf-8-sig') as handle:
        matches = [row for row in csv.DictReader(handle) if row['sha256'] == digest]
    if len(matches) != 1:
        raise ValueError('Input must identify exactly one manifest row')
    row = matches[0]
    contracts = json.loads((ROOT / 'results/runtime-mining/algorithm-contracts.json').read_text())
    if config.get('algorithm') != contracts[row['program']]['algorithm']:
        raise ValueError('Pool algorithm differs from the source contract')
    module = ROOT / row['object']
    if digest_file(module) != digest:
        raise ValueError('Module digest mismatch')
    proxy = ROOT / '.tools/xmrig-proxy-6.18.0/xmrig-proxy-6.18.0/xmrig-proxy'
    provenance = json.loads((ROOT / 'results/runtime-mining/proxy-provenance.json').read_text(encoding='utf-8-sig'))
    if digest_file(proxy) != provenance['binary_sha256']:
        raise ValueError('Proxy differs from the checked official binary')
    return config, row, module, proxy


def wait_local(port, process):
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError('Component exited before becoming ready; see process log')
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=1):
                return
        except OSError:
            time.sleep(0.2)
    raise TimeoutError('Local component did not become ready')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pool-config', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--threads', type=int, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--validate-only', action='store_true')
    args = parser.parse_args()
    config, row, module, proxy = configuration(args.pool_config, args.sha256, args.threads)
    if args.validate_only:
        print(json.dumps({'status':'configuration-validated', 'program':row['program'],
                          'network_used':False, 'mining_executed':False}))
        return
    if platform.system() != 'Linux':
        raise RuntimeError('Use the prepared Linux environment; this proxy is a Linux binary')
    # Refuse to collide with unrelated services. Binding uses loopback only.
    for port in (3333, 7676, 8892):
        with socket.socket() as probe:
            probe.bind(('127.0.0.1', port))
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    metadata = dict(input_sha256=args.sha256, baseline_sha256=row['baseline_sha256'],
                    program=row['program'], release=row['release'], method=row['method'],
                    synthetic=False, status='starting', threads=args.threads,
                    started_utc=datetime.now(timezone.utc).isoformat(),
                    algorithm=config['algorithm'], pool_host=config['host'], pool_port=config['port'],
                    operator_source_url=config['operator_source_url'], verified_date=config['verified_date'],
                    software_platform=platform.platform(), python_version=platform.python_version(),
                    docker_image_id=os.environ.get('EXPERIMENT_IMAGE_ID'),
                    methodology='1001 nominal one-second samples; retain samples[10:]',
                    runtime='Adapted hash_cn runtime, not original CoinHive; one hash per worker message')
    metadata['component_sha256'] = {
        name:digest_file(SOURCE / name)
        for name in ('run_mining.py', 'collect_reference.py', 'serve_mining.py', 'bridge.cjs',
                     'bridge-instrumentation.cjs', 'hash-adapter.js', 'mining-worker.js', 'mining-client.js')}
    metadata['proxy_sha256'] = digest_file(proxy)
    metadata['input_io'] = 'Same readonly file read in 4096-byte blocks; full digest checked before measurement'
    save(output / 'run-metadata.json', metadata)
    pool = {'algo':config['algorithm'], 'coin':None,
            'url':config['host'] + ':' + str(config['port']), 'user':config['address'],
            'pass':config.get('pass', 'x'), 'keepalive':False, 'enabled':True,
            'tls':config.get('tls', False), 'daemon':False}
    proxy_config = {'background':False, 'donate-level':0, 'mode':'simple',
                    'bind':[{'host':'127.0.0.1', 'port':3333, 'tls':False}],
                    'http':{'enabled':False}, 'tls':{'enabled':False}, 'pools':[pool], 'watch':False,
                    'colors':False, 'title':False, 'syslog':False, 'verbose':True,
                    'log-file':str(output / 'proxy.log'), 'retries':2, 'retry-pause':1}
    save(output / 'xmrig-proxy.json', proxy_config)
    save(output / 'bridge.json', {'proxyHost':'127.0.0.1', 'proxyPort':3333,
                                 'address':config['address'], 'pass':config.get('pass', 'x'),
                                 'logDirectory':str(output)})
    commands = [
        [str(proxy), '--config', str(output / 'xmrig-proxy.json')],
        ['node', str(SOURCE / 'bridge.cjs'), str(output / 'bridge.json')],
        [sys.executable, '-P', str(SOURCE / 'serve_mining.py'), '--module', str(module),
         '--sha256', args.sha256, '--threads', str(args.threads), '--program', row['program'],
         '--output', str(output), '--operator-confirmed-algorithm'],
        [sys.executable, '-P', str(SOURCE / 'collect_reference.py'), '--output', str(output)]
    ]
    save(output / 'commands.json', commands)
    processes, logs = [], []
    try:
        for index, (command, port) in enumerate(zip(commands[:3], (3333, 8892, 7676))):
            log = (output / ('component-' + str(index) + '.log')).open('w', encoding='utf-8')
            logs.append(log)
            process = subprocess.Popen(command, cwd=str(SOURCE), stdout=log, stderr=subprocess.STDOUT)
            processes.append(process)
            wait_local(port, process)
        log = (output / 'collector.log').open('w', encoding='utf-8')
        logs.append(log)
        collector = subprocess.Popen(commands[3], cwd=str(SOURCE), stdout=log, stderr=subprocess.STDOUT)
        processes.append(collector)
        while collector.poll() is None:
            if any(process.poll() is not None for process in processes[:-1]):
                raise RuntimeError('Mining component exited during collection')
            time.sleep(0.5)
        if collector.returncode != 0:
            raise RuntimeError('Collector failed; see collector.log and collection-failure.json')
        metadata['status'] = 'collected; pool validity must be assessed from share logs'
    except BaseException as error:
        metadata['status'] = 'failed'
        metadata['failure'] = {'type':type(error).__name__, 'message':str(error)}
        if not (output / 'collection-failure.json').exists():
            save(output / 'collection-failure.json', metadata['failure'])
        raise
    finally:
        # Only children created by this runner are stopped; no global process-name kill.
        for process in reversed(processes):
            if process.poll() is None:
                process.terminate()
        for process in reversed(processes):
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        for log in logs:
            log.close()
        metadata['finished_utc'] = datetime.now(timezone.utc).isoformat()
        save(output / 'run-metadata.json', metadata)
    subprocess.run([sys.executable, '-P', str(SOURCE / 'analyze_reference.py'), '--run', str(output)], check=True)


if __name__ == '__main__':
    main()
