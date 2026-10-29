"""Record the saved operator API evidence; do not infer worldwide availability."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sources = ROOT / 'results/runtime-mining/pool-sources'
stats_path = sources / 'moneroocean-stats.json'
stats = json.loads(stats_path.read_text(encoding='utf-8-sig'))
coins = stats['pool_statistics']['coins']
targets = ['cn/0', 'cn/1', 'cn/2', 'cn/half', 'cn-lite/0', 'cn-lite/1',
           'cn-lite/2', 'cn-pico/trtl', 'cn/r', 'cn/rwz']
audit = {
    'operator': 'MoneroOcean', 'retrieved_date': '2026-10-07',
    'source_url': 'https://api.moneroocean.stream/pool/stats',
    'endpoint_discovery_source': 'https://moneroocean.stream/script.js?v=660da4b',
    'scope': 'Saved public operator API; no miner login or share submission',
    'target_algorithm_evidence': [],
    'source_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in sources.iterdir() if p.is_file()},
    'compatible_pool_confirmed': False,
    'limitation': 'Absence/inactive in this operator API does not establish that no other compatible pool exists.'
}
for algo in targets:
    entries = [dict(value) for value in coins.values() if value.get('algo') == algo]
    audit['target_algorithm_evidence'].append({
        'algorithm': algo, 'entries': entries,
        'operator_api_status': 'active' if any(x.get('active') for x in entries)
            else 'inactive' if entries else 'not_listed'
    })
destination = ROOT / 'results/runtime-mining/pool-compatibility-audit.json'
destination.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'output':str(destination), 'compatible_pool_confirmed':False,
                  'algorithms_checked':len(targets)}))
