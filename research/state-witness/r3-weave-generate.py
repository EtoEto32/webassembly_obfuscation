"""Generate bounded Weave controls from the predeclared R3 normal-completion set."""
import argparse,hashlib,json,shutil,subprocess,time
from pathlib import Path
import prototype as k
import composition as c
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def main(source,audit,out):
    out.mkdir(parents=True,exist_ok=False);rows=[];exe=ROOT/'.tools/weave-build/target/release/weave-default.exe'
    for row in json.loads((audit/'results.json').read_text())['rows']:
        if row['status']!='accepted' or row['file']=='pathfinding.wasm':continue
        name=Path(row['file']).stem;src=next(source.rglob(row['file']));raw=out/(name+'.wasm');shutil.copy2(src,raw)
        m,meta=c.with_directory(k.p.read(src))
        # Directory elements already declare references; avoid redundant wrappers.
        m=[x for x in m if not (isinstance(x,list) and x and x[0]=='export' and x[1].startswith('"__sw_func_'))]
        obs=out/(name+'-directory.wasm');k.p.compile_wat(k.p.w.emit(m),obs)
        (out/(name+'-manifest.json')).write_text(json.dumps(meta,indent=2))
        for kind,input_ in [('plain',raw),('directory',obs)]:
            dest=out/(name+'-'+kind+'-woven.wasm');start=time.perf_counter()
            r={'name':name,'kind':kind,'original':raw.name,'source':input_.name,'output':dest.name,'manifest':name+'-manifest.json'}
            try:
                proc=subprocess.run([str(exe),str(input_),str(dest)],capture_output=True,text=True,encoding='utf8',timeout=60)
                r.update({'code':proc.returncode,'stderr':proc.stderr[-8000:]})
                r['status']='valid' if proc.returncode==0 else 'transform-failure'
                if proc.returncode==0:k.p.tool('wasm-validate',[dest])
            except subprocess.TimeoutExpired:r['status']='transform-timeout'
            except RuntimeError as err:r.update({'status':'validation-failure','reason':str(err)[-8000:]})
            r['seconds']=time.perf_counter()-start;rows.append(r);print(json.dumps(r),flush=True)
    for n in ('r3-weave-generate.py','composition.py','prototype.py','weave-default.rs'):shutil.copy2(HERE/n,out/n)
    shutil.copy2(ROOT/'.tools/weave-build/js/weave.mjs',out/'weave.mjs')
    (out/'results.json').write_text(json.dumps({'rows':rows,'exeSha256':hashlib.sha256(exe.read_bytes()).hexdigest(),
      'excluded':[{'name':'pathfinding','reason':'original traps in prior run; exclude from normal-completion set'}]},indent=2))
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file()},indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('audit',type=Path);p.add_argument('out',type=Path);v=p.parse_args();main(v.source,v.audit,v.out)
