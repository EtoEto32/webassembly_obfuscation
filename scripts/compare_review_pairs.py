"""Compare inspected pairs without asserting parentage or behavioral identity."""
import difflib
import json
import re
from acquire import ROOT

PAIRS=[('22a8da39','4ab6ed5e'),('2eb0e7c2','1d38d08e'),('c1be4071','65debcbe')]


def functions(path):
    result={}; current=None
    for line in path.read_text().splitlines():
        match=re.search(r'func\[(\d+)\]',line)
        if match: current=int(match[1]);result[current]=[]
        if current is not None and '|' in line:
            op=line.split('|',1)[1].strip()
            if op:result[current].append(op)
    return result


def main():
    output=ROOT/'results/cases/pair-comparisons'; output.mkdir(exist_ok=True)
    reports=[]
    for a,b in PAIRS:
        paths=[]
        for prefix in [a,b]:
            matches=list((ROOT/'results/cases').glob(prefix+'*'))
            if len(matches)!=1:raise ValueError('Ambiguous case prefix')
            paths.append(matches[0])
        hashes=[p.name for p in paths]
        ds=[json.loads((ROOT/'data/analysis-v2'/(h+'.json')).read_text()) for h in hashes]
        if [f['function_index'] for f in ds[0]['functions']] != [f['function_index'] for f in ds[1]['functions']]:
            raise ValueError('Function alignment not established')
        text=[functions(p/'disassembly.txt') for p in paths]
        changed=[];diffs=[]
        for fa,fb in zip(ds[0]['functions'],ds[1]['functions']):
            if fa['body_sha256']==fb['body_sha256']:continue
            index=fa['function_index']; changed.append({'function_index':index,
                'body_sha256_a':fa['body_sha256'],'body_sha256_b':fb['body_sha256'],
                'body_bytes_a':fa['body_bytes'],'body_bytes_b':fb['body_bytes']})
            diffs += [f'FUNCTION {index}\n']+list(difflib.unified_diff(text[0][index],text[1][index],fromfile=hashes[0],tofile=hashes[1],n=8))
        (output/(a+'-'+b+'.diff.txt')).write_text('\n'.join(diffs),encoding='utf-8')
        reports.append({'sha256_a':hashes[0],'sha256_b':hashes[1],
            'defined_functions':len(ds[0]['functions']),
            'identical_function_bodies':len(ds[0]['functions'])-len(changed),
            'code_payload_equal':ds[0]['code_payload_sha256']==ds[1]['code_payload_sha256'],
            'data_payload_equal':ds[0]['data_payload_sha256']==ds[1]['data_payload_sha256'],
            'changed_functions':changed,'proven_parent_relation':False,
            'scope':'byte identity and decoded instruction difference; no whole-module semantic equivalence claim'})
    (output/'pairs.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')
    for r in reports: print(r['sha256_a'][:8],r['sha256_b'][:8],r['identical_function_bodies'],'/',r['defined_functions'],'identical function bodies')


if __name__=='__main__':main()
