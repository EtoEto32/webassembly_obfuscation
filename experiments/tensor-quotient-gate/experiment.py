"""Bounded repair and attack gate. Uses existing public instances, not private bases."""
import copy, difflib, hashlib, itertools, json, platform, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent / 'tensor-support-gate'
OUT = ROOT / 'artifacts'
MASK = (1 << 32) - 1

def write(name, v):
    (OUT / name).write_text(json.dumps(v, indent=2))

def rol(x, n, width=32):
    n %= width
    return ((x << n) | (x >> (width-n))) & ((1 << width)-1)

def reference(x, y, w):
    mask = (1 << w)-1
    return ((rol((x+y)&mask, 7, w) ^ (x&y)) + (x ^ rol(y, 13, w))) & mask

def tensor(t, a, b):
    products = [a[0]*b[0], a[0]*b[1], a[1]*b[0], a[1]*b[1]]
    return tuple(sum(k*v for k,v in zip(row, products)) & MASK for row in t)

def input_factor(x, y, nonce, i):
    return (2*(x ^ rol(y, i) ^ nonce ^ i)+1) & MASK

def gate_factor(a, b):
    return (2*(a[0] ^ b[1])+1) & MASK

def execute(p, recovered, x, y, w, nonce, scaled):
    vals = {}
    for i, n in enumerate(p['inputs']):
        bit = ((x if i<w else y) >> (i%w)) & 1
        s = input_factor(x,y,nonce,i) if scaled else 1
        vals[n['id']] = tuple(s*v & MASK for v in n['columns'][bit])
    vals.update({n['id']: tuple(n['value']) for n in p['constants']})
    lookup = {n['id']: n for n in p['nodes']}
    for item in recovered['nodes']:
        n = lookup[item['id']]
        a,b = [vals[k] for k in n['parents']]
        v = tensor(n['tensor'],a,b)
        s = gate_factor(a,b) if scaled else 1
        vals[n['id']] = tuple(s*k & MASK for k in v)
    raw = [sum(k*v for k,v in zip(n['decoder'],vals[n['id']])) & MASK for n in p['outputs']]
    if not scaled:
        assert set(raw) <= {0,1}
    answer = sum((v & 1) << i for i,v in enumerate(raw))
    return answer, vals

def compact(r,x,y,w):
    vals = {n: ((x if i<w else y) >> (i%w)) & 1 for i,n in enumerate(r['inputs'])}
    vals.update(r['constants'])
    for n in r['nodes']:
        a,b = n['parents']
        vals[n['id']] = n['table'][vals[a]][vals[b]]
    return sum(n['table'][vals[n['id']]] << i for i,n in enumerate(r['outputs']))

def certificate(p, r):
    """Check every projected local row using an independent explicit contraction."""
    rows = 0
    known = set()
    assert r['inputs'] == [n['id'] for n in p['inputs']]
    assert set(r['constants']) == {n['id'] for n in p['constants']}
    assert set(r['support']) == {n['id'] for field in ['inputs','constants','nodes'] for n in p[field]}
    for support in r['support'].values():
        assert 1 <= len(support) <= 2
        assert len(set(map(tuple,support))) == len(support)
        assert all(len(v)==2 and set(v)<={0,1} for v in support)
    for n in p['inputs']:
        assert r['support'][n['id']] == [[v&1 for v in col] for col in n['columns']]
        known.add(n['id'])
    for n in p['constants']:
        assert r['support'][n['id']] == [[v&1 for v in n['value']]]
        assert r['constants'][n['id']] == 0
        known.add(n['id'])
    lookup = {n['id']:n for n in p['nodes']}
    assert len(lookup) == len(r['nodes'])
    for n in r['nodes']:
        assert n['id'] not in known
        source = lookup[n['id']]
        assert n['parents'] == source['parents']
        a,b = n['parents']
        assert a in known and b in known
        assert len(n['table']) == len(r['support'][a])
        assert all(len(row)==len(r['support'][b]) for row in n['table'])
        assert all(0<=k<len(r['support'][n['id']]) for row in n['table'] for k in row)
        for i,u in enumerate(r['support'][a]):
            for j,v in enumerate(r['support'][b]):
                actual = [k&1 for k in tensor(source['tensor'],u,v)]
                assert actual == r['support'][n['id']][n['table'][i][j]]
                rows += 1
        known.add(n['id'])
    assert len(p['outputs']) == len(r['outputs'])
    for source,n in zip(p['outputs'],r['outputs']):
        assert n['id'] == source['id']
        assert n['table'] == [sum(k*v for k,v in zip(source['decoder'],s))&1 for s in r['support'][n['id']]]
    return rows

def run_attack(stem,p):
    write(stem+'.public.json',p)
    subprocess.run([sys.executable,str(ROOT/'attack.py'),str(OUT/(stem+'.public.json')),str(OUT/(stem+'.quotient.json')),str(OUT/(stem+'.recovered.json'))],check=True,timeout=35)
    r=json.loads((OUT/(stem+'.recovered.json')).read_text())
    assert r['status'] == 'reconstructed'
    return r

