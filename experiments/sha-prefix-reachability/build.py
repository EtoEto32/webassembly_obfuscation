import difflib
import hashlib
import importlib.util
import json
import platform
import random
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else HERE / 'artifacts'
BASE = REPO / 'experiments/sha256-research-baseline'
HISTORY = REPO / 'experiments/sha-history-gate/check.py'
MASK = 2**32 - 1


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    plan = json.loads((HERE / 'protocol.json').read_text())
    spec = importlib.util.spec_from_file_location('history', HISTORY)
    history = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(history)
    vendor = (BASE / 'vendor/sha256.js').read_text()
    constants = [int(x, 16) for x in re.findall(r'0x[0-9A-Fa-f]+', vendor.split('var K = [')[1].split(']')[0])]
    iv = [int(re.search(r'this\._' + c + r' = (0x[0-9a-f]+)', vendor)[1], 16) for c in 'abcdefgh']
    assert len(constants) == 64
    rng = random.Random(plan['seed'])
    targets = [[0]*8, [MASK]*8]
    for lane in range(8):
        for value in [1, 0x80000000, MASK]:
            state = [0]*8
            state[lane] = value
            targets.append(state)
    targets += [[rng.getrandbits(32) for _ in range(8)] for _ in range(256)]
    rows = []
    for target in targets:
        state = iv[:]
        words = []
        trace = []
        for i, desired_a in enumerate(reversed(history.encode(target))):
            a,b,c,d,e,f,g,h = state
            sigma = history.rotr(e,6)^history.rotr(e,11)^history.rotr(e,25)
            choice = g^(e&(f^g))
            u = (desired_a-history.q(a,b,c)-h-sigma-choice)&MASK
            words.append((u-constants[i])&MASK)
            state = history.reference(state,u)
            trace.append(state)
        assert state == target
        message = b''.join(w.to_bytes(4,'big') for w in words)
        rows.append({'target':target, 'message':message.hex(), 'digest':hashlib.sha256(message).hexdigest(), 'trace':trace})
    (OUT / 'cases.json').write_text(json.dumps(rows,indent=2)+'\n')
    source = (BASE / 'artifacts/plain.wat').read_text()
    marker = '(local.set $j (i32.add (local.get $j) (i32.const 1)))'
    assert source.count(marker) == 1
    capture = '\n (if (i32.eq (local.get $j) (i32.const 8)) (then\n' + '\n'.join(
        f' (i32.store (i32.const {640+4*i}) (local.get ${c}))' for i,c in enumerate('abcdefgh')) + '))\n'
    instrumented = source.replace(marker,marker+capture)
    (OUT / 'before.wat').write_text(source)
    (OUT / 'capture.wat').write_text(instrumented)
    (OUT / 'capture.diff').write_text(''.join(difflib.unified_diff(source.splitlines(True),instrumented.splitlines(True),fromfile='before.wat',tofile='capture.wat')))
    wabt = REPO / '.tools/wabt-1.0.42/bin'
    opt = REPO / '.tools/binaryen-version_133/bin/wasm-opt.exe'
    commands = [
        [wabt/'wat2wasm.exe',OUT/'before.wat','-o',OUT/'before.wasm'],
        [wabt/'wat2wasm.exe',OUT/'capture.wat','-o',OUT/'capture.raw.wasm'],
        [opt,OUT/'capture.raw.wasm','-O2','-o',OUT/'capture.O2.wasm'],
        [wabt/'wasm2wat.exe',OUT/'capture.O2.wasm','-o',OUT/'capture.O2.wat'],
    ]
    commands += [[wabt/'wasm-validate.exe',OUT/name] for name in ['before.wasm','capture.raw.wasm','capture.O2.wasm']]
    commands += [[wabt/'wat2wasm.exe','--version'],[opt,'--version']]
    logs=[]
    for command in commands:
        result = subprocess.run(list(map(str,command)),capture_output=True,text=True,timeout=60)
        logs.append({'command':list(map(str,command)), 'exit':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
        (OUT/'build-log.json').write_text(json.dumps(logs,indent=2)+'\n')
        result.check_returncode()
    assert (OUT/'before.wasm').read_bytes() == (BASE/'artifacts/plain.raw.wasm').read_bytes()
    paths = [HISTORY,HERE/'protocol.json',HERE/'build.py',HERE/'verify.cjs',BASE/'vendor/sha256.js',BASE/'artifacts/plain.wat']
    manifest={'python':platform.python_version(),'cases':len(rows),'inputs':{str(p.relative_to(REPO)):sha(p) for p in paths},
              'artifacts':{p.name:{'sha256':sha(p),'bytes':p.stat().st_size} for p in OUT.iterdir() if p.is_file()}}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'cases':len(rows),'out':str(OUT)}))


if __name__ == '__main__':
    main()
