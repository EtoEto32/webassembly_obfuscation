"""Resource-bounded Wasmtime replay; fuel exhaustion is not a program trap."""
import argparse,hashlib,importlib.metadata,json,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'))
import wasmtime as wt
FUEL=500_000_000

def one(audit,original,normalized,name,out,fuel=FUEL):
    cfg=wt.Config();cfg.consume_fuel=bool(fuel);engine=wt.Engine(cfg);r=json.loads((audit/(name+'.json')).read_text());meta=r['manifest']
    memname=json.loads(next(e[1] for e in meta['originalExports'] if e[2]==['memory','0']));rows=[];baseline=None
    for kind,file in [('original',original/'wasm-r3-bench'/(name+'.wasm')),('normalized',normalized/'wasm-r3-bench'/(name+'.wasm')),('observed',audit/(name+'.wasm'))]:
        started=time.perf_counter();mod=wt.Module(engine,file.read_bytes())
        with wt.Store(engine) as s:
            s.set_limits(memory_size=256*65536)
            if fuel:s.set_fuel(fuel)
            e=wt.Instance(s,mod,[]).exports(s);before=time.perf_counter()
            try:outcome={'value':e['_start'](s)};status='completed';detail=None
            except wt.Trap as exc:
                status='fuel-exhausted' if exc.trap_code==wt.TrapCode.OUT_OF_FUEL else 'guest-trap'
                outcome={'fuelExhausted':True} if status=='fuel-exhausted' else {'trap':True};detail=str(exc)[:2000]
            elapsed=time.perf_counter()-before;memory=bytes(e[memname].read(s));remaining=s.get_fuel() if fuel else None
            if baseline is None:baseline=(status,outcome,memory)
            # Under the same instruction budget the original bodies should behave alike.
            assert (status,outcome,memory)==baseline,(name,kind,status)
            row={'kind':kind,'status':status,'outcome':outcome,'detail':detail,'memoryBytes':len(memory),
                 'memorySha256':hashlib.sha256(memory).hexdigest(),'inputSha256':hashlib.sha256(file.read_bytes()).hexdigest(),
                 'fuelUsed':fuel-remaining if fuel else None,'executionSeconds':elapsed,'totalSeconds':time.perf_counter()-started}
            rows.append(row);out.write_text(json.dumps({'name':name,'wasmtime':importlib.metadata.version('wasmtime'),'rows':rows,'status':'in-progress'},indent=2))
    result={'name':name,'wasmtime':importlib.metadata.version('wasmtime'),'rows':rows,'status':'compared',
            'scope':'API outcomes and exported memory only, within-engine byte comparison; fuel exhaustion not a completed execution.'}
    out.write_text(json.dumps(result,indent=2));print(json.dumps({'name':name,'status':baseline[0],'memoryBytes':len(baseline[2])}))

def main(audit,original,normalized,out,fuel=FUEL,names=None):
    out.mkdir(parents=True,exist_ok=False);rows=[]
    for c in json.loads((audit/'results.json').read_text())['rows']:
        if c['status']!='accepted':continue
        name=Path(c['file']).stem;dest=out/(name+'.json')
        if names and name not in names:continue
        cmd=[sys.executable,str(Path(__file__).resolve()),str(audit.resolve()),str(original.resolve()),str(normalized.resolve()),str(dest.resolve()),'--one',name,'--fuel',str(fuel)]
        try:
            r=subprocess.run(cmd,capture_output=True,text=True,timeout=45)
            row={'name':name,'status':'compared' if r.returncode==0 else 'process-failure','code':r.returncode,'stdout':r.stdout,'stderr':r.stderr[-8000:]}
        except subprocess.TimeoutExpired:row={'name':name,'status':'timeout','seconds':45}
        rows.append(row);print(json.dumps(row),flush=True)
    summary={s:sum(r['status']==s for r in rows) for s in sorted({r['status'] for r in rows})}
    (out/'results.json').write_text(json.dumps({'summary':summary,'rows':rows,'memoryLimitPages':256,'fuelPerEntry':fuel or None,'deadlineSeconds':45},indent=2))
    shutil.copy2(__file__,out/'r3-cross.py');(out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()},indent=2));print(json.dumps(summary))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('audit',type=Path);p.add_argument('original',type=Path);p.add_argument('normalized',type=Path);p.add_argument('out',type=Path);p.add_argument('--one')
    p.add_argument('--fuel',type=int,default=FUEL);p.add_argument('--names')
    v=p.parse_args();one(v.audit,v.original,v.normalized,v.one,v.out,v.fuel) if v.one else main(v.audit,v.original,v.normalized,v.out,v.fuel,v.names.split(',') if v.names else None)
