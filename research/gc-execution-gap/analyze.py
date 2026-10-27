"""Recompute categories, re-instrument binaries, and separate instrumentation effects."""
import argparse,collections,json,subprocess,shutil
from pathlib import Path
from probe import ROOT,HERE,INSTRUMENT,SOURCE,command,categories,dump,digest
def main(source,out):
    out.mkdir(parents=True,exist_ok=False);errors=[];hashed=0;rebuilt=0;meta={};static={};classified=0
    for manifest in [source/'manifest.json',ROOT/'results/gc-execution-gap/priors-v2/manifest.json']:
        for row in json.loads(manifest.read_text()):
            if row.get('status')=='unavailable':continue
            p=Path(row['path']) if 'path' in row else manifest.parent/row['file'];hashed+=1
            if digest(p)!=row['sha256']:errors.append(dict(kind='hash',path=str(p)))
    modules=json.loads((source/'modules.json').read_text());rows=json.loads((source/'rows.json').read_text());temporary=out/'reencoded.wasm'
    for m in modules:
        if 'metadata' not in m:continue
        key='%s-%d-%s'%(m['name'],m['seed'],m['profile']);meta[m['name'],m['seed'],m['profile']]=m;access=[s for s in m['metadata']['sites'] if s['target'] and s['kind'] in ('StructGet','StructGetS','StructGetU','StructSet','ArrayGet','ArrayGetS','ArrayGetU','ArraySet')]
        st=static.setdefault(m['profile'],dict(modules=0,access_sites=0,modules_with_access=0,kinds=collections.Counter()));st['modules']+=1;st['access_sites']+=len(access);st['modules_with_access']+=bool(access);st['kinds'].update(s['kind'] for s in m['metadata']['sites'])
        for mode in ['plain','count']:
            generated=command([INSTRUMENT,SOURCE/(m['name']+'-shape.wasm'),source/(key+'.wasm'),temporary,mode]);rebuilt+=1
            if generated['status']!='instrumented' or temporary.read_bytes()!=(source/(key+'-'+mode+'.wasm')).read_bytes():errors.append(dict(kind='regeneration',key=key,mode=mode))
            if mode=='count' and generated['sites']!=m['metadata']['sites']:errors.append(dict(kind='site-list',key=key))
    # Keep a single temporary Wasm inside this audit directory for transparent provenance.
    differences=[];terminal=collections.Counter();failed=collections.Counter();new_access=[]
    for r in rows:
        m=meta[r['name'],r['seed'],r['profile']]['metadata'];computed=categories(m,r['counted']);classified+=1
        if computed!=r['categories']:errors.append(dict(kind='category',name=r['name'],seed=r['seed']))
        if not r['status_equal']:differences.append({k:r[k] for k in ['name','seed','profile','variant']}|dict(plain_cause=r['plain'].get('cause'),counted_cause=r['counted'].get('cause')))
        terminal[r['profile'],r['variant'],r['plain']['status'],r['plain'].get('cause','')]+=1
        for site,c in zip(m['sites'],r['counted']['site_counts']):
            if not 0<=c['completed']<=c['attempted']<=100000:errors.append(dict(kind='counter-bounds'))
            if c['attempted']>c['completed']:failed[r['profile'],r['variant'],site['kind'],r['counted'].get('cause','')]+=1
    for r in rows:
        if r['variant']!='depth1' or not r['categories']['target_access'].get('completed',0):continue
        base=next(x for x in rows if x['name']==r['name'] and x['seed']==r['seed'] and x['profile']==r['profile'] and x['variant']=='null')
        if not base['categories']['target_access'].get('completed',0):new_access.append({k:r[k] for k in ['name','seed','profile']})
    cal=[]
    for engine,cmd in [('node',['node',str(HERE/'check-calibration.js'),str(source)]),('spidermonkey',[str(ROOT/'.tools/spidermonkey-150.0.1/js.exe'),str(HERE/'check-calibration.js'),str(source)])]:
        p=subprocess.run(cmd,capture_output=True,text=True,timeout=30);p.check_returncode();result=json.loads(p.stdout);dump(out/(engine+'-calibration.json'),result);cal.append(dict(engine=engine,calls=result['calls'],errors=result['errors']));errors+=result['errors']
    report=dict(hashed_files=hashed,rebuilt_binaries=rebuilt,classified_runs=classified,static=static,instrumentation_status_differences=differences,new_access_vs_null=new_access,terminal_causes=[dict(profile=k[0],variant=k[1],status=k[2],cause=k[3],count=v) for k,v in terminal.items()],attempted_but_failed=[dict(profile=k[0],variant=k[1],kind=k[2],cause=k[3],count=v) for k,v in failed.items()],calibration=cal,errors=errors)
    dump(out/'report.json',report)
    for p in [Path(__file__),HERE/'check-calibration.js']:shutil.copy2(p,out/p.name)
    dump(out/'manifest.json',[dict(path=str(p.resolve()),sha256=digest(p)) for p in out.rglob('*') if p.is_file()]);print(json.dumps(dict(hashed_files=hashed,rebuilt_binaries=rebuilt,classified_runs=classified,static=static,differences=len(differences),new_access=new_access,calibration=cal,errors=errors),indent=2));assert not errors
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('out',type=Path);a=ap.parse_args();main(a.source,a.out)
