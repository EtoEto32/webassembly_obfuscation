"""Replay validation expectations from pinned official WAST; never execute modules."""
import argparse,json,shutil
from collections import Counter
from pathlib import Path
from experiment import ROOT,HERE,CHECKER,WABT,command,digest

def main(source,out):
    out.mkdir(parents=True,exist_ok=False);commands=[];cases=[];conversion=[]
    for wat in sorted(source.glob('*.wast')):
        dest=out/(wat.stem+'.json')
        c=command([WABT.parent/'wast2json.exe',wat,'--no-check','--enable-all','-o',dest]);commands.append(c)
        if c['code']!=0:conversion.append(dict(file=wat.name,status='conversion_failed'));continue
        conversion.append(dict(file=wat.name,status='converted'))
        for row in json.loads(dest.read_text())['commands']:
            if row['type'] not in ['module','assert_invalid','assert_malformed','assert_unlinkable','assert_uninstantiable']:continue
            if not row.get('filename','').endswith('.wasm'):continue
            p=out/row['filename']
            cases.append(dict(source=wat.name,line=row['line'],assertion=row['type'],expected=row['type'] in ['module','assert_unlinkable','assert_uninstantiable'],path=str(p.resolve()),sha256=digest(p)))
    files=[r['path'] for r in cases];paths=out/'paths.json';paths.write_text(json.dumps(files))
    c=command(['node',HERE/'independent.mjs',paths]);commands.append(c);assert c['code']==0,c
    node={r['path']:r['valid'] for r in json.loads(c['stdout'])['rows']};actual={}
    for i in range(0,len(files),25):
        c=command([CHECKER,'check',*files[i:i+25]]);commands.append(c);assert c['code']==0,c
        for line in c['stdout'].splitlines():r=json.loads(line);actual[r['path']]=r
    errors=[];counts=Counter();outside=[]
    for row in cases:
        r=actual[row['path']];row['checker']=r;row['node']=node[row['path']]
        status=r['segment']['status'];counts[status]+=1
        if status in ['unsupported','resource_limit']:
            outside.append(dict(source=row['source'],line=row['line'],status=status,reason=r['segment']['message']));continue
        for mode in ['flat','cached','segment','stock','stock-current']:
            if (r[mode]['status']=='valid')!=row['expected']:errors.append(dict(path=row['path'],mode=mode,expected=row['expected'],actual=r[mode]))
        if row['node']!=row['expected']:errors.append(dict(path=row['path'],mode='node',expected=row['expected'],actual=row['node']))
    summary=dict(cases=len(cases),counts=dict(counts),errors=errors,conversion=conversion,
        supported_expected_valid=sum(r['expected'] and r['checker']['segment']['status'] in ['valid','invalid'] for r in cases),
        unsupported_expected_valid=sum(r['expected'] and r['checker']['segment']['status']=='unsupported' for r in cases))
    (out/'summary.json').write_text(json.dumps(summary,indent=2));(out/'rows.json').write_text(json.dumps(cases,indent=2))
    (out/'outside.json').write_text(json.dumps(outside,indent=2));(out/'commands.json').write_text(json.dumps(commands,indent=2))
    snapshots=out/'source';snapshots.mkdir()
    for p in [HERE/'spec-check.py',HERE/'independent.mjs',HERE/'checker/src/main.rs',HERE/'checker/Cargo.toml',HERE/'checker/Cargo.lock',CHECKER]:shutil.copyfile(p,snapshots/p.name)
    records=[dict(path=str(p.resolve()),sha256=digest(p)) for p in list(snapshots.iterdir())+list(source.glob('*.wast'))]
    records += [dict(path=r['path'],sha256=r['sha256']) for r in cases]
    (out/'manifest.json').write_text(json.dumps(records,indent=2));print(json.dumps(summary,indent=2));assert not errors
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('out',type=Path);args=ap.parse_args();main(args.source,args.out)
