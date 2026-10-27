"""Restrict both baselines to the job's public API before optimization."""
import argparse,hashlib,json,shutil
from pathlib import Path
import prototype as p
HERE=Path(__file__).resolve().parent
def main(source,out):
    out.mkdir(parents=True,exist_ok=False)
    for f in ('bench-inputs.py','prototype.py'):shutil.copy2(HERE/f,out/f)
    rows=[]
    for fixture in ('small','medium'):
        for job in ('work-only','grow-drop'):
            names={'work'} if job=='work-only' else {'work','grow','tgrow','init','tinit','ddrop','edrop'}
            m=p.read(source/(fixture+'-source.wasm'))
            m=['module',*[x for x in m[1:] if x[0]!='export' or x[1][1:-1] in names]]
            raw=out/(fixture+'-'+job+'-source.wasm');p.compile_wat(p.w.emit(m),raw)
            for mode in ('source','full','plain'):
                target=raw if mode=='source' else out/(fixture+'-'+job+'-'+mode+'.wasm')
                if mode!='source':p.transform(raw,target,mode)
                optimized=target.with_name(target.stem+'-O3.wasm')
                p.tool('wasm-opt',[target,'-O3','--enable-bulk-memory','--enable-reference-types','-o',optimized])
                rows.append({'fixture':fixture,'job':job,'mode':mode,'pipeline':'O3','file':optimized.name,'bytes':optimized.stat().st_size})
    m={'directory':str(out.resolve()),'rows':rows,'sourceSHA256':hashlib.sha256((source/'sha256.json').read_bytes()).hexdigest(),
       'note':'Both sides expose exactly the job API; reset export only in reset variants. Not the full original 34-export fixture interface.'}
    (out/'manifest.json').write_text(json.dumps(m,indent=2),encoding='utf8')
    (out/'sha256.json').write_text(json.dumps({x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in out.iterdir() if x.is_file()},indent=2),encoding='utf8')
    print(json.dumps({'binaries':len(rows)}))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('source',type=Path);a.add_argument('out',type=Path);v=a.parse_args();main(v.source,v.out)
