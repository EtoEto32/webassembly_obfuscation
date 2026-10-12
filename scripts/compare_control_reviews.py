"""Reproduce narrow comparisons used in authored stage-2 static reviews."""
import hashlib
import json
import re
import subprocess
from analyze_corpus import ROOT, CACHE, WABT, OP, FUNC


def decoded(sha):
    functions={}; current=None
    for line in (ROOT/'results/cases'/sha/'disassembly.txt').read_text().splitlines():
        f=FUNC.match(line.strip())
        if f:
            current=int(f[2]);functions[current]=[]
        m=OP.match(line)
        if m and current is not None:
            functions[current].append((m[1],m[2],m[3].strip()))
    return functions


def main():
    plan=json.loads((ROOT/'experiments/review-selection-stage2.json').read_text())
    rows=plan['selected']; output=ROOT/'results/controls'
    result={'name_pairs':[],'memory_cases':[],
            'scope':'decoded instruction comparisons include numeric operands and local declarations, ignore display-name annotations; not whole-module semantic equivalence'}
    for i,j in [(0,1),(3,4)]:
        a,b=decoded(rows[i]['sha256']),decoded(rows[j]['sha256'])
        normalize=lambda instructions:[(op,re.sub(r'\s*<[^>]*>','',args)) for _,op,args in instructions]
        result['name_pairs'].append({'origin_sha256':rows[i]['sha256'],'variant_sha256':rows[j]['sha256'],
            'origin_defined_functions':len(a),'variant_defined_functions':len(b),
            'matching_decoded_functions':sum(normalize(a[k])==normalize(b.get(k,[])) for k in a),
            'pairing':'same author-path program; functions compared by index'})
    for i in [2,5]:
        sha=rows[i]['sha256'];folder=ROOT/'results/cases'/sha
        x=subprocess.run([str(WABT/'wasm-objdump.exe'),'-x',str(folder/'review-core.wasm')],capture_output=True,check=True,text=True).stdout
        (folder/'core-details.txt').write_text(x,encoding='utf-8')
        functions=decoded(sha)
        reads=[{'function':fn,'offset':off} for fn,ops in functions.items() for off,op,arg in ops if op=='global.get' and arg=='1']
        writes=[{'function':fn,'offset':off} for fn,ops in functions.items() for off,op,arg in ops if op=='global.set' and arg=='1']
        info=json.loads((CACHE/(sha+'.json')).read_text())
        result['memory_cases'].append({'sha256':sha,'offset_scope':'custom sections stripped',
            'global_1_definition':[line.strip() for line in x.splitlines() if '- global[1] ' in line],
            'global_1_reads':reads,'global_1_writes':writes,
            'global_exports':[e for e in info.get('exports',[]) if e['kind']==3],
            'global_imports':[e for e in info.get('imports',[]) if e['kind']==3]})
    sha=rows[8]['sha256'];info=json.loads((CACHE/(sha+'.json')).read_text())
    details=subprocess.run([str(WABT/'wasm-objdump.exe'),'-x',str(ROOT/info['object'])],capture_output=True,check=True,text=True).stdout
    (ROOT/'results/cases'/sha/'module-details.txt').write_text(details,encoding='utf-8')
    result['call_indirect_pair']={'origin_sha256':rows[6]['sha256'],'variant_sha256':sha,
        'observed_table_entries':[l.strip() for l in details.splitlines() if re.search(r'elem\[(20|54)\]',l)]}
    (output/'stage2-comparisons.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result),flush=True)


if __name__=='__main__': main()
