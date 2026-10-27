"""Evidence/source/link audit; does not rerun the completed performance study."""
import argparse,ast,json,re,subprocess
from pathlib import Path
import prototype as p
def run(output):
    dst=Path(output)
    if dst.exists():raise FileExistsError(dst)
    root=p.ROOT;rd=root/'results/invention-20261022';counts={};source_checks=[]
    for name in ('recursive-frame-v2','recursive-frame-audit-v2','recursive-frame-runtime-v2'):
        base=rd/name;pins=json.loads((base/'pins.json').read_text(encoding='utf-8'))
        for file,h in pins.items():assert p.digest(base/file)==h,(name,file)
        counts[name]=len(pins)
        for f in base.glob('source-*'):
            if f.suffix not in ('.py','.cjs'):continue
            current=Path(__file__).parent/f.name[len('source-'):]
            assert p.digest(f)==p.digest(current),f
            source_checks.append(str(f.relative_to(root)))
    pins=json.loads((rd/'recursive-frame-report-v2/input-pins.json').read_text(encoding='utf-8'))
    for file,h in pins.items():assert p.digest(root/file)==h,file
    counts['report_inputs']=len(pins)
    syntax=[]
    for f in Path(__file__).parent.glob('*.py'):ast.parse(f.read_text(encoding='utf-8'));syntax.append(f.name)
    for f in Path(__file__).parent.glob('*.cjs'):
        r=subprocess.run(['node','--check',str(f)],capture_output=True,text=True,timeout=30)
        assert r.returncode==0,r.stderr;syntax.append(f.name)
    links=[]
    for f in Path(__file__).parent.glob('*.md'):
        for target in re.findall(r'\]\(([^)]+)\)',f.read_text(encoding='utf-8')):
            if '://' in target or target.startswith('#'):continue
            dest=(f.parent/target.split('#')[0]).resolve();assert dest.exists(),(str(f),target);links.append((f.name,target))
    checks=json.loads((rd/'recursive-frame-v2/checks.json').read_text());manifest=json.loads((rd/'recursive-frame-v2/manifest.json').read_text());rec=json.loads((rd/'recursive-frame-v2/recovery.json').read_text())
    assert len(checks['rows'])==len(manifest['binaries'])==42
    assert sum(r['calls'] for r in checks['rows'] if not r['negative'])==checks['positiveCalls']==265680
    assert checks['positiveMismatches']==checks['unexpectedTraps']==0
    assert all(r['mismatch']==7121 for r in checks['rows'] if r['negative'])
    assert all(r['function_summaries']==1 and r['stack_unfoldings']==0 for r in rec if r['status']=='recovered')
    assert all(r['peak_polynomial_terms']==29 for r in rec if r['mode']=='dynamic')
    assert all(b['function_parameters'][0]==7 for b in manifest['binaries'] if b['mode']=='dynamic')
    runtime=json.loads((rd/'recursive-frame-runtime-v2/runtime.json').read_text());assert len(runtime)==72 and sum(len(r['measurement']['batches']) for r in runtime)==648
    for name in ('wide','small','edge'):
        for depth in (8,31):assert len({r['measurement']['verification'] for r in runtime if r['name']==name and r['depth']==depth})==1
    files=[*Path(__file__).parent.glob('*.*'),root/'research/connectivity-elimination/prototype.py']
    result=dict(status='passed',pin_counts=counts,source_snapshots_equal=len(source_checks),syntax=syntax,local_links=len(links),facts=dict(binaries=42,positive_calls=265680,negative_conditions=6,summary_conditions=18,processes=72,batches=648),current_sources={str(f.relative_to(root)):p.digest(f) for f in files if f.is_file()})
    p.save(dst,result);print(json.dumps({k:v for k,v in result.items() if k!='current_sources'}))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output');a=ap.parse_args();run(a.output)
