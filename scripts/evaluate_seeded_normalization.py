"""New seeded SWAMPED controls; static normalization comparisons only.

Runs only the two previously reviewed generator function bodies, not upstream
module initialization. Never instantiate or execute generated mining Wasm.
"""
import ast
import csv
import json
import random
import re
import time
from collections import Counter
from types import SimpleNamespace
from pathlib import Path
import numpy as np
from normalize_wat_local import normalize
from evaluate_local_normalization import ROOT,WABT,OPT,run,sha,measure

OUT=ROOT/'results/countermeasures/seeded-normalization'
SOURCE=ROOT/'data/source/swamped/code_perturbation.py'
INPUT=ROOT/'results/runtime-mining/cross-dataset/swamped/046dc081.wat'
SEEDS=[20261011,20261012]
RATIOS=[.05,.25]
FUNCTIONS={'nop':'nop_insertion','constsplit':'constant_value_splitting'}


def generate(text, selected, method, seed, ratio):
    rng=np.random.default_rng(seed);prng=random.Random(seed)
    env=dict(random=prng,re=re,retIndent=lambda s:' '*(len(s)-len(s.lstrip())),
             getDist=lambda a,b,n:int(rng.beta(1,1)*n))
    exec(compile(ast.Module(body=selected,type_ignores=[]),str(SOURCE),'exec'),env)
    lines=text.splitlines(keepends=True);spans=[]
    for match in re.finditer(r'^  \(func (\$\S+).*\n',text,re.M):
        start=text[:match.start()].count('\n');end=start+1
        while end<len(lines) and not lines[end].startswith('  ('):
            end+=1
        header=start+1
        if header<end and lines[header].lstrip().startswith('(local '):
            header+=1
        spans.append((match[1],start,end,header))
    functions={name:SimpleNamespace(body=[[line,''] for line in lines[header:end]]) for name,start,end,header in spans}
    excluded=[name for name,f in functions.items() if method=='constsplit' and any(re.search(r'f(?:32|64)\.const',r[0]) for r in f.body)]
    env[FUNCTIONS[method]]({'Function':{name:f for name,f in functions.items() if name not in excluded}},1,1,ratio)
    output=[];last=0;changes=[]
    for name,start,end,header in spans:
        output.extend(lines[last:header]);output.extend(r[0] for r in functions[name].body);last=end
        tagged=[dict(body_row=i,instruction=r[0].rstrip(),tag=r[1]) for i,r in enumerate(functions[name].body) if r[1]]
        if tagged:
            changes.append(dict(function=name,changes=tagged))
    output.extend(lines[last:])
    return ''.join(output),changes,excluded


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    source_text=SOURCE.read_text(encoding='utf-8');tree=ast.parse(source_text)
    selected=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in FUNCTIONS.values()]
    assert len(selected)==2
    input_text=INPUT.read_text(encoding='utf-8')
    generation=[];cases=[]
    baseline=OUT/'baseline.wasm';baseline.with_suffix('.wat').write_text(input_text,encoding='utf-8')
    run([WABT/'wat2wasm.exe',baseline.with_suffix('.wat'),'-o',baseline])
    cases.append(('baseline',baseline,None,None,None))
    for seed in SEEDS:
        for ratio in RATIOS:
            for method in FUNCTIONS:
                name=f'{method}-seed{seed}-ratio{int(ratio*100):02d}'
                text,changes,excluded=generate(input_text,selected,method,seed,ratio)
                path=OUT/(name+'.wasm');path.with_suffix('.wat').write_text(text,encoding='utf-8')
                run([WABT/'wat2wasm.exe',path.with_suffix('.wat'),'-o',path]);run([WABT/'wasm-validate.exe',path])
                log=path.with_suffix('.generation.json')
                log.write_text(json.dumps(dict(changes=changes,floating_functions_excluded=excluded),indent=2),encoding='utf-8')
                generation.append(dict(name=name,path=str(path.relative_to(ROOT)),sha256=sha(path),method=method,seed=seed,ratio=ratio,
                                       transformed_functions=len(changes),tagged_rows=sum(len(c['changes']) for c in changes),log=str(log.relative_to(ROOT))))
                cases.append((name,path,method,seed,ratio))
    development=json.loads((ROOT/'results/runtime-mining/cross-dataset/swamped/controlled-pair-manifest.json').read_text(encoding='utf-8'))
    old_hashes={c['sha256'] for c in development['cases']}
    assert len({g['sha256'] for g in generation})==8 and not any(g['sha256'] in old_hashes for g in generation)
    (OUT/'generation.json').write_text(json.dumps(dict(cases=generation,baseline_sha256=sha(baseline),source_sha256=sha(SOURCE),
                input_wat_sha256=sha(INPUT),seeds=SEEDS,ratios=RATIOS,normalizer_sha256=sha(ROOT/'scripts/normalize_wat_local.py'),
                generator_commit='04e2bcc03be443bf24dbcfd729d4f54da8133ac5',
                adaptation='Previously reviewed function bodies, seeded persistent beta(1,1) RNG and local seeded Python RNG. Floating-constant functions excluded.',
                scope='New variants of the same underlying program, not independent implementations or in-the-wild obfuscation.'),indent=2),encoding='utf-8')
    records=[]
    for name,path,method,seed,ratio in cases:
        original,wat=measure(path)
        targets=[('unmodified',path,[],None)]
        for label,rules in [('nop',('nop',)),('integer-fold',('integer-fold',)),('both',('nop','integer-fold'))]:
            start=time.perf_counter();text,events=normalize(wat,rules);elapsed=(time.perf_counter()-start)*1000
            target=OUT/(name+'-'+label+'.wasm');target.with_suffix('.wat').write_text(text,encoding='utf-8')
            target.with_suffix('.events.json').write_text(json.dumps(events,indent=2),encoding='utf-8')
            run([WABT/'wat2wasm.exe',target.with_suffix('.wat'),'-o',target]);targets.append((label,target,events,elapsed))
        for label,flags in [('binaryen-local',['--vacuum','--precompute']),('binaryen-O2',['-O2'])]:
            target=OUT/(name+'-'+label+'.wasm');start=time.perf_counter();run([OPT,path,*flags,'-o',target]);elapsed=(time.perf_counter()-start)*1000
            targets.append((label,target,[],elapsed))
        for label,target,events,elapsed in targets:
            metrics,_=measure(target)
            records.append(dict(source=name,method=method,seed=seed,ratio=ratio,variant=label,path=str(target.relative_to(ROOT)),**metrics,
                                events=len(events),events_by_rule=dict(Counter(e['rule'] for e in events)),transform_elapsed_ms=elapsed,
                                timing_scope='in-process rewrite only' if label in ['nop','integer-fold','both'] else 'optimizer process startup and run' if label.startswith('binaryen') else None,
                                raw_import_export_records_equal=metrics['imports']==original['imports'] and metrics['exports']==original['exports']))
    for row in records:
        base=next(r for r in records if r['source']=='baseline' and r['variant']==row['variant'])
        row['equal_equally_processed_reference']=row['sha256']==base['sha256']
        row['instruction_difference_to_processed_reference']=row['instruction_count']-base['instruction_count']
        row['byte_difference_to_processed_reference']=row['bytes']-base['bytes']
    report=dict(records=records,generation_sha256=sha(OUT/'generation.json'),evaluator_sha256=sha(Path(__file__)),
                normalizer_sha256=sha(ROOT/'scripts/normalize_wat_local.py'),binaryen_sha256=sha(OPT),
                tools=dict(wabt=run([WABT/'wasm2wat.exe','--version']).strip(),binaryen=run([OPT,'--version']).strip()),
                runtime_executed=False,hash_outputs_checked=False,
                scope='Frozen rules on new seeds and ratios; same-program generalization only. No mining or throughput measurement.')
    (OUT/'comparison.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    with (OUT/'comparison.csv').open('w',encoding='utf-8',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=['source','method','seed','ratio','variant','sha256','bytes','instruction_count','events','equal_equally_processed_reference','instruction_difference_to_processed_reference','byte_difference_to_processed_reference','transform_elapsed_ms','timing_scope'],extrasaction='ignore')
        writer.writeheader();writer.writerows(records)
    print(json.dumps([dict(source=r['source'],variant=r['variant'],events=r['events'],equal=r['equal_equally_processed_reference'],instruction_difference=r['instruction_difference_to_processed_reference']) for r in records if r['variant'] in ['both','binaryen-O2']],indent=2))


if __name__=='__main__':
    main()
