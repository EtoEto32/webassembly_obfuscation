"""Verify structured rejection of malformed certificates at the CLI boundary."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(out):
    out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
    for name in ('checker-cli-audit.py','check-certificate.py','byte-checker.py'):
        shutil.copy2(HERE/name,out/'sources'/name)
    wasm=ROOT/'results/masters-security-20261024/compiler-v1/metadata-rust2.wasm'
    cert=json.loads((ROOT/'results/masters-security-20261024/compiler-v2/cli-acyclic.json').read_text())
    cases=[('valid',json.dumps(cert).encode(),True,wasm),('root-list',b'[]',False,wasm),('invalid-json',b'{',False,wasm),
        ('invalid-utf8',b'\xff',False,wasm),('duplicate-key',b'{"schema":1,"schema":2}',False,wasm),
        ('non-finite',b'{"analysis":NaN}',False,wasm),('oversize',b' '* (2*1024*1024+1),False,wasm),
        ('deep-json',b'['*1500+b']'*1500,False,wasm)]
    for name,key,value in [('analysis-list','analysis',[]),('analysis-null','analysis',None),('wrong-hash','wasm_sha256','0'*64),('wrong-entry','export','other')]:
        bad=copy.deepcopy(cert);bad[key]=value;cases.append((name,json.dumps(bad).encode(),False,wasm))
    invalid=out/'invalid.wasm';invalid.write_bytes(b'not a wasm binary');cases.append(('invalid-binary',json.dumps(cert).encode(),False,invalid))
    rows=[]
    for name,data,want,binary in cases:
        file=out/(name+'.certificate.json');file.write_bytes(data);target=out/(name+'.check.json')
        r=subprocess.run([sys.executable,str(HERE/'check-certificate.py'),str(binary),str(file),str(target)],capture_output=True,text=True,timeout=30)
        (out/(name+'.log')).write_text(r.stdout+r.stderr,encoding='utf8');assert r.returncode==(0 if want else 2),(name,r.stderr)
        result=json.loads(target.read_text());assert result['verdict']['accepted']==want
        rows.append({'name':name,'exit':r.returncode,'validation':result['standardBinaryValidation'],'verdict':result['verdict']})
    (out/'audit.json').write_text(json.dumps({'cases':len(rows),'accepted':1,'rejected':len(rows)-1,'rows':rows},indent=2),encoding='utf8')
    (out/'sha256.json').write_text(json.dumps({str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()},indent=2),encoding='utf8')
    print(json.dumps({'cases':len(rows),'accepted':1,'rejected':len(rows)-1}))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);main(ap.parse_args().output.resolve())
