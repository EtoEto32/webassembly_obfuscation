import json,platform,subprocess,sys,time
from pathlib import Path
import prototype as p
def main(out):
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    source=out/'source.wasm';p.q.compile(p.source(),source)
    rows=[]
    for label,mode,layers,linear in [('plain','plain',0,False),('linear','native',1,True),('fiber1','native',1,False),('fiber2','native',2,False),('repair1','repair',1,False)]:
        raw=source if mode=='plain' else out/(label+'-raw.wasm')
        info={} if mode=='plain' else p.transform(source,raw,mode,layers,211051,linear)
        for opt in ('raw','O3'):
            f=raw if opt=='raw' else out/(label+'-O3.wasm')
            if opt=='O3':p.q.tool('wasm-opt',[raw,'-O3','--enable-bulk-memory','--enable-multivalue','-o',f]);p.q.w.tool('wasm-validate',[f])
            probe=out/(label+'-'+opt+'-probe.wasm');p.probe(f,probe)
            rows.append({'label':label+'-'+opt,'kind':label,'opt':opt,'path':str(f),'probe':str(probe),'sha256':p.q.digest(f),'bytes':f.stat().st_size,'info':info})
    (out/'targets.json').write_text(json.dumps(rows,indent=2))
    (out/'environment.json').write_text(json.dumps({'platform':platform.platform(),'python':sys.version,'wabt':p.q.w.tool('wasm-validate',['--version']).strip(),'binaryen':p.q.tool('wasm-opt',['--version']).strip()},indent=2))
    cp=subprocess.run(['node',str(Path(__file__).with_name('check.cjs')),str(out/'targets.json'),str(out/'checks.json')],capture_output=True,text=True,timeout=180)
    (out/'check.stdout.txt').write_text(cp.stdout);(out/'check.stderr.txt').write_text(cp.stderr)
    if cp.returncode:raise RuntimeError(cp.stderr)
    print(cp.stdout.strip())
if __name__=='__main__':main(sys.argv[1])
