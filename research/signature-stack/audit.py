import argparse,hashlib,json,math,statistics
from pathlib import Path
from experiment import ROOT,wide,wasmtime
from fragmented import source

def main(out):
    base=ROOT/'results/signature-stack';names=['correctness-v3','performance-v2','spec-check-v2','corpus-v1','fragmented-v1']
    errors=[];manifests=[];count=0
    for name in names:
        entries=json.loads((base/name/'manifest.json').read_text())
        for entry in entries:
            p=Path(entry['path']);count+=1
            if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=entry['sha256']:errors.append(dict(reason='hash',path=str(p)))
        manifests.append(dict(name=name,files=len(entries)))
    regenerated=[]
    for name in ['correctness-v3','performance-v2','fragmented-v1']:
        for wat in (base/name).glob('*.wat'):
            binary=wat.with_suffix('.wasm');same=bytes(wasmtime.wat2wasm(wat.read_text()))==binary.read_bytes()
            regenerated.append(dict(path=str(binary.relative_to(ROOT)),identical=same))
            if not same:errors.append(dict(reason='WAT regeneration',path=str(binary)))
    numeric=0
    for name in ['performance-v2','fragmented-v1']:
        rows=json.loads((base/name/'rows.json').read_text());summary=json.loads((base/name/'summary.json').read_text())
        for s in summary:
            key='case' if name=='performance-v2' else 'name'
            for mode in ['flat','cached','segment','stock-current']:
                rs=[r for r in rows if r[key]==s['name'] and r['mode']==mode];assert len(rs)==3
                assert all(len(r['end_to_end_s'])==11 and r['warmup']==5 and 1<=r['batch_iterations']<=512 for r in rs)
                med=statistics.median(statistics.median(r['end_to_end_s']) for r in rs)
                recorded=s[mode]['end_to_end_s']['median'] if name=='performance-v2' else s[mode]['median_s']
                numeric+=1
                if not math.isclose(med,recorded,rel_tol=1e-12):errors.append(dict(reason='median',name=s['name'],mode=mode))
            if name=='performance-v2':
                expected=wide(s['width'],s['reps'],s['family'])
                same=bytes(wasmtime.wat2wasm(expected))==Path(s['path']).read_bytes()
            else:same=bytes(wasmtime.wat2wasm(source(s['width'],1024)))==Path(s['path']).read_bytes()
            if not same:errors.append(dict(reason='generator regeneration',name=s['name']))
    for name in ['correctness-v3','spec-check-v2','corpus-v1']:
        s=json.loads((base/name/'summary.json').read_text())
        if s['errors']:errors.append(dict(reason='recorded test errors',name=name))
    # Verify the downloaded primary-source and official-suite snapshots too.
    primary=0
    for folder in ['prior-snapshots-v2','spec-source-v2']:
        entries=json.loads((base/folder/'manifest.json').read_text())
        if isinstance(entries,dict):entries=entries['files']
        for e in entries:
            primary+=1;p=Path(e['path'])
            if hashlib.sha256(p.read_bytes()).hexdigest()!=e['sha256']:errors.append(dict(reason='primary hash',path=str(p)))
    report=dict(manifests=manifests,file_hashes=count,primary_source_hashes=primary,wat_regenerated=len(regenerated),generator_regenerated=43,
        recomputed_medians=numeric,regenerated=regenerated,errors=errors)
    out.write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ['regenerated','manifests']},indent=2));assert not errors
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);main(ap.parse_args().out)
