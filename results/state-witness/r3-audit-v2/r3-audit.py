"""Bounded static applicability audit of already downloaded replay benchmarks."""
import argparse,hashlib,json,shutil,subprocess,sys,time
from pathlib import Path
import prototype as k

def one(source,out):
    start=time.perf_counter();r={'source':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'bytes':source.stat().st_size}
    try:
        m=k.p.read(source);r['validation']='passed'
        r['shape']={name:k.p.section(m,name) for name in ('memory','table','start','import','export')}
        r['shape']['functionCount']=len(k.p.section(m,'func'));r['shape']['globalCount']=len(k.p.section(m,'global'))
        r['shape']['segmentCount']={n:len(k.p.section(m,n)) for n in ('data','elem')}
        _,meta=k.augment(m,False)
        r['status']='accepted';r['manifest']=k.transform(source,out.with_suffix('.wasm'),False)
    except ValueError as e:r.update({'status':'unsupported','reason':str(e)})
    except RuntimeError as e:r.update({'status':'tool-failure','reason':str(e)[:8000]})
    except RecursionError as e:r.update({'status':'parser-depth-limit','reason':str(e)})
    r['seconds']=time.perf_counter()-start;out.write_text(json.dumps(r,indent=2));print(r['status'])

def main(source,out):
    out.mkdir(parents=True,exist_ok=False);rows=[]
    downloaded=json.loads((source/'download.json').read_text())
    for i,r in enumerate(downloaded['rows']):
        if not r['path'].endswith('.wasm'):continue
        src=source/r['path'];assert hashlib.sha256(src.read_bytes()).hexdigest()==r['sha256'];dest=out/(src.stem+'.json')
        try:
            run=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--one',str(src.resolve()),str(dest.resolve())],capture_output=True,text=True,timeout=60)
            if run.returncode==0:result=json.loads(dest.read_text())
            else:result={'source':r['path'],'status':'audit-process-failure','code':run.returncode,'stderr':run.stderr[-8000:]};dest.write_text(json.dumps(result,indent=2))
        except subprocess.TimeoutExpired:
            result={'source':r['path'],'status':'audit-timeout','seconds':60};dest.write_text(json.dumps(result,indent=2))
        rows.append({'file':src.name,'record':dest.name,'status':result['status'],'reason':result.get('reason')})
        print(json.dumps(rows[-1]),flush=True)
    for name in ('r3-audit.py','prototype.py'):shutil.copy2(Path(__file__).with_name(name),out/name)
    shutil.copy2(source/'download.json',out/'download.json')
    summary={s:sum(x['status']==s for x in rows) for s in sorted({x['status'] for x in rows})}
    (out/'results.json').write_text(json.dumps({'commit':downloaded['commit'],'summary':summary,'rows':rows,'downloadSkips':downloaded['skips']},indent=2))
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file()},indent=2));print(json.dumps(summary))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--one',action='store_true');p.add_argument('source',type=Path);p.add_argument('out',type=Path)
    v=p.parse_args();one(v.source,v.out) if v.one else main(v.source,v.out)
