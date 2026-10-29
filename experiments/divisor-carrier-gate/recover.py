"""Recover coprime atoms using public chosen-input observations; no factoring."""
import hashlib,json,math,sys
from pathlib import Path
source,destination=map(Path,sys.argv[1:3])
if destination.exists():raise SystemExit('Refuse overwrite')
blob=source.read_bytes();p=json.loads(blob);width=p['width'];universe=int(p['universe'])
blocks={0:universe};gcds=0
assert len(p['observations'])==(width-1).bit_length()
for j,item in enumerate(p['observations']):
    expected=sum(1<<i for i in range(width) if (i>>j)&1)
    assert item['input']==expected
    observation=int(item['value']);next_blocks={}
    for label,block in blocks.items():
        yes=math.gcd(block,observation);gcds+=1;no=block//yes
        if no>1:next_blocks[label]=no
        if yes>1:next_blocks[label|(1<<j)]=yes
    blocks=next_blocks
assert set(blocks)==set(range(width))
atoms=[blocks[i] for i in range(width)]
assert math.prod(atoms)==universe
assert all(math.gcd(a,b)==1 for i,a in enumerate(atoms) for b in atoms[i+1:])
destination.write_text(json.dumps({'atoms':list(map(str,atoms)),'queries':len(p['observations']),'splitting_gcds':gcds,'source_sha256':hashlib.sha256(blob).hexdigest(),'factoring_calls':0},indent=2))
