"""Compile all preregistered fixtures, analyze exact binaries, test snapshots."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
spec=importlib.util.spec_from_file_location('boundary', HERE/'boundary.py')
b=importlib.util.module_from_spec(spec); spec.loader.exec_module(b)

def main(out):
    out.mkdir(parents=True,exist_ok=False)
    (out/'sources').mkdir()
    for name in ('compiler.py','compiler.cjs','compiler-fixture.rs','compiler-plan.md','boundary.py','probe.py'):
        shutil.copy2(HERE/name,out/'sources'/name)
    tc=json.loads((ROOT/'.tools/masters-security-rust/toolchain.json').read_text())
    (out/'toolchain.json').write_text(json.dumps(tc,indent=2),encoding='utf8')
    manifest=[]; builds=[]
    for name in ('fixed','indexed','branch','metadata','loop','copy','fill','helper'):
        for opt in ('0','2','s'):
            raw=out/(name+'-rust'+opt+'.wasm')
            cmd=['rustc',str(HERE/'compiler-fixture.rs'),'--edition=2021','--crate-type=cdylib',
                 '--crate-name=coverage_fixture','--target=wasm32-unknown-unknown',
                 '--sysroot',tc['sysroot'],'-C','linker='+tc['linker'],'-C','panic=abort',
                 '-C','opt-level='+opt,'-C','debuginfo=0','-C','strip=symbols',
                 '--cfg','case="'+name+'"','-o',str(raw)]
            start=time.perf_counter();r=subprocess.run(cmd,capture_output=True,text=True,timeout=90)
            record={'fixture':name,'optimization':opt,'command':cmd,'seconds':time.perf_counter()-start,
                    'status':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
            builds.append(record)
            if r.returncode:
                (out/'builds.json').write_text(json.dumps(builds,indent=2),encoding='utf8')
                raise RuntimeError(r.stderr)
            post=raw.with_name(raw.stem+'-O3.wasm')
            b.p.w.tool('wasm-opt',[raw,'-O3','--enable-bulk-memory','--enable-sign-ext','--enable-mutable-globals','--enable-nontrapping-float-to-int','-o',post])
            for binary in (raw,post):
                b.p.w.tool('wasm-validate',[binary])
                folded=b.p.w.tool('wasm2wat',[binary,'--fold-exprs'])
                binary.with_suffix('.wat').write_text(folded,encoding='utf8')
                start=time.perf_counter();summary=b.summary(b.p.w.parse(folded));elapsed=time.perf_counter()-start
                manifest.append({'fixture':name,'rustOpt':opt,'binaryenO3':binary==post,'file':binary.name,
                                 'sha256':b.p.digest(binary),'bytes':binary.stat().st_size,
                                 'summary':summary,'analysis_ms':elapsed*1000})
    (out/'builds.json').write_text(json.dumps(builds,indent=2),encoding='utf8')
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    r=subprocess.run(['node',str(HERE/'compiler.cjs'),str(out)],capture_output=True,text=True,timeout=120)
    (out/'stdout.txt').write_text(r.stdout,encoding='utf8');(out/'stderr.txt').write_text(r.stderr,encoding='utf8')
    (out/'sha256.json').write_text(json.dumps({str(p.relative_to(out)):b.p.digest(p) for p in out.rglob('*') if p.is_file()},indent=2),encoding='utf8')
    if r.returncode: raise RuntimeError(r.stderr)
    print(r.stdout)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path)
    main(ap.parse_args().output.resolve())
