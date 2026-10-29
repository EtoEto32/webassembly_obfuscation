import json,subprocess,sys,time
from pathlib import Path
import recover as r
def main(source,out):
    source=Path(source);out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);rows=[];targets=[]
    for t in json.loads((source/'targets.json').read_text()):
        f=out/(t['label']+'-recovered.wasm');start=time.perf_counter()
        try:
            result=r.recover(t['path'],f);result.update(label=t['label'],status='recovered')
            opt=f.with_name(f.stem+'-O3.wasm');r.q.tool('wasm-opt',[f,'-O3','--enable-multivalue','-o',opt]);r.q.w.tool('wasm-validate',[opt])
            result['optimized_bytes']=opt.stat().st_size
            targets.extend({'label':t['label']+'-recovered-'+flavor,'path':str(p),'info':{}} for flavor,p in [('raw',f),('O3',opt)])
        except r.Unsupported as e:result={'label':t['label'],'status':'unsupported','reason':str(e)}
        except subprocess.TimeoutExpired as e:result={'label':t['label'],'status':'timeout','reason':str(e)}
        except Exception as e:result={'label':t['label'],'status':'error','reason':repr(e)}
        result['total_ms']=1000*(time.perf_counter()-start);rows.append(result);print(t['label'],result['status'],flush=True)
        (out/'recovery.json').write_text(json.dumps(rows,indent=2));(out/'targets.json').write_text(json.dumps(targets,indent=2))
    if targets:
        cp=subprocess.run(['node',str(Path(__file__).with_name('check.cjs')),str(out/'targets.json'),str(out/'checks.json')],capture_output=True,text=True,timeout=180)
        (out/'check.stdout.txt').write_text(cp.stdout);(out/'check.stderr.txt').write_text(cp.stderr)
        if cp.returncode:raise RuntimeError(cp.stderr)
        print(cp.stdout.strip())
if __name__=='__main__':main(*sys.argv[1:])
