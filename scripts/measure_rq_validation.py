"""Reproducible mechanical observations; not automatic mechanism verdicts."""
import argparse
import collections
import hashlib
import json
import re
from analyze_corpus import ROOT, OP, FUNC

OUT = ROOT/'results/rq-validation'


def functions(sha):
    path=ROOT/'results/cases'/sha/'disassembly.txt'
    result={}; fn=None
    for line_no,line in enumerate(path.read_text(encoding='utf-8').splitlines(),1):
        m=FUNC.match(line.strip())
        if m:
            fn=int(m[2]); result[fn]={'header':line.strip(),'ops':[]}
        m=OP.match(line)
        if m and fn is not None:
            result[fn]['ops'].append(dict(offset=m[1],op=m[2],args=m[3].strip(),line=line_no))
    return result


def normalized(f):
    return [(x['op'],re.sub(r'\s*<[^>]*>','',x['args'])) for x in f['ops']]


def increments(f):
    hits=[]
    for i in range(len(f['ops'])-3):
        a,b,c,d=f['ops'][i:i+4]
        if (a['op']=='global.get' and b['op'] in ('i32.const','i64.const')
            and b['args']=='1' and c['op']==b['op'][:3]+'.add'
            and d['op']=='global.set' and a['args']==d['args']):
            hits.append(dict(global_index=a['args'],type=b['op'][:3],offset=a['offset'],line=a['line']))
    return hits


def compare(a,b):
    return {'origin_functions':len(a),'variant_functions':len(b),
            'same_index_decoded_matches':sum(normalized(f)==normalized(b[i]) for i,f in a.items() if i in b),
            'changed_indices':[i for i,f in a.items() if i not in b or normalized(f)!=normalized(b[i])]}


def strip_increments(f):
    offsets={h['offset'] for h in increments(f)}
    ops=[]; j=0
    while j<len(f['ops']):
        if f['ops'][j]['offset'] in offsets: j+=4
        else: ops.append(f['ops'][j]); j+=1
    return {'ops':ops}


def smoke():
    p=json.loads((ROOT/'experiments/review-selection-stage2.json').read_text())['selected']
    measured=[]
    for i,j,count in [(0,1,53),(3,4,55)]:
        a,b=functions(p[i]['sha256']),functions(p[j]['sha256'])
        result=compare(a,b)
        assert result['same_index_decoded_matches']==count, result
        measured.append(result)
    sha='aafff58765c917b0900726ecca11c715c38c3c25b1be9e0af130e0f5b170c14e'
    hits=sum(len(increments(f)) for f in functions(sha).values())
    assert hits==4051,hits
    # A changed target and a non-unit addition must not match.
    for args in [('2','1','3'),('2','2','2')]:
        f={'ops':[dict(op=op,args=arg,offset='0',line=1) for op,arg in
                  zip(('global.get','i64.const','i64.add','global.set'),(args[0],args[1],'',args[2]))]}
        assert not increments(f)
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'measurement-smoke.json').write_text(json.dumps(dict(name_pairs=measured,counter_hits=hits,
        negative_controls='different global and non-unit addition rejected',status='passed'),indent=2))
    print('Pilot comparisons and negative controls passed')


def measure():
    plan=json.loads((ROOT/'experiments/rq-validation-selection.json').read_text(encoding='utf-8'))
    output=[]
    for r in plan['selected']:
        fs=functions(r['sha256'])
        obs=[]
        for i,f in fs.items():
            sites=[x for x in f['ops'] if x['op'] in ('br_table','call_indirect')]
            inc=increments(f)
            obs.append(dict(index=i,header=f['header'],decoded_rows=len(f['ops']),
                            sites=sites,increments=inc,
                            opcode_counts=dict(collections.Counter(x['op'] for x in f['ops']))))
        output.append(dict(sha256=r['sha256'],stratum=r['stratum'],program=r['program_unit'],functions=obs))
    pairs=[]; instrumentation=[]
    units=collections.defaultdict(list)
    for r in plan['selected']:
        if r['program_unit']!='unknown_ancestry': units[r['program_unit']].append(r)
    for unit,rs in units.items():
        original=next(r for r in rs if r['stratum'].split('/')[-1] in ('origin','original','unobfuscated'))
        for r in rs:
            if r is original: continue
            pairs.append(dict(program=unit,origin=original['sha256'],variant=r['sha256'],
                stratum=r['stratum'],**compare(functions(original['sha256']),functions(r['sha256']))))
            if r['stratum']=='seismic_nonmining/profiled':
                a,b=functions(original['sha256']),functions(r['sha256'])
                matches=[i for i,f in a.items() if i in b and normalized(f)==normalized(strip_increments(b[i]))]
                instrumentation.append(dict(program=unit,origin=original['sha256'],profiled=r['sha256'],
                    matched_after_removing_increments=len(matches),origin_functions=len(a),
                    unmatched=[i for i in a if i not in matches],
                    added_functions=[dict(index=i,**f) for i,f in b.items() if i not in a]))
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'mechanical-observations.json').write_text(json.dumps(output,indent=2),encoding='utf-8')
    (OUT/'paired-comparisons.json').write_text(json.dumps(pairs,indent=2),encoding='utf-8')
    (OUT/'instrumentation-removal-check.json').write_text(json.dumps(instrumentation,indent=2),encoding='utf-8')
    print(json.dumps({'modules':len(output),'pairs':len(pairs),'status':'observations_only_not_verdicts'}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['smoke','measure']);a=p.parse_args()
    smoke() if a.action=='smoke' else measure()
