"""Extract fixed hash_cn arguments from pinned C sources; never execute Wasm."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMMIT = '009e9e7bd812cbecacb506507e36834ae3ecddc4'
EXPECTED = {
    'cn-0':('cn/0',0,0), 'cn-1':('cn/1',0,1), 'cn-2':('cn/2',0,2),
    'cn-lite-0':('cn-lite/0',1,0), 'cn-lite-1':('cn-lite/1',1,1),
    'cn-lite-2':('cn-lite/2',1,2), 'cn-pico-trtl':('cn-pico/trtl',2,2),
    'cn-half':('cn/half',3,2), 'cn-r':('cn/r',0,4), 'cn-rwz':('cn/rwz',4,2)
}


def main():
    contracts = {}
    for program, (algorithm, lite, variant) in EXPECTED.items():
        relative = f'dataset/miners/{program}/main.c'
        source = ROOT / 'data/upstream/source' / relative
        raw = source.read_bytes()
        text = raw.decode('utf-8')
        match = re.search(r'char\s*\*hash_cn\([^)]*\)', text)
        if not match:
            raise ValueError('Missing hash_cn: ' + program)
        end = text.index('strlen(', match.end())
        prologue = text[match.end():end]
        assignments = {}
        locations = {}
        for argument in ['lite', 'variant']:
            assignment = re.search(rf'\b{argument}\s*=\s*(\d+)\s*;', prologue)
            if not assignment:
                raise ValueError('Missing fixed argument: ' + program + '/' + argument)
            assignments[argument] = int(assignment.group(1))
            locations[argument] = text.count('\n',0,match.end()+assignment.start()) + 1
        if assignments != {'lite':lite, 'variant':variant}:
            raise ValueError('Declared algorithm differs from source: ' + program)
        contracts[program] = dict(program=program, algorithm=algorithm, lite=lite, variant=variant,
            source_commit=COMMIT, source_path=relative,
            source_url=f'https://raw.githubusercontent.com/HakonHarnes/wasm-obf/{COMMIT}/{relative}',
            source_sha256=hashlib.sha256(raw).hexdigest(), assignment_lines=locations,
            signature='char *hash_cn(char *hex, int lite, int variant, int height)',
            height_required=program == 'cn-r', mining_semantics_confirmed=False,
            evidence='Source fixes lite/variant inside hash_cn; binary execution is still required')
    destination = ROOT / 'results/runtime-mining/algorithm-contracts.json'
    destination.write_text(json.dumps(contracts,indent=2),encoding='utf-8')
    inventory = json.loads((ROOT / 'results/runtime-mining/input-abi-inventory.json').read_text())
    adapter_imports = {'__assert_fail', 'emscripten_memcpy_big', 'emscripten_date_now',
                       '_emscripten_get_now_is_monotonic', 'emscripten_get_now',
                       '_gmtime_js', '_tzset_js', 'emscripten_resize_heap'}
    compatibility = []
    for item in inventory:
        missing = [entry for entry in item['imports'] if entry['module'] != 'env'
                   or entry['kind'] != 0 or entry['name'] not in adapter_imports]
        exports = {(entry['name'],entry['kind']) for entry in item['exports']}
        required = {('memory',2),('hash_cn',0),('malloc',0)}
        compatibility.append({'sha256':item['sha256'], 'program':item['program'],
            'release':item['release'], 'method':item['method'], 'unprovided_imports':missing,
            'missing_required_exports':sorted(required - exports),
            'static_names_match':not missing and required <= exports,
            'function_signatures_verified':False, 'execution_compatibility_confirmed':False,
            'conditional_unimplemented_functions':[entry['name'] for entry in item['imports']
                                                  if entry['name'] in {'_gmtime_js','_tzset_js'}]})
    (ROOT / 'results/runtime-mining/adapter-abi-audit.json').write_text(
        json.dumps({'scope':'Cached static interface names and kinds; not runtime compatibility',
                    'records':compatibility},indent=2),encoding='utf-8')
    print(json.dumps({program:{'algorithm':item['algorithm'],'lite':item['lite'],
                              'variant':item['variant']} for program,item in contracts.items()}))


if __name__ == '__main__':
    main()
