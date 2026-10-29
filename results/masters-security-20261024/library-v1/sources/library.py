"""Assess candidate B on unmodified hash-wasm bodies plus a thin entry wrapper."""
import argparse
import base64
import copy
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import time
import effects

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('boundary',HERE/'boundary.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
LIB=ROOT/'.tools/masters-security-hash-wasm-4.12.0'
ALGORITHMS=('adler32','crc32','md5','sha1','sha256','sha512','xxhash32','xxhash64')
def main(out):
    out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
    for name in ('library.py','library.cjs','library-plan.md','effects.py','setup-hash-library.py'):
        shutil.copy2(HERE/name,out/'sources'/name)
    shutil.copy2(LIB/'provenance.json',out/'package-provenance.json')
    shutil.copy2(LIB/'package/LICENSE',out/'THIRD-PARTY-LICENSE')
    rows=[];extracts=[]
    for algorithm in ALGORITHMS:
        bundle=LIB/'package/dist'/(algorithm+'.umd.min.js')
        matches=re.findall(r'data:"(AGFzb[A-Za-z0-9+/=]+)"',bundle.read_text())
        assert len(matches)==1,algorithm
        binary=out/(algorithm+'-original.wasm');binary.write_bytes(base64.b64decode(matches[0],validate=True))
        b.p.w.tool('wasm-validate',[binary]);mod=b.p.w.parse(b.p.w.tool('wasm2wat',[binary,'--fold-exprs']))
        imports=[x for x in mod[1:] if x[0]=='import'];assert not imports,'unexpected library imports'
        funcs=[x for x in mod[1:] if x[0]=='func'];exports={x[1]:x[2] for x in mod[1:] if x[0]=='export'}
        extracts.append({'algorithm':algorithm,'packageBundle':str(bundle.relative_to(ROOT)),
                         'bundleSha256':b.p.digest(bundle),'originalSha256':b.p.digest(binary),'bytes':binary.stat().st_size})
        for operation in ('Hash_Init','Hash_Update','Hash_Final'):
            idx=int(exports['"'+operation+'"'][1]);f=funcs[idx]
            params=[p for x in f[1:] if x[0]=='param' for p in x[1:]]
            if any(p!='i32' for p in params) or len(params)>3 or any(x[0]=='result' for x in f[1:]):
                rows.append({'algorithm':algorithm,'operation':operation,'status':'unsupported-signature','params':params});continue
            wrapped=copy.deepcopy(mod);wrapped.append(['func',['param','i32','i32','i32'],['call',str(idx),*([['local.get',str(i)] for i in range(len(params))])]])
            wrapped.append(['export','"callback"',['func',str(len(funcs))]])
            raw=out/(algorithm+'-'+operation+'-raw.wasm');wat=raw.with_suffix('.wat');wat.write_text(b.p.w.emit(wrapped),encoding='utf8')
            b.p.w.tool('wat2wasm',[wat,'-o',raw]);post=raw.with_name(raw.stem.replace('-raw','-O3')+'.wasm')
            b.p.w.tool('wasm-opt',[raw,'-O3','--enable-bulk-memory','--enable-sign-ext','--enable-mutable-globals','-o',post])
            for file in (raw,post):
                b.p.w.tool('wasm-validate',[file]);normalized=b.p.w.parse(b.p.w.tool('wasm2wat',[file,'--fold-exprs']))
                if file==raw:assert [x for x in normalized[1:] if x[0]=='func'][:-1]==funcs
                start=time.perf_counter();summary=effects.summary(normalized);ms=(time.perf_counter()-start)*1000
                rows.append({'algorithm':algorithm,'operation':operation,'status':'built','file':file.name,
                  'original':binary.name,'params':len(params),'optimized':file==post,'sha256':b.p.digest(file),
                  'bytes':file.stat().st_size,'summary':summary,'analysis_ms':ms})
    (out/'extraction.json').write_text(json.dumps(extracts,indent=2),encoding='utf8')
    (out/'manifest.json').write_text(json.dumps(rows,indent=2),encoding='utf8')
    r=subprocess.run(['node',str(HERE/'library.cjs'),str(out)],capture_output=True,text=True,timeout=120)
    (out/'stdout.txt').write_text(r.stdout,encoding='utf8');(out/'stderr.txt').write_text(r.stderr,encoding='utf8')
    (out/'sha256.json').write_text(json.dumps({str(p.relative_to(out)):b.p.digest(p) for p in out.rglob('*') if p.is_file()},indent=2),encoding='utf8')
    if r.returncode:raise RuntimeError(r.stderr)
    print(r.stdout)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);main(ap.parse_args().output.resolve())
