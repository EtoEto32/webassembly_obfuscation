"""Inventory locally cached public NoWAS dataset; no Wasm execution."""
import argparse,json,shutil
from collections import Counter
from pathlib import Path
from experiment import ROOT,HERE,CHECKER,command,digest

def main(out):
    out.mkdir(parents=True,exist_ok=False);source=ROOT/'.tools/nowaset-53118203';prov=source/'provenance.json'
    files=json.loads(prov.read_text())['files'];commands=[];rows=[];errors=[]
    for f in files:
        path=source/f['file'];actual=digest(path);assert actual==f['sha256']
        c=command([CHECKER,'profile',path]);commands.append(c)
        if c['code']!=0:rows.append(dict(file=f,status='tool_failed',command=c));continue
        profile=json.loads(c['stdout'])['profile']
        c=command([CHECKER,'check',path]);commands.append(c)
        if c['code']!=0:rows.append(dict(file=f,status='tool_failed',command=c));continue
        checked=json.loads(c['stdout']);rows.append(dict(file=f,status=profile['status'],profile=profile,checker=checked))
        for mode in ['flat','cached','segment']:
            status=checked[mode]['status']
            if status in ['valid','invalid'] and status!=checked['stock']['status']:
                errors.append(dict(path=str(path),mode=mode,status=status,reference=checked['stock']['status']))
    valid=[r['profile']['data'] for r in rows if r['status']=='valid'];hist=Counter()
    for r in valid:hist.update({int(k):v for k,v in r['width_histogram'].items()})
    summary=dict(corpus_files=len(rows),profile_status=dict(Counter(r['status'] for r in rows)),
        kernel_status=dict(Counter(r['checker']['segment']['status'] for r in rows if 'checker' in r)),
        total_functions=sum(r['functions'] for r in valid),total_instructions=sum(r['instructions'] for r in valid),
        signature_uses=sum(hist.values()),signature_width_histogram=dict(sorted(hist.items())),
        modules_max_width_over_8=sum(r['max_explicit_signature_width']>8 for r in valid),
        modules_max_width_over_64=sum(r['max_explicit_signature_width']>64 for r in valid),
        multi_value_block_uses=sum(r['multi_value_block_uses'] for r in valid),errors=errors)
    (out/'summary.json').write_text(json.dumps(summary,indent=2));(out/'rows.json').write_text(json.dumps(rows,indent=2));(out/'commands.json').write_text(json.dumps(commands,indent=2))
    snapshots=out/'source';snapshots.mkdir()
    for p in [HERE/'corpus.py',HERE/'experiment.py',HERE/'checker/src/main.rs',HERE/'checker/Cargo.toml',HERE/'checker/Cargo.lock',CHECKER,prov]:shutil.copyfile(p,snapshots/p.name)
    records=[dict(path=str(p.resolve()),sha256=digest(p)) for p in list(snapshots.iterdir())+[source/r['file'] for r in files]]
    (out/'manifest.json').write_text(json.dumps(records,indent=2));print(json.dumps(summary,indent=2));assert not errors
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);main(ap.parse_args().out)
