import argparse
import json
import random
import statistics
import shutil
from pathlib import Path
from experiment import ROOT,HERE,CHECKER,command,digest,wide,wasmtime

def main(out):
    out.mkdir(parents=True,exist_ok=False);cases=[];commands=[]
    modes=['stock-current','flat','cached','segment']
    for family in ['block','call','if','br-if','alternating']:
        for width in [1,8,64,512]:
            for reps in [64,1024]:
                name=f'{family}-w{width}-r{reps}';text=out/(name+'.wat');binary=out/(name+'.wasm')
                text.write_text(wide(width,reps,family));binary.write_bytes(wasmtime.wat2wasm(text.read_text()))
                cases.append(dict(name=name,path=str(binary.resolve()),width=width,reps=reps,family=family,bytes=binary.stat().st_size,sha256=digest(binary)))
    for case in cases:
        c=command([CHECKER,'check',case['path']]);commands.append(c);assert c['code']==0,c
        checked=json.loads(c['stdout']);assert all(checked[m]['status']=='valid' for m in modes),checked
    jobs=[(case,mode,trial) for case in cases for mode in modes for trial in range(3)]
    random.Random(261026).shuffle(jobs);rows=[]
    for case,mode,trial in jobs:
        c=command([CHECKER,'bench',case['path'],mode,'11']);commands.append(c)
        (out/'commands.json').write_text(json.dumps(commands,indent=2))
        assert c['code']==0,c
        row=json.loads(c['stdout']);row.update(case=case['name'],trial=trial)
        rows.append(row);(out/'rows.json').write_text(json.dumps(rows,indent=2))
    summary=[]
    for case in cases:
        record=dict(case)
        for mode in modes:
            subset=[r for r in rows if r['case']==case['name'] and r['mode']==mode]
            entry={}
            for metric in ['end_to_end_s','kernel_s','prepare_s']:
                medians=[statistics.median(r[metric]) for r in subset if r[metric]]
                if medians:entry[metric]=dict(median=statistics.median(medians),min=min(medians),max=max(medians),process_medians=medians)
            entry['stats']=subset[0]['stats'];entry['peak_process_bytes']=[r['peak_process_bytes'] for r in subset];record[mode]=entry
        record['segment_over_flat']=record['segment']['end_to_end_s']['median']/record['flat']['end_to_end_s']['median']
        record['segment_over_stock']=record['segment']['end_to_end_s']['median']/record['stock-current']['end_to_end_s']['median']
        record['segment_over_cached']=record['segment']['end_to_end_s']['median']/record['cached']['end_to_end_s']['median']
        summary.append(record)
    (out/'summary.json').write_text(json.dumps(summary,indent=2))
    sources=[HERE/'benchmark.py',HERE/'experiment.py',HERE/'checker/src/main.rs',HERE/'checker/Cargo.toml',HERE/'checker/Cargo.lock',CHECKER]
    snapshots=out/'source';snapshots.mkdir()
    for p in sources:shutil.copyfile(p,snapshots/p.name)
    sources=list(snapshots.iterdir())
    (out/'manifest.json').write_text(json.dumps([dict(path=str(p.resolve()),sha256=digest(p)) for p in sources]+[dict(path=c['path'],sha256=c['sha256']) for c in cases],indent=2))
    print(json.dumps(dict(processes=len(rows),cases=len(cases),wide=[{k:r[k] for k in ['name','segment_over_flat','segment_over_cached','segment_over_stock']} for r in summary if r['width']==512 and r['reps']==1024]),indent=2))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);main(ap.parse_args().out)
