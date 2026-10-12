"""Verify the finite-support simulation for every public DAG input, without private maps."""
import hashlib, itertools, json
from pathlib import Path
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'artifacts';reports=[]
def contract(t,a,b,p):
    return [(t[k][0]*a[0]*b[0]+t[k][1]*a[0]*b[1]+t[k][2]*a[1]*b[0]+t[k][3]*a[1]*b[1])%p for k in range(2)]
for original in sorted(OUT.glob('*.public.json')):
    if original.name.startswith('negative.'):continue
    target=original.with_name(original.name.replace('.public.json','.recovered.json'))
    p=json.loads(original.read_text());r=json.loads(target.read_text());q=p['modulus']
    assert r['status']=='reconstructed' and r['public_sha256']==hashlib.sha256(original.read_bytes()).hexdigest()
    assert r['inputs']==[n['id'] for n in p['inputs']]
    expected_ids=[n['id'] for category in ['inputs','constants','nodes'] for n in p[category]]
    assert len(set(expected_ids))==len(expected_ids)
    assert set(r['support'])==set(expected_ids)
    known=set(r['inputs'])
    for n in p['inputs']:assert r['support'][n['id']]==n['columns']
    assert r['constants']=={n['id']:0 for n in p['constants']}
    for n in p['constants']:assert r['support'][n['id']]==[n['value']];known.add(n['id'])
    nodes={n['id']:n for n in p['nodes']};seen=set();rows=0
    for n in r['nodes']:
        assert n['id'] not in seen and n['id'] in nodes
        source=nodes[n['id']];assert n['parents']==source['parents']
        assert all(parent in known for parent in n['parents'])
        left,right=[r['support'][parent] for parent in n['parents']];states=r['support'][n['id']]
        assert 1<=len(states)<=2 and n['states']==len(states)
        assert len(n['table'])==len(left) and all(len(row)==len(right) for row in n['table'])
        for i,j in itertools.product(range(len(left)),range(len(right))):
            k=n['table'][i][j];assert type(k) is int and 0<=k<len(states)
            assert contract(source['tensor'],left[i],right[j],q)==states[k];rows+=1
        known.add(n['id']);seen.add(n['id'])
    assert seen==set(nodes)
    assert len(p['outputs'])==len(r['outputs'])
    for a,b in zip(p['outputs'],r['outputs']):
        assert a['id']==b['id']
        expected=[(a['decoder'][0]*v[0]+a['decoder'][1]*v[1])%q for v in r['support'][a['id']]]
        assert b['table']==expected and all(x in (0,1) for x in expected)
    reports.append({'public':original.name,'public_sha256':hashlib.sha256(original.read_bytes()).hexdigest(),'recovered_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'nodes':len(nodes),'local_rows':rows,'input_bits':len(p['inputs']),'all_boundary_and_local_checks_pass':True})
destination=OUT/'certificates.json'
if destination.exists():raise SystemExit('Refuse overwrite certificate results')
destination.write_text(json.dumps({'verifier_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'reports':reports},indent=2))
print(json.dumps({'certificates':len(reports),'rows':sum(r['local_rows'] for r in reports)}))
