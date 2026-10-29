import hashlib
import importlib.util
import json
from pathlib import Path
import platform

HERE = Path(__file__).resolve().parent
HELPER = HERE.parent / 'sha-joint-history-gate/check.py'
spec = importlib.util.spec_from_file_location('joint', HELPER)
j = importlib.util.module_from_spec(spec)
spec.loader.exec_module(j)
M = (1 << 32) - 1


def block_for_window(phase, target):
    # Bijective schedule shifts: invert one recurrence at a time.
    words = [None] * phase
    words[phase-16:phase] = [(v-j.K[k]) & M for k,v in enumerate(target, phase-16)]
    for k in reversed(range(16, phase)):
        words[k-16] = (words[k]-j.small1(words[k-2])-words[k-7]-j.small0(words[k-15])) & M
    return b''.join(w.to_bytes(4, 'big') for w in words[:16])


def vnext(v, phase):
    return (j.small1((v[14]-j.K[phase-2]) & M)
            + v[9]-j.K[phase-7]
            + j.small0((v[1]-j.K[phase-15]) & M)
            + v[0]-j.K[phase-16]+j.K[phase]) & M


def digest(message):
    chain = j.IV[:]
    data = j.padded(message)
    for offset in range(0, len(data), 64):
        states, _ = j.normal(data[offset:offset+64], chain)
        chain = [(a+b) & M for a,b in zip(chain,states[-1])]
    return b''.join(w.to_bytes(4,'big') for w in chain).hex()


def main():
    p = json.loads((HERE/'protocol.json').read_text())
    out = HERE/'artifacts'
    out.mkdir(exist_ok=False)
    rows = []
    checks = 0
    for phase in p['phases']:
        message = block_for_window(phase, [0]*16)
        _, w = j.normal(message, j.IV)
        v = [(a+b) & M for a,b in zip(w,j.K)]
        assert v[phase-16:phase] == [0]*16
        for k in range(16,64):
            assert vnext(v[k-16:k],k) == v[k]
            checks += 1
        expected = hashlib.sha256(message).hexdigest()
        assert digest(message) == expected
        rows.append({'phase':phase,'message_hex':message.hex(),'digest':expected,
                     'W':w,'V':v,'window':v[phase-16:phase],'successor':v[phase]})
    assert rows[0]['window'] == rows[1]['window']
    assert rows[0]['successor'] != rows[1]['successor']
    (out/'cases.json').write_text(json.dumps(rows,indent=2)+'\n')
    sources = [HERE/'check.py',HERE/'protocol.json',HELPER,j.HELPER,j.BASE/'vendor/sha256.js']
    result = {'python':platform.python_version(),'messages':2,'full_python_hash_checks':2,
              'recurrence_checks':checks,'successors':[r['successor'] for r in rows],
              'rejected':True,'sources':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in sources}}
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__': main()
