import argparse,json,platform,shutil,subprocess,time
from pathlib import Path
import prototype as p
import recover
FIXTURES=[dict(name='wide',parameters=[2654435761,2246822519,7]),dict(name='small',parameters=[17,257,13]),dict(name='edge',parameters=[4294967295,2147483649,31])]
def run(output):
    out=Path(output).resolve();out.mkdir(parents=True,exist_ok=False);rows=[];attacks=[];transforms=[]
    try:
        for fixture in FIXTURES:
            name=fixture['name'];src=out/(name+'.plain.raw.wasm');p.compile(p.source_text(*fixture['parameters']),src)
            for mode in ('plain','fixed','dynamic','bad'):
                raw=out/(name+'.'+mode+'.raw.wasm')
                if mode!='plain':transforms.append(dict(name=name,**p.transform(src,raw,mode)))
                for opt in ('raw','O3'):
                    dst=raw if opt=='raw' else out/(name+'.'+mode+'.O3.wasm')
                    if opt=='O3':p.tool('wasm-opt',[raw,'-O3','-o',dst])
                    mod=p.read(dst);fs=[f for f in mod[1:] if f[0]=='func']
                    rows.append(dict(name=name,mode=mode,opt=opt,file=dst.name,negative=mode=='bad',bytes=dst.stat().st_size,sha256=p.digest(dst),linear_memory_bytes=0,
                        function_parameters=[len([t for x in f[1:] if x[0]=='param' for t in x[1:]]) for f in fs],
                        call_instructions=sum(x[0]=='call' for x in p.walk(mod))))
                    recovered=out/(name+'.'+mode+'.'+opt+'.recovered.wasm')
                    try:stats=recover.recover(dst,recovered)
                    except p.Unsupported as e:
                        attacks.append(dict(name=name,mode=mode,opt=opt,status='unsupported',reason=str(e)))
                        if mode!='bad':raise
                    else:
                        if mode=='bad':raise AssertionError('bad determinant accepted')
                        attacks.append(dict(name=name,mode=mode,opt=opt,status='recovered',**stats))
                        rows.append(dict(name=name,mode=mode+'-recovered',opt=opt,file=recovered.name,negative=False,bytes=recovered.stat().st_size,sha256=p.digest(recovered),linear_memory_bytes=0))
        p.save(out/'manifest.json',dict(fixtures=FIXTURES,binaries=rows,transforms=transforms,environment=dict(python=platform.python_version(),platform=platform.platform(),wabt=p.tool('wat2wasm',['--version']).decode().strip(),binaryen=p.tool('wasm-opt',['--version']).decode().strip())))
        p.save(out/'recovery.json',attacks)
        r=subprocess.run(['node',str(Path(__file__).with_name('check.cjs')),str(out)],capture_output=True,text=True,timeout=120)
        p.save(out/'node-command.json',dict(command=['node','check.cjs',str(out)],returncode=r.returncode,stdout=r.stdout,stderr=r.stderr))
        if r.returncode:raise RuntimeError(r.stderr+r.stdout)
        for name in ('prototype.py','recover.py','run.py','check.cjs'):shutil.copy2(Path(__file__).with_name(name),out/('source-'+name))
        print(r.stdout)
    finally:
        p.save(out/'commands.json',p.LOG)
        p.save(out/'pins.json',{str(f.relative_to(out)):p.digest(f) for f in out.rglob('*') if f.is_file() and f.name!='pins.json'})
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output');a=ap.parse_args();run(a.output)
