import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import platform
import shutil
import transform as t


def run(out, compare=None):
    read=lambda name:json.loads((out/name).read_text(encoding='utf-8'))
    m=read('manifest.json'); assert len(m['records'])==72 and len(m['attacks'])==72
    assert all(a['status']=='ok' and a['same_boolean_dag'] for a in m['attacks'])
    assert all(a['verified_rounds'] is None or a['output_settling_bound']<=a['verified_rounds'] for a in m['attacks'])
    c=read('correctness.json');assert (c['conditions'],c['calls'],c['mismatches'])==(144,646272,0)
    e=read('edges/correctness.json');assert (e['conditions'],e['calls'],e['mismatches'])==(27,121176,0)
    assert read('small-checks.json')=={'cases':209664,'mismatches':0}
    controls=read('edges/controls.json');assert len(controls['unsupported'])==4 and controls['wrong_round_mismatches']==2244
    assert controls['recovery_bound_control']=='insufficient_round_bound'
    rt=read('runtime.json');assert len(rt)==216 and set(Counter(r['path'] for r in rt).values())=={3}
    assert all(len(r['samples_ns'])==9 and r['warmup']==10000 for r in rt)
    an=read('analysis-timing.json');assert len(an)==72 and all(len(a['samples_seconds'])==9 for a in an)
    cross=read('wabt.json');assert len(cross)==72 and sum(r['mismatches'] for r in cross)==0
    comparison=None
    if compare:
        other=json.loads((compare/'manifest.json').read_text());equal=0
        for a,b in zip(m['attacks'],other['attacks']):
            assert (a['kernel'],a['variant'],a['opt'])==(b['kernel'],b['variant'],b['opt'])
            for key in ('path','recovered'):
                assert Path(a[key]).read_bytes()==Path(b[key]).read_bytes();equal+=1
        comparison={'other':str(compare),'identical_binaries':equal,'note':'Recovery bound checking added in this run; transformation unchanged.'}
    summary=read('summary.json')
    lines=['# Measured comparison (O3)','', 'Runtime is the median of three process medians; each process uses 10,000 warmup calls and 9 x 10,000 timed calls. JS calling/input costs are included. Analysis is 1 warmup + 9 runs after parsing, including settling-bound verification and Boolean digest.','',
           '|Kernel|Variant|Bytes|Runtime ns|Process median range ns|Analysis ms|Analysis sample range ms|', '|---|---|---:|---:|---:|---:|---:|']
    for r in summary:
        if r['opt']=='O3':
            p=r['process_medians_ns'];a=r['analysis_range_ms']
            lines.append(f"|{r['kernel']}|{r['variant']}|{r['bytes']}|{r['runtime_median_ns']:.2f}|{min(p):.2f}–{max(p):.2f}|{r['analysis_median_ms']:.3f}|{a[0]:.3f}–{a[1]:.3f}|")
    (out/'comparison.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    versions={'python':platform.python_version(),'platform':platform.platform(), 'wabt':t.w.tool('wat2wasm',['--version']).strip(),
              'binaryen':t.w.tool('wasm-opt',['--version']).strip(),'node':rt[0]['node'],'v8':rt[0]['v8'],'cpu':rt[0]['cpu']}
    (out/'environment.json').write_text(json.dumps(versions,indent=2))
    snapshot=out/'source';snapshot.mkdir(exist_ok=True)
    for f in Path(__file__).parent.iterdir():
        if f.is_file() and f.suffix in ('.py','.cjs','.ps1','.md'):shutil.copy2(f,snapshot/f.name)
    shutil.copy2(Path(__file__).resolve().parents[1]/'stack-cycle/transform.py',snapshot/'dependency-stack-cycle-transform.py')
    shutil.copy2(Path(__file__).resolve().parents[1]/'connectivity-elimination/prototype.py',snapshot/'dependency-wasm-tools.py')
    hashes={str(p.relative_to(out)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.rglob('*')) if p.is_file() and p.name!='audit.json'}
    result={'status':'passed','main_conditions':144,'main_calls':c['calls'],'initial_state_calls':e['calls'],'small_width_cases':209664,
            'wabt_calls':288,'recovered_conditions':72,'same_boolean_dag_conditions':72,'recovery_unsupported':0,'recovery_crash':0,
            'recovery_failure':0,'runtime_processes':216,'comparison':comparison,'hashes':hashes}
    (out/'audit.json').write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k!='hashes'}))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);ap.add_argument('--compare',type=Path);a=ap.parse_args();run(a.output,a.compare)
