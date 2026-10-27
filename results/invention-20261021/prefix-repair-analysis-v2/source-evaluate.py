import argparse,json,shutil,subprocess
from pathlib import Path
import prototype as p
import recover as r
from run import safe

def run(main,out):
    main=Path(main).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    manifest=json.loads((main/'manifest.json').read_text(encoding='utf-8'));rows=[];checks=[];seen=set()
    for t in manifest['targets']:
        dst=out/(Path(t['file']).stem+'.recovered.wasm')
        try:meta=r.recover(main/t['file'],dst)
        except ValueError as exc:
            rows.append(dict(file=t['file'],mode=t['mode'],status='rejected',reason=str(exc)))
            p.q.save(out/'analysis.json',rows)
            if t['mode']!='bad':raise
            continue
        if t['mode']=='bad':raise AssertionError('accepted invalid trap compensation')
        assert dst.read_bytes()==(main/(t['name']+'.source.wasm')).read_bytes()
        rows.append(dict(file=t['file'],mode=t['mode'],status='recovered',output=dst.name,meta=meta,byte_equals_source=True))
        p.q.save(out/'analysis.json',rows)
        if t['name'] not in seen:
            seen.add(t['name']);probe=out/(dst.stem+'.probe.wasm');p.probe(dst,probe)
            checks.append(dict(t,file=dst.name,probe=probe.name,mode='plain',meta=dict(t['meta'],matrix=p.m.ident(t['meta']['n']))))
    p.q.save(out/'analysis.json',rows);p.q.save(out/'manifest.json',safe(dict(targets=checks)))
    result=subprocess.run(['node',str(Path(__file__).with_name('check.cjs')),str(out)],capture_output=True,text=True,timeout=90)
    (out/'stdout.txt').write_text(result.stdout,encoding='utf-8');(out/'stderr.txt').write_text(result.stderr,encoding='utf-8')
    if result.returncode:raise RuntimeError(result.stderr)
    for f in ('prototype.py','recover.py','evaluate.py','check.cjs'):shutil.copy2(Path(__file__).with_name(f),out/('source-'+f))
    p.q.save(out/'pins.json',{str(f.relative_to(out)):p.q.digest(f) for f in out.rglob('*') if f.is_file()})
    print(json.dumps({'recovered':sum(x['status']=='recovered' for x in rows),'rejected_negative':sum(x['status']=='rejected' for x in rows),'unique_reexecution':len(checks)}))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('main');ap.add_argument('output');a=ap.parse_args();run(a.main,a.output)
