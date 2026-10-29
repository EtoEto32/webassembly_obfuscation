import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path
import recover

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"artifacts/controls"
OUT.mkdir(exist_ok=False)
source=ROOT/"artifacts/mixed/input.wat"
tree=recover.parser.parse_wat(source.read_text())

def walk(n):
    if isinstance(n,list):
        yield n
        for x in n:
            yield from walk(x)

records=[]
for label,expected in [("shift2","carry recurrence"),("one_sweep","insufficient settling bound"),("self_dependency","cyclic recovered graph")]:
    variant=copy.deepcopy(tree)
    if label=="shift2":
        next(n for n in walk(variant) if n and n[0]=="i32.shl")[2]=recover.c(2)
    elif label=="one_sweep":
        variant[2][-2][-1][2][2]=recover.c(1)
    else:
        s=next(n for n in walk(variant) if len(n)==3 and n[0]=="local.set" and isinstance(n[2],list) and n[2][0]=="i32.mul")
        s[2][1]=recover.g(s[1])
    wat=OUT/(label+".wat");binary=OUT/(label+".wasm")
    wat.write_text(recover.serialize(variant)+"\n")
    subprocess.run([str(recover.TOOLS/"wat2wasm.exe"),str(wat),"-o",str(binary)],check=True,capture_output=True,timeout=60)
    subprocess.run([str(recover.TOOLS/"wasm-validate.exe"),str(binary)],check=True,capture_output=True,timeout=60)
    p=subprocess.run([sys.executable,str(ROOT/"recover.py"),str(binary),str(OUT/(label+"-attempt"))],capture_output=True,text=True,timeout=60)
    (OUT/(label+".stderr.txt")).write_text(p.stderr)
    assert p.returncode!=0 and "ValueError: "+expected in p.stderr
    records.append({"name":label,"sha256":hashlib.sha256(binary.read_bytes()).hexdigest(),"returncode":p.returncode,"reason":expected})
(OUT/"results.json").write_text(json.dumps(records,indent=2)+"\n")
print(json.dumps(records,indent=2))
