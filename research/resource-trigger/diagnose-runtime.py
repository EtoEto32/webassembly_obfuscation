import argparse,subprocess
from pathlib import Path
import prototype as p
a=argparse.ArgumentParser();a.add_argument('output');v=a.parse_args();out=Path(v.output);out.mkdir(parents=True,exist_ok=False)
source=Path(__file__).with_name('probe.wat');p.jco('parse',source,'-o',out/'probe.wasm');p.transpile(out/'probe.wasm',out/'js')
r=subprocess.run(['node',str(Path(__file__).with_name('runtime-probe.cjs')),str(out)],capture_output=True,text=True,timeout=60);(out/'probe.log').write_text(r.stdout+r.stderr,encoding='utf-8');p.q.save(out/'provenance.json',dict(source_sha256=p.q.digest(source),component_sha256=p.q.digest(out/'probe.wasm'),jco='1.27.0'))
print(r.stdout,r.stderr)
if r.returncode:raise RuntimeError('probe runtime failure')
