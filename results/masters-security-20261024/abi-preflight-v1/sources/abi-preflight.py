"""Build a bounded Component fixture and guard its generated import trampoline."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import fence
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(out):
 out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
 for name in ('abi-preflight.py','abi-preflight.cjs','abi-preflight.wat','abi-preflight-test.cjs','abi-preflight-plan.md'):
  shutil.copy2(HERE/name,out/'sources'/name)
 commands=[]
 def run(*args):
  r=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=60)
  commands.append({'args':list(map(str,args)),'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
  (out/'commands.json').write_text(json.dumps(commands,indent=2),encoding='utf8');assert r.returncode==0,r.stderr
  return r.stdout
 try:
  run('node',fence.JCO,'parse',HERE/'abi-preflight.wat','-o',out/'unit.wasm')
  for mode in ('late','tree','memo'):
   dest=out/mode;dest.mkdir()
   run('node',fence.JCO,'transpile',out/'unit.wasm','-o',dest,'--name','unit','--instantiation','async','--base64-cutoff','0','--no-wasi-shim','--quiet')
   if mode!='late':
    file=dest/'unit.js';text=file.read_text(encoding='utf8');marker='const _trampoline0 = function(arg0, arg1) {'
    assert text.count(marker)==1,'expected fixed import trampoline not found'
    text="import preflight from './abi-preflight.cjs';\n"+text.replace(marker,marker+"\n    preflight.guard(memory0.buffer,arg0,arg1,imports.preflightConfig);")
    file.write_text(text,encoding='utf8');shutil.copy2(HERE/'abi-preflight.cjs',dest/'abi-preflight.cjs')
  print(run('node',HERE/'abi-preflight-test.cjs',out))
 finally:(out/'sha256.json').write_text(json.dumps({str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file() and p.name!='sha256.json'},indent=2),encoding='utf8')
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);main(ap.parse_args().output.resolve())
