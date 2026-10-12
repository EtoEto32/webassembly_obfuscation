"""Prepare source-backed local hash checks without executing artifact scripts."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/runtime-mining/cross-dataset/proof-of-theft'


def main():
    roles = json.loads((OUT / 'runtime-roles.json').read_text())
    run = ROOT / 'results/runtime-mining/runs/cn-pico-normal-binaries-20261007-222952'
    jobs = {}
    for line in (run / 'bridge-events.jsonl').read_text().splitlines():
        event = json.loads(line)
        if event['event'] == 'job':
            job = event['data']['job']
            jobs[job['job_id']] = job
    shares = [json.loads(line) for line in (run / 'shares.jsonl').read_text().splitlines()]
    accepted = {x['rpc_id'] for x in shares if x['event'] == 'accepted'}
    vectors = []
    for x in shares:
        if x['event'] != 'submitted' or x['rpc_id'] not in accepted:
            continue
        job = jobs[x['job_id']]
        blob = bytearray.fromhex(job['blob'])
        blob[39:43] = bytes.fromhex(x['nonce'])
        vectors.append(dict(hex=blob.hex(), expected=x['result'], lite=2, variant=2,
                            height=job['height'], job_id=x['job_id'], rpc_id=x['rpc_id']))
    modules = []
    for x in roles['modules']:
        if 'webminerpoolhashcn' not in x['path'] or x['wasabi_imports'] or not x['path'].endswith('/cn.og.wasm'):
            continue
        # Virtualization has a larger WASI ABI and needs a separate reviewed adapter.
        if '_virtualize/' in x['path']:
            continue
        source = next(s for s in roles['source_receipts'] if s['path'] == x['path'].rsplit('/', 1)[0] + '/cn.js')
        glue = (ROOT / source['saved']).read_text()
        minified = any(e['name'] == 'g' and e['kind'] == 2 for e in x['exports'])
        if minified:
            for required in ['"d":__emscripten_get_now_is_monotonic', '"c":__gmtime_js',
                             '"b":__tzset_js', '"e":_emscripten_date_now',
                             '"f":_emscripten_memcpy_big', '"a":_emscripten_resize_heap',
                             'Module["asm"]["k"]', 'Module["asm"]["g"]']:
                if required not in glue:
                    raise ValueError('Unverified minified ABI: ' + x['path'])
        obj = ROOT / x['object']
        if hashlib.sha256(obj.read_bytes()).hexdigest() != x['sha256']:
            raise ValueError('Object digest mismatch')
        modules.append(dict(path=x['path'], sha256=x['sha256'], object=x['object'],
                            bytes=x['bytes'], abi='minified-pointer-time' if minified else 'named-split-i64-time',
                            glue_sha256=source['sha256'], glue_source=source['path'],
                            method=x['path'].split('/')[-2]))
    report = dict(modules=modules, vectors=vectors, algorithm='cn-pico/trtl',
                  reference='Previously recorded actual pool-accepted shares, not a newly connected pool',
                  reference_run=str(run.relative_to(ROOT)),
                  limitations=['Finite observed inputs; not proof of correctness on all inputs.',
                               'No claim that all modules were compiled with identical toolchain/optimization.',
                               'Virtualization requires additional host ABI review and is not excluded from study scope.'])
    (OUT / 'hash-experiment-input.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'modules': len(modules), 'accepted_share_vectors': len(vectors)}))


if __name__ == '__main__':
    main()
