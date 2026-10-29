import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time
import compensate as c
import prototype as p

HERE=Path(__file__).resolve().parent;z=p.z

def symbolic(row):
    # Independent byte expression: signed saturation and lane selection, no
    # calls to the generator's coefficient extractor or matrix multiplication.
    x=z.BitVec('check_index',8);table=[z.BitVec('check_t'+str(i),8) for i in range(16)];proofs=[]
    for profile in (0,1):
        encoded=[]
        for bits in row['certificate']['profiles'][profile]['E']:
            value=z.BitVecVal(0,8)
            for j in range(16):
                if (bits>>j)&1:value=value^table[j]
            encoded.append(value)
        idx=x;result=z.BitVecVal(0,8)
        for site in range(16):
            if site:
                if site<=8:idx=idx-z.BitVecVal(16,8)
                else:
                    extended=z.SignExt(1,idx)-z.BitVecVal(16,9)
                    idx=z.Extract(7,0,z.If(extended<z.BitVecVal(-128,9),z.BitVecVal(-128,9),extended))
            selected=z.ULT(idx,16)
            if profile and not (row['mask']>>site)&1:selected=z.Or(selected,z.ULT(idx,128))
            result=result^z.If(selected,encoded[site],z.BitVecVal(0,8))
        target=table[0]
        for j in range(1,16):target=z.If(z.Extract(7,4,x)==j,table[j],target)
        solver=z.Solver();solver.set(timeout=15000);solver.add(result!=target);start=time.perf_counter();status=solver.check()
        if status!=z.unsat:raise RuntimeError(str(status)+' '+row['mode'])
        proofs.append({'profile':profile,'status':str(status),'seconds':time.perf_counter()-start})
    return proofs

def main(source,out):
    out.mkdir(parents=True,exist_ok=False);rows=json.loads((source/'results.json').read_text(encoding='utf8'))['rows']
    for name in ('compensation-audit.py','compensation-test.cjs'):shutil.copy2(HERE/name,out/name)
    try:
        proofs=[{'mode':r['mode'],'proofs':symbolic(r)} for r in rows if r['kind'] not in ('scalar','dispatch')]
        cmd=['node',str(HERE/'compensation-test.cjs'),str(source/'results.json')];run=subprocess.run(cmd,capture_output=True,text=True,timeout=120)
        (out/'raw.json').write_text(json.dumps({'command':cmd,'returncode':run.returncode,'stdout':run.stdout,'stderr':run.stderr},indent=2),encoding='utf8')
        if run.returncode:raise RuntimeError(run.stderr)
        result={'symbolic':proofs,'concrete':json.loads(run.stdout),'sourceManifestSHA256':hashlib.sha256((source/'sha256.json').read_bytes()).hexdigest(),
            'limitations':'Lane expression proof plus actual binary tests, not a verified compiler. Constant address trace is at Wasm level only. The same semantic cases appear under explicit profiles and native, not separate applications.'}
        (out/'results.json').write_text(json.dumps(result,indent=2),encoding='utf8')
        print(json.dumps({'unsat':sum(len(v['proofs']) for v in proofs),**{k:v for k,v in result['concrete'].items() if k not in ('rows','traces')}}))
    finally:(out/'sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir() if f.is_file() and f.name!='sha256.json'},indent=2),encoding='utf8')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();main(a.source.resolve(),a.output.resolve())
