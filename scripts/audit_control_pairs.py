"""Audit author-path pairings against actual bytes, without assuming labels true."""
import collections
import csv
import hashlib
import json
from analyze_corpus import ROOT, CACHE, acquired_rows


def main():
    rows = [r for r in acquired_rows() if r['dataset'] == 'wasmixer'
            and r['path'].startswith(('benchmark/basic-algorithms/', 'benchmark/realworld_program/'))]
    origins = {(r['path'].split('/')[1], r['path'].split('/')[-1]): r
               for r in rows if r['path'].split('/')[2] == 'origin'}
    pairs, checked = [], {}
    def verify(r):
        sha = r['sha256']
        if sha not in checked:
            checked[sha] = hashlib.sha256((ROOT/r['object']).read_bytes()).hexdigest() == sha
        if not checked[sha]:
            raise ValueError('Stored bytes disagree with manifest '+sha)
    for r in rows:
        group, transform, name = r['path'].split('/')[1:]
        if transform == 'origin':
            continue
        original = origins.get((group, name))
        if original is None:
            continue
        verify(r); verify(original)
        pair = {'dataset':'wasmixer', 'group':group, 'declared_transform':transform,
                'parent_id':group+'/'+name, 'pairing_evidence':'same basename in author origin/transform directories; no semantic equivalence inferred',
                'origin_path':original['path'], 'variant_path':r['path'],
                'origin_sha256':original['sha256'], 'variant_sha256':r['sha256'],
                'exact_bytes_equal':r['sha256'] == original['sha256'],
                'stored_sha256_reverified':True}
        for prefix, item in [('origin',original), ('variant',r)]:
            p=CACHE/(item['sha256']+'.json')
            features=json.loads(p.read_text()) if p.exists() else {}
            pair[prefix+'_analysis_status']=features.get('status','pending')
            pair[prefix+'_analyzer_version']=features.get('analyzer_version')
            for field in ['core_bytes_sha256','code_payload_sha256','data_payload_sha256']:
                pair[prefix+'_'+field]=features.get(field)
        for field in ['core_bytes_sha256','code_payload_sha256','data_payload_sha256']:
            a,b=pair['origin_'+field],pair['variant_'+field]
            pair[field+'_equal']=(a==b) if a is not None and b is not None else None
        pair['control_label_validation']='no_byte_difference_from_origin' if pair['exact_bytes_equal'] else 'byte_difference_only_not_transform_confirmation'
        pairs.append(pair)
    out=ROOT/'results/controls'; out.mkdir(parents=True,exist_ok=True)
    with (out/'wasmixer-pairs.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(pairs[0]));writer.writeheader();writer.writerows(pairs)
    summary=[]
    for group, transform in sorted({(r['group'],r['declared_transform']) for r in pairs}):
        selected=[r for r in pairs if (r['group'],r['declared_transform'])==(group,transform)]
        summary.append({'group':group,'declared_transform':transform,'paired_paths':len(selected),
                        'unique_origin_sha256':len({r['origin_sha256'] for r in selected}),
                        'unique_variant_sha256':len({r['variant_sha256'] for r in selected}),
                        'exact_bytes_equal_pairs':sum(r['exact_bytes_equal'] for r in selected),
                        'core_equal_pairs':sum(r['core_bytes_sha256_equal'] is True for r in selected),
                        'code_equal_pairs':sum(r['code_payload_sha256_equal'] is True for r in selected)})
    (out/'wasmixer-pair-summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    # Indexed by path: the same bytes may have conflicting declared labels.
    (out/'wasmixer-pair-evidence.json').write_text(json.dumps({r['variant_path']:r for r in pairs},indent=2),encoding='utf-8')
    print(json.dumps(summary),flush=True)


if __name__ == '__main__': main()
