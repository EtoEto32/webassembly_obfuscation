"""Reconstruct the reference instruction text from tagged transformations and check integer identities."""
import json
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/runtime-mining/cross-dataset/swamped'
spec=json.loads((OUT/'controlled-pair-manifest.json').read_text())
reference=(OUT/'046dc081.wat').read_text()
records=[]
for case in spec['cases'][1:]:
    text=(OUT/(case['name']+'.wat')).read_text()
    recovered=text
    sites=[]
    if case['source_function']=='nop_insertion':
        # Every newly inserted nop is a separate line. Reference has none.
        assert not re.search(r'^\s*nop\s*$',reference,re.M)
        recovered=re.sub(r'^ *nop\n','',text,flags=re.M)
        sites=[dict(function=f['function'],site_count=len(f['changes'])) for f in case['changes']]
    else:
        replacements=[]
        for f in case['changes']:
            tags=f['changes'];assert len(tags)%3==0
            identities=[]
            for i in range(0,len(tags),3):
                a,b,add=[v['instruction'] for v in tags[i:i+3]]
                ma=re.fullmatch(r'( *)(i32|i64)\.const (-?\d+)',a)
                mb=re.fullmatch(r'( *)(i32|i64)\.const (-?\d+)',b)
                assert ma and mb and ma[2]==mb[2] and add.strip()==ma[2]+'.add'
                value=int(ma[3])+int(mb[3]);bits=int(ma[2][1:]);value%=1<<bits
                if value>=1<<(bits-1):value-=1<<bits
                replacements.append((a+'\n'+b+'\n'+add+'\n',ma[1]+ma[2]+'.const '+str(value)+'\n'))
                identities.append(dict(type=ma[2],a=int(ma[3]),b=int(mb[3]),recovered_constant=value))
            sites.append(dict(function=f['function'],site_count=len(identities),identities=identities))
        # Replace only the published tagged sequences, preserving all other text.
        for before,after in replacements:
            assert before in recovered
            recovered=recovered.replace(before,after,1)
    assert recovered==reference,'Changes other than the reviewed transformation remain'
    records.append(dict(name=case['name'],sha256=case['sha256'],reference_recovered_exactly=True,
                        sites=sites,scope='Complete syntactic transformation audit, not a proof of engine behavior or all-input runtime correctness'))
(OUT/'controlled-pair-mechanism-audit.json').write_text(json.dumps(records,indent=2)+'\n')
print(json.dumps([dict(name=r['name'],sites=sum(f['site_count'] for f in r['sites']),
                      exact_reference_recovery=r['reference_recovered_exactly']) for r in records]))
