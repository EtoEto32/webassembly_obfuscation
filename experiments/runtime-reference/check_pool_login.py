"""One ordinary login to the selected published endpoint; no hashes or shares."""
import argparse
import json
import socket
from datetime import datetime, timezone
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--config', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
config = json.loads(args.config.read_text(encoding='utf-8-sig'))
if (config['host'], config['port'], config['algorithm']) != ('fastpool.xyz', 10092, 'cn-pico/trtl'):
    raise ValueError('This check is only for the selected official-generator endpoint')
if not config.get('address') or config.get('user_owned_identifier') is not True:
    raise ValueError('A user-supplied public identifier is required')
if args.output.exists():
    raise FileExistsError('Preserve the existing login receipt')
receipt = {'utc':datetime.now(timezone.utc).isoformat(), 'endpoint':'fastpool.xyz:10092',
           'algorithm_requested':config['algorithm'], 'hashes_computed':0, 'shares_submitted':0}
try:
    with socket.create_connection((config['host'], config['port']), timeout=10) as connection:
        connection.settimeout(10)
        message = {'id':1, 'jsonrpc':'2.0', 'method':'login', 'params':{
            'login':config['address'], 'pass':config['pass'],
            'agent':'Wasm-RQ3-research/1.0', 'algo':[config['algorithm']]}}
        connection.sendall((json.dumps(message) + '\n').encode())
        data = b''
        while b'\n' not in data:
            chunk = connection.recv(4096)
            if not chunk:
                raise ConnectionError('Pool closed the connection before a complete response')
            data += chunk
            if len(data) > 65536:
                raise ValueError('Response exceeded the bound')
        response = json.loads(data.split(b'\n', 1)[0])
        receipt['response'] = response
        receipt['status'] = 'response-received'
except (OSError, ValueError) as error:
    receipt['status'] = 'failed'
    receipt['error'] = {'type':type(error).__name__, 'message':str(error)}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(receipt, indent=2), encoding='utf-8')
response = receipt.get('response', {})
job = (response.get('result') or {}).get('job') or {}
print(json.dumps({'status':receipt['status'], 'error':receipt.get('error'),
                  'pool_error':response.get('error'), 'pool_status':(response.get('result') or {}).get('status'),
                  'job_received':bool(job), 'algorithm_reported':job.get('algo'),
                  'variant':job.get('variant'), 'height':job.get('height'),
                  'hashes_computed':0, 'shares_submitted':0}))