def main():
    if OUT.exists():
        raise SystemExit('Refuse overwrite artifacts')
    OUT.mkdir()
    protocol=json.loads((ROOT/'protocol.json').read_text())
    rows=[];provenance={}
    sources=sorted((BASE/'artifacts').glob('w*.public.json'))
    assert len(sources)==protocol['limits']['source_dags']
    for source in sources:
        stem=source.name.removesuffix('.public.json');w=int(stem.split('-')[0][1:])
        p=json.loads(source.read_text());scaled=copy.deepcopy(p);scaled['scaling']='odd-input-and-gate-v1'
        r=run_attack(stem,scaled)
        checks_source=source.with_name(stem+'.checks.json')
        checks=json.loads(checks_source.read_text())
        for f in [source, checks_source]:
            provenance[str(f.relative_to(BASE))]=hashlib.sha256(f.read_bytes()).hexdigest()
        outcomes=[];observed={n['id']:set() for n in p['nodes']}
        changed_vectors=0
        for x,y,*old in checks:
            expected=reference(x,y,w)
            assert old[0] == expected
            ordinary,unscaled=execute(p,r,x,y,w,0,False)
            reconstructed=compact(r,x,y,w)
            assert ordinary == expected == reconstructed
            for nonce in protocol['nonces']:
                actual,vals=execute(scaled,r,x,y,w,nonce,True)
                assert actual==expected
                for node in observed:
                    observed[node].add(vals[node])
                    changed_vectors += vals[node] != unscaled[node]
                    # This checks the exposed full trace quotient, not only outputs.
                    assert tuple(k&1 for k in vals[node]) == tuple(k&1 for k in unscaled[node])
                outcomes.append([x,y,nonce,expected,actual,reconstructed])
        write(stem+'.checks.json',outcomes)
        rows.append({'name':stem,'original_cases':len(checks),'scaled_cases':len(outcomes),'errors':0,'gates':len(p['nodes']),'local_certificate_rows':certificate(scaled,r),'gates_with_more_than_two_observed_vectors':sum(len(v)>2 for v in observed.values()),'maximum_observed_vectors':max(map(len,observed.values())),'changed_gate_vectors':changed_vectors,'recovered_nodes':len(r['nodes'])})
    # Positive control, same attacker, no special one-hot handling.
    plain=json.loads((BASE/'artifacts/plain.public.json').read_text())
    pr=run_attack('plain',plain)
    for x,y in itertools.product(range(8),repeat=2):
        assert compact(pr,x,y,3)==reference(x,y,3)
    positive={'cases':64,'certificate_rows':certificate(plain,pr)}
    # Unit condition is necessary: an even scale annihilates an encoded true bit's parity.
    even_control={'encoded_true':[0,1],'factor':2,'scaled_true':[0,2],'decoded_parity':0,'expected':1}
    assert even_control['decoded_parity'] != even_control['expected']
    write('even-scale-counterexample.json',even_control)
    # Detect input information lost under the proposed projection.
    invalid=copy.deepcopy(plain);invalid['inputs'][0]['columns']=[[1,0],[1,2]]
    write('collapsed.public.json',invalid)
    child=subprocess.run([sys.executable,str(ROOT/'attack.py'),str(OUT/'collapsed.public.json'),str(OUT/'collapsed.quotient.json'),str(OUT/'collapsed.recovered.json')],capture_output=True,text=True,timeout=35)
    assert child.returncode != 0 and 'Input columns collapse' in child.stderr
    write('collapsed-control.json',{'returncode':child.returncode,'stderr':child.stderr,'classification':'unsupported quotient, not security'})
    # Retain actual before/after/projection sample from generated artifacts.
    p=json.loads(sources[-1].read_text());stem=sources[-1].name.removesuffix('.public.json')
    r=json.loads((OUT/(stem+'.recovered.json')).read_text());node=r['nodes'][0]['id']
    sample={'source':stem,'node':node,'before':next(n for n in p['nodes'] if n['id']==node),'after_scaling_rule':'U(a,b) * ((2*(a[0] XOR b[1])+1) mod 2^32)','quotient':next(n for n in json.loads((OUT/(stem+'.quotient.json')).read_text())['nodes'] if n['id']==node),'recovered':r['nodes'][0]}
    write('sample.json',sample)
    (OUT/'sample.diff').write_text(''.join(difflib.unified_diff(json.dumps(sample['before'],indent=2).splitlines(True),json.dumps(sample['quotient'],indent=2).splitlines(True),fromfile='public-tensor',tofile='modulo-2-tensor')))
    result={'python':platform.python_version(),'rows':rows,'positive':positive,'even_scale':even_control,'source_hashes':provenance,'decision':'reject odd-scaling repair; concrete support growth does not remove the small exact quotient'}
    write('results.json',result)
    print(json.dumps({'original_cases':sum(r['original_cases'] for r in rows),'scaled_cases':sum(r['scaled_cases'] for r in rows),'certificate_rows':sum(r['local_certificate_rows'] for r in rows)+positive['certificate_rows'],'errors':0,'all_recovered':True}))

if __name__ == '__main__':main()
