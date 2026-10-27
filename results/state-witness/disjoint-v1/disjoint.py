"""Freeze the classifier and test native lifetime differences on disjoint modules."""
import argparse,hashlib,importlib.util,json,shutil,subprocess
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('context_analysis',HERE/'context-analysis.py');ca=importlib.util.module_from_spec(spec);spec.loader.exec_module(ca)

def main(source,cut,out):
    out.mkdir(parents=True,exist_ok=False);rows=[];manifest=json.loads((source/'manifest.json').read_text())
    used={x['source'] for x in json.loads((cut/'manifest.json').read_text())['cases']}
    for r in manifest['rows']:
        if r['status']!='accepted' or r['source'] in used:continue
        live=[s for s in r['manifest']['segments'] if s['initialLive']]
        if not live:continue
        original=k.p.read(source/r['source']);extended,meta=k.augment(original,False)
        if any(json.loads(e[1]).startswith('__ctx_') for e in k.p.section(original,'export')):raise ValueError('reserved export')
        for seg in live:extended.append(k.p.expr(f'(func (export "__ctx_drop_{seg["kind"]}_{seg["index"]}") ({seg["kind"]}.drop {seg["index"]}))'))
        filename=f'module-{len(rows):02}.wasm';k.p.compile_wat(k.p.w.emit(extended),out/filename)
        rows.append({'source':r['source'],'sourceSha256':hashlib.sha256((source/r['source']).read_bytes()).hexdigest(),'file':filename,'observer':meta,
          'segments':[{'segment':s,'certificate':ca.certify(original,[(s['kind'],s['index'])])} for s in live],
          'commands':r['commands']})
    for name in ['disjoint.py','disjoint.mjs','context-analysis.py','prototype.py','observer.cjs']:shutil.copy2(HERE/name,out/name)
    (out/'manifest.json').write_text(json.dumps({'cases':rows,'excludedSources':sorted(used),
      'classifierSha256':hashlib.sha256((HERE/'context-analysis.py').read_bytes()).hexdigest()},indent=2))
    r=subprocess.run(['node',str(HERE/'disjoint.mjs'),str(out.resolve())],capture_output=True,text=True,timeout=60)
    (out/'node-log.json').write_text(json.dumps({'code':r.returncode,'stdout':r.stdout,'stderr':r.stderr},indent=2))
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()},indent=2))
    assert r.returncode==0,r.stderr;print(r.stdout)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('cut',type=Path);p.add_argument('out',type=Path)
    v=p.parse_args();main(v.source,v.cut,v.out)
