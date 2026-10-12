"""Audit Cryptic Bytes release lineage from pinned source paths and manifests.

Program groups are author build inputs, not independent malware families.
Declared transformation names are not verified obfuscation labels.
"""
import collections
import csv
import hashlib
import json
from acquire import ROOT

OUT = ROOT/'results/provenance'
MANIFESTS = ['wasm-obf-release-binaries','wasm-obf-release-binaries-opt']


def parse_release_path(path, categories):
    p = path.split('/')
    if len(p) not in (4,5) or p[0] not in ('binaries','binaries-opt'):
        raise ValueError('unexpected release path: '+path)
    variant, program, method = p[:3]
    if program not in categories or p[-1] != program+'.wasm':
        raise ValueError('unknown source program or mismatched filename: '+path)
    if (method == 'unobfuscated') != (len(p) == 4):
        raise ValueError('unexpected transformation path: '+path)
    transform = method if len(p)==4 else method+'/'+p[3]
    return {'release_variant':variant,'program':program,'program_category':categories[program],
            'declared_transformation':transform,
            'parent_id':'wasm-obf/program/'+program,
            'pair_id':'/'.join(p[1:])}


def write_csv(name, rows):
    if not rows:
        return
    with (OUT/name).open('w',newline='',encoding='utf-8') as f:
        writer = csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    tree_path = ROOT/'data/upstream/tree.json'
    tree = json.loads(tree_path.read_text())
    categories = {p[2]:p[1] for x in tree['tree']
                  if x['type']=='tree' and (p:=x['path'].split('/'))[0]=='dataset'
                  and len(p)==3 and p[1] in ('games','utilities','miners')}
    rows, inputs = [], []
    for folder in MANIFESTS:
        path = ROOT/'data/catalog'/folder/'acquisition.jsonl'
        data = path.read_bytes()
        inputs.append({'path':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(data).hexdigest()})
        for line in data.splitlines():
            r=json.loads(line)
            rows.append({**r, **parse_release_path(r['path'],categories)})
    baselines = {}
    for r in rows:
        if r['declared_transformation']=='unobfuscated':
            key=(r['release_variant'],r['program'])
            if key in baselines:
                raise ValueError('ambiguous author baseline: '+str(key))
            baselines[key]=r
    if len(baselines) != 2*len(categories):
        raise ValueError('missing source-program baseline')
    paired = {}
    for r in rows:
        key=(r['release_variant'],r['pair_id'])
        if key in paired:
            raise ValueError('ambiguous optimization pair: '+str(key))
        paired[key]=r
    evidence=[]
    for r in rows:
        base=baselines[(r['release_variant'],r['program'])]
        unoptimized=baselines[('binaries',r['program'])]
        other_variant='binaries-opt' if r['release_variant']=='binaries' else 'binaries'
        other=paired.get((other_variant,r['pair_id']))
        if other is None:
            raise ValueError('optimization counterpart missing: '+r['path'])
        evidence.append({k:r[k] for k in ('dataset','path','sha256','release_variant','program',
                                          'program_category','declared_transformation','parent_id')} | {
            'parent_sha256':unoptimized['sha256'],
            'comparison_baseline_sha256':base['sha256'],
            'comparison_baseline_path':base['path'],
            'exact_bytes_equal_baseline':r['sha256']==base['sha256'],
            'optimization_counterpart_sha256':other['sha256'],
            'exact_bytes_equal_optimization_counterpart':r['sha256']==other['sha256'],
            'parent_basis':'author release program path + pinned dataset source directory; not a malware-family assignment',
            'source_commit':tree['sha'],
            'source_directory':'dataset/'+r['program_category']+'/'+r['program'],
            'observed_transformation':'identical_bytes_to_baseline' if r['sha256']==base['sha256']
                                       and r['declared_transformation']!='unobfuscated' else 'not_individually_verified',
        })
    write_csv('cryptic-bytes-parents.csv',evidence)
    (OUT/'cryptic-bytes-parent-evidence.json').write_text(
        json.dumps({r['path']:r for r in evidence}),encoding='utf-8')
    summary=[]
    grouped=collections.defaultdict(list)
    for r in evidence:
        method=r['declared_transformation'].split('/')[0]
        grouped[(r['release_variant'],method)].append(r)
    for (variant,method),members in sorted(grouped.items()):
        summary.append({'release_variant':variant,'declared_method':method,'occurrences':len(members),
                        'unique_sha256':len({r['sha256'] for r in members}),
                        'source_programs':len({r['parent_id'] for r in members}),
                        'exact_bytes_equal_baseline':sum(r['exact_bytes_equal_baseline'] for r in members),
                        'exact_bytes_equal_optimization_counterpart':sum(r['exact_bytes_equal_optimization_counterpart'] for r in members)})
    write_csv('cryptic-bytes-method-summary.csv',summary)
    program_summary=[]
    for program in sorted(categories):
        members=[r for r in evidence if r['program']==program]
        variants={v:[r for r in members if r['release_variant']==v] for v in ('binaries','binaries-opt')}
        program_summary.append({'program':program,'category':categories[program],
            'unoptimized_occurrences':len(variants['binaries']),
            'unoptimized_unique':len({r['sha256'] for r in variants['binaries']}),
            'optimized_occurrences':len(variants['binaries-opt']),
            'optimized_unique':len({r['sha256'] for r in variants['binaries-opt']}),
            'combined_unique':len({r['sha256'] for r in members})})
    write_csv('cryptic-bytes-program-summary.csv',program_summary)
    result={'inputs':inputs,'source_commit':tree['sha'],'occurrences':len(evidence),
            'unique_sha256':len({r['sha256'] for r in evidence}),'source_programs':len(categories),
            'program_categories':dict(collections.Counter(categories.values())),
            'baseline_records':len(baselines),'missing_counterparts':0,'method_summary':summary,
            'interpretation':'Source groups verified by author paths. Neither malware labels nor functional equivalence nor obfuscation intent independently established. Optimization pairing follows author paths and optimization script, not execution replay.'}
    (OUT/'cryptic-bytes-summary.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result),flush=True)


if __name__=='__main__':
    main()
