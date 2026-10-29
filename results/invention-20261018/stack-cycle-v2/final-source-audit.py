"""Verify saved condition coverage and hash the evidence; no empirical proof claim."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import transform as t
from experiment import save


def main(out,compare=None):
    def read(name):return json.loads((out/name).read_text(encoding='utf-8'))
    rows=read('manifest.json');assert len(rows)==84
    assert all(x['recovery']['status']=='recovered' for x in rows)
    c=read('correctness.json');assert c['conditions']==168 and c['calls']==611730 and c['mismatches']==0
    assert c['wrong_next']=={'inputs':4107,'detected':4106}
    assert c['trap_reason_differences']==52 and sum(x['memory_mismatches'] for x in c['rows'])==0
    assert all(x['trap_reason_differences']==0 for x in c['rows'] if x['opt']=='raw')
    interpreter=read('interpreter.json');assert (interpreter['calls'],interpreter['mismatches'])==(336,0)
    edges=read('edge-correctness.json');assert (edges['conditions'],edges['calls'],edges['mismatches'])==(30,30990,0)
    assert len(read('unsupported.json'))==5
    assert read('planner-check.json')=={'exhaustive_small_cases':200,'mismatches':0}
    transforms=read('transforms.json');assert len(transforms)==24
    for k in {x['kernel'] for x in transforms}:
        for n in (4,8,16):
            a=next(x for x in transforms if x['kernel']==k and x['variant']==f'locals{n}')
            b=next(x for x in transforms if x['kernel']==k and x['variant']==f'payload{n}')
            for field in ('shape','cuts','physical_order','source_instructions','protected_instructions','largest_fragment','input_sha256'):assert a[field]==b[field]
            assert b['added_locals']==0 and a['added_locals']==len(a['shape'])+1
    perf=read('performance.json');assert len(perf)==252
    assert set(Counter(x['file'] for x in perf).values())=={3}
    raw_functions={}
    for row in rows:
        for kind in ('path','recovered_path'):
            expected=row['sha256'] if kind=='path' else row['recovered_sha256']
            assert hashlib.sha256((out/row[kind]).read_bytes()).hexdigest()==expected
        if row['opt']=='raw':
            mod=t.w.parse(t.w.tool('wasm2wat',[out/row['recovered_path'],'--fold-exprs','--no-debug-names']))
            f=next(x for x in mod[1:] if x[0]=='func')
            # Ignore only the type reference declaration; retain all instructions.
            f=[x for x in f if not(isinstance(x,list) and x[0]=='type')]
            raw_functions.setdefault(row['kernel'],set()).add(hashlib.sha256(t.w.emit(f).encode()).hexdigest())
    assert all(len(v)==1 for v in raw_functions.values())
    comparison=None
    if compare is not None:
        other=json.loads((compare/'manifest.json').read_text(encoding='utf-8'))
        assert [x['path'] for x in rows]==[x['path'] for x in other]
        assert all(a['sha256']==b['sha256'] and a['recovered_sha256']==b['recovered_sha256'] for a,b in zip(rows,other))
        assert (out/'inputs.json').read_bytes()==(compare/'inputs.json').read_bytes()
        comparison={'other':str(compare),'byte_identical_inputs_and_recovered_binaries':168,'identical_generated_inputs':True}
    for file in Path(__file__).parent.iterdir():
        if file.is_file() and file.suffix in ('.py','.cjs','.ps1','.md'):shutil.copy2(file,out/('final-source-'+file.name))
    common=Path(__file__).resolve().parents[1]/'connectivity-elimination/prototype.py'
    shutil.copy2(common,out/'common-prototype.py')
    hashes={str(p.relative_to(out)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.rglob('*')) if p.is_file() and p.name!='audit.json'}
    report={'status':'passed','conditions':84,'main_calls':c['calls'],'edge_calls':edges['calls'],'interpreter_calls':interpreter['calls'],
            'trap_reason_differences':52,'raw_recovered_function_variants':{k:len(v) for k,v in raw_functions.items()},'replay_comparison':comparison,'hashes':hashes}
    save(out/'audit.json',report);print(json.dumps({k:v for k,v in report.items() if k!='hashes'}))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);ap.add_argument('--compare',type=Path);a=ap.parse_args();main(a.output,a.compare)
