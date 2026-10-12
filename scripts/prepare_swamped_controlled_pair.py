"""Use reviewed SWAMPED transformation functions with an explicit seeded selection adaptation."""
import ast
import hashlib
import json
import random
import re
import subprocess
from pathlib import Path
from types import SimpleNamespace
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/runtime-mining/cross-dataset/swamped'
SOURCE=ROOT/'data/source/swamped/code_perturbation.py'
COMMIT='04e2bcc03be443bf24dbcfd729d4f54da8133ac5'
wat=(OUT/'046dc081.wat').read_text()
tree=ast.parse(SOURCE.read_text(encoding='utf-8'))
names=['nop_insertion','constant_value_splitting']
selected=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
assert len(selected)==2

def sha(data):return hashlib.sha256(data).hexdigest()
def run_case(name, function=None):
    seed=20261008
    rng=np.random.default_rng(seed);random.seed(seed)
    # Original getDist uses a fresh RNG and beta(1,1), ignoring alpha/beta.
    # Retain that distribution while holding one seeded generator for reproducibility.
    env={'random':random,'re':re,'retIndent':lambda s:' '*(len(s)-len(s.lstrip())),
         'getDist':lambda a,b,n:int(rng.beta(1,1)*n)}
    exec(compile(ast.Module(body=selected,type_ignores=[]),str(SOURCE),'exec'),env)
    lines=wat.splitlines(keepends=True)
    spans=[]
    for match in re.finditer(r'^  \(func (\$\S+).*\n',wat,re.M):
        start=wat[:match.start()].count('\n')
        end=start+1
        while end<len(lines) and not lines[end].startswith('  ('):
            end+=1
        header=start+1
        if header<end and lines[header].lstrip().startswith('(local '):header+=1
        spans.append((match.group(1),start,end,header))
    original={n:SimpleNamespace(body=[[line,''] for line in lines[h:e]]) for n,s,e,h in spans}
    excluded=[]
    if function=='constant_value_splitting':
        excluded=[n for n,f in original.items() if any(re.search(r'f(?:32|64)\.const',row[0]) for row in f.body)]
    parsed={'Function':{n:f for n,f in original.items() if n not in excluded}}
    if function:env[function](parsed,1,1,.10)
    new=[];last=0;changes=[]
    for n,s,e,h in spans:
        new.extend(lines[last:h]);body=original[n].body
        new.extend(item[0] for item in body);last=e
        tagged=[dict(transformed_body_row=i,instruction=item[0].rstrip(),tag=item[1]) for i,item in enumerate(body) if item[1]]
        if tagged:changes.append(dict(function=n,original_wat_first_line=s+1,changes=tagged))
    new.extend(lines[last:]);text=''.join(new)
    target=OUT/(name+'.wat');target.write_text(text)
    binary=OUT/(name+'.wasm')
    subprocess.run([str(ROOT/'.tools/wabt-1.0.42/bin/wat2wasm.exe'),str(target),'-o',str(binary)],check=True)
    subprocess.run([str(ROOT/'.tools/wabt-1.0.42/bin/wasm-validate.exe'),str(binary)],check=True)
    return dict(name=name,sha256=sha(binary.read_bytes()),object=str(binary.relative_to(ROOT)).replace('\\','/'),
                wat_sha256=sha(target.read_bytes()),bytes=binary.stat().st_size,source_function=function,
                selection_seed=seed,ratio=.10 if function else 0,transformed_functions=len(changes),
                floating_constant_functions_excluded=excluded,changes=changes)

cases=[run_case('046dc081-roundtrip'),run_case('046dc081-nop10','nop_insertion'),
       run_case('046dc081-constsplit10','constant_value_splitting')]
report=dict(original_sha256='046dc081076d9cea6831967619b862cc80fa8c2381346406ec639c899cda640f',
            source_url=f'https://github.com/SKKU-SecLab/SWAMPED/blob/{COMMIT}/strategies/code_perturbation.py',
            source_sha256=sha(SOURCE.read_bytes()),wabt_version='1.0.42',cases=cases,
            provenance='locally generated controls, not publicly distributed SWAMPED transformed samples',
            adaptation='Reviewed original function bodies executed with a minimal Function-body adapter. getDist retains beta(1,1) but uses a seeded persistent numpy RNG. Python random also seeded.',
            mechanism={'nop':'Inserted nop leaves stack, memory and control unchanged.',
                       'constant_split':'Integer const c becomes const a, const b, add with a+b=c modulo bit width.'},
            constraints=['No floating constant replacement.','Validation and finite hash checks are required before timing.',
                         'Compare transformed binaries to the same WAT roundtrip control, not differently assembled original bytes.'])
(OUT/'controlled-pair-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps([{k:v for k,v in r.items() if k!='changes'} for r in cases],indent=2))

