import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time
import transform as t

HERE=Path(__file__).resolve().parent


def main(out):
    out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
    for n in ('compiler.py','compiler.cjs','compiler.rs','compiler-plan.md','transform.py'):
        shutil.copy2(HERE/n,out/'sources'/n)
    tc=json.loads((t.ROOT/'.tools/masters-security-rust/toolchain.json').read_text());logs=[];records=[]
    def run(cmd):
        start=time.perf_counter();r=subprocess.run(list(map(str,cmd)),capture_output=True,text=True,timeout=60)
        logs.append({'command':list(map(str,cmd)),'returncode':r.returncode,'seconds':time.perf_counter()-start,'stdout':r.stdout,'stderr':r.stderr})
        (out/'commands.json').write_text(json.dumps(logs,indent=2),encoding='utf8')
        if r.returncode:raise RuntimeError(r.stderr)
    try:
        for case in ('swap','stages','classify'):
            for opt in ('0','2','s'):
                stem=case+'-'+opt;obj=out/(stem+'.o');raw=out/(stem+'.wasm');post=out/(stem+'-O3.wasm')
                run(['rustc',HERE/'compiler.rs','--edition=2021','--crate-type=lib','--crate-name=frontier_probe','--emit=obj','--target=wasm32-unknown-unknown','--sysroot',tc['sysroot'],'-C','panic=abort','-C','opt-level='+opt,'--cfg','case="'+case+'"','-o',obj])
                run([tc['linker'],'-flavor','wasm','--no-entry','--export=run','--allow-undefined','--strip-all',obj,'-o',raw])
                t.w.tool('wasm-opt',[raw,'-O3','--remove-unused-module-elements','--enable-sign-ext','-o',post])
                for src in (raw,post):
                    t.w.tool('wasm-validate',[src]);wat=t.w.tool('wasm2wat',[src,'--fold-exprs']);src.with_suffix('.wat').write_text(wat,encoding='utf8')
                    row={'case':case,'opt':opt,'binary':src.name,'bytes':src.stat().st_size}
                    try:
                        rep=t.transform(src,out/(src.stem+'-frontier.wasm'),'frontier');row.update(status='accepted',summary=rep['summary'])
                    except ValueError as exc:row.update(status='unsupported',reason=str(exc))
                    records.append(row)
        manifest={'toolchain':tc,'records':records}
        (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
        run(['node',HERE/'compiler.cjs',out])
        print(json.dumps({'accepted':sum(x['status']=='accepted' for x in records),'total':len(records),'reasons':sorted({x.get('reason','accepted') for x in records})}))
    finally:
        (out/'sha256.json').write_text(json.dumps({str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file() and p.name!='sha256.json'},indent=2),encoding='utf8')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);main(ap.parse_args().output.resolve())
