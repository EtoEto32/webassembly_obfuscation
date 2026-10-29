"""Reanalyze frozen binaries without recompiling or replacing previous results."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import time
import effects

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('boundary',HERE/'boundary.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)

def main(source,out):
    out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
    for name in ('effects.py','reanalyze.py','compiler.cjs'):
        shutil.copy2(HERE/name,out/'sources'/name)
    entries=json.loads((source/'manifest.json').read_text());old=json.loads((source/'results.json').read_text())
    for e in entries:
        binary=source/e['file'];assert b.p.digest(binary)==e['sha256']
        shutil.copy2(binary,out/binary.name)
        folded=b.p.w.tool('wasm2wat',[binary,'--fold-exprs'])
        (out/binary.with_suffix('.wat').name).write_text(folded,encoding='utf8')
        e['previousSummary']=e['summary']
        start=time.perf_counter();e['summary']=effects.summary(b.p.w.parse(folded));e['analysis_ms']=(time.perf_counter()-start)*1000
    (out/'manifest.json').write_text(json.dumps(entries,indent=2),encoding='utf8')
    (out/'source.json').write_text(json.dumps({'source':str(source),'sourceManifestSha256':b.p.digest(source/'manifest.json'),'sourceResultsSha256':b.p.digest(source/'results.json')},indent=2),encoding='utf8')
    r=subprocess.run(['node',str(HERE/'compiler.cjs'),str(out)],capture_output=True,text=True,timeout=120)
    (out/'stdout.txt').write_text(r.stdout,encoding='utf8');(out/'stderr.txt').write_text(r.stderr,encoding='utf8')
    if r.returncode: raise RuntimeError(r.stderr)
    new=json.loads((out/'results.json').read_text())
    for a,z in zip(old['entries'],new['entries']):
        assert a['file']==z['file']
        assert [r['args'] for r in a['rows']]==[r['args'] for r in z['rows']]
        assert a['changedBytes']==z['changedBytes']
    (out/'sha256.json').write_text(json.dumps({str(p.relative_to(out)):b.p.digest(p) for p in out.rglob('*') if p.is_file()},indent=2),encoding='utf8')
    print(r.stdout)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('output',type=Path)
    args=ap.parse_args();main(args.source.resolve(),args.output.resolve())
