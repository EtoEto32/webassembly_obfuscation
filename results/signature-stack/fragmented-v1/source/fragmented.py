"""Counterexample to a blanket O(binary bytes) resource-bound claim."""
import argparse,json,random,shutil,statistics
from pathlib import Path
from experiment import HERE,CHECKER,command,digest,wasmtime,TYPES,const

def source(width,reps):
    ts=[TYPES[i%4] for i in range(width)];a=ts[:width//2];b=ts[width//2:]
    return '(module '+f'(func $a (result {" ".join(a)}) {" ".join(map(const,a))}) '+f'(func $b (result {" ".join(b)}) {" ".join(map(const,b))}) '+f'(func $sink (param {" ".join(ts)})) '+ '(func (export "run") '+ 'call $a call $b call $sink '*reps+'))'
def main(out):
    out.mkdir(parents=True,exist_ok=False);cases=[];commands=[]
    for width in [8,64,512]:
        name=f'split-w{width}-r1024';path=out/(name+'.wasm');wat=out/(name+'.wat')
        wat.write_text(source(width,1024));path.write_bytes(wasmtime.wat2wasm(wat.read_text()))
        c=command([CHECKER,'check',path]);commands.append(c);checked=json.loads(c['stdout'])
        assert all(checked[m]['status']=='valid' for m in ['flat','cached','segment','stock-current'])
        cases.append(dict(name=name,path=str(path.resolve()),width=width,checks=checked,sha256=digest(path)))
    jobs=[(case,mode,trial) for case in cases for mode in ['flat','cached','segment','stock-current'] for trial in range(3)]
    random.Random(261026).shuffle(jobs);rows=[]
    for case,mode,trial in jobs:
        c=command([CHECKER,'bench',case['path'],mode,'11']);commands.append(c);assert c['code']==0,c
        row=json.loads(c['stdout']);row.update(name=case['name'],trial=trial);rows.append(row)
    summary=[]
    for case in cases:
        r=dict(case)
        for mode in ['flat','cached','segment','stock-current']:
            rs=[x for x in rows if x['name']==case['name'] and x['mode']==mode]
            medians=[statistics.median(x['end_to_end_s']) for x in rs]
            r[mode]=dict(median_s=statistics.median(medians),process_medians_s=medians,stats=rs[0]['stats'])
        summary.append(r)
    (out/'summary.json').write_text(json.dumps(summary,indent=2));(out/'rows.json').write_text(json.dumps(rows,indent=2));(out/'commands.json').write_text(json.dumps(commands,indent=2))
    snapshots=out/'source';snapshots.mkdir()
    for p in [HERE/'fragmented.py',HERE/'experiment.py',HERE/'checker/src/main.rs',HERE/'checker/Cargo.toml',HERE/'checker/Cargo.lock',CHECKER]:shutil.copyfile(p,snapshots/p.name)
    records=[dict(path=str(p.resolve()),sha256=digest(p)) for p in list(snapshots.iterdir())]+[dict(path=c['path'],sha256=c['sha256']) for c in cases]
    (out/'manifest.json').write_text(json.dumps(records,indent=2));print(json.dumps([dict(name=r['name'],segment_over_flat=r['segment']['median_s']/r['flat']['median_s'],segment_over_cached=r['segment']['median_s']/r['cached']['median_s'],stats=r['segment']['stats']) for r in summary],indent=2))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);main(ap.parse_args().out)
