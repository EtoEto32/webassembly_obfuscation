"""White-box instrumentation; recovery receives no encoding generation metadata."""
import json,subprocess,sys
from pathlib import Path
import prototype as p
src,out=map(Path,sys.argv[1:]);out.mkdir(parents=True,exist_ok=False);q=p.q;targets=[]
for row in json.loads((src/'manifest.json').read_text()):
    m=q.read(src/row['file']);m.append(['export','"memory"',['memory','0']])
    f=out/row['file'];q.compile(q.w.emit(m),f)
    targets.append(dict(file=f.name,sha256=q.digest(f)))
q.save(out/'targets.json',targets)
subprocess.run(['node',str(Path(__file__).with_name('recover.cjs')),str(out)],check=True,timeout=90)
