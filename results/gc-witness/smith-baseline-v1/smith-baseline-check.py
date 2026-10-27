"""Compare feature-off patched smith with the untouched upstream crate."""
import argparse,json,shutil,subprocess
from pathlib import Path
from experiment import ROOT,HERE,dump,digest

def main(source,out):
    out.mkdir(parents=True,exist_ok=False);rows=[];errors=[]
    pristine=ROOT/'.tools/gc-witness-smith-target/release/gc-witness-smith-pristine.exe'
    for old in json.loads((source/'rows.json').read_text()):
        if old['mode']!='stock':continue
        name,seed=old['name'],old['seed'];dest=out/('%s-%s.wasm'%(name,seed))
        p=subprocess.run([str(pristine),str(source/(name+'-shape.wasm')),str(source/(name+'-%s.seed'%seed)),str(dest)],capture_output=True,text=True,timeout=15)
        row=dict(name=name,seed=seed,code=p.returncode,stderr=p.stderr)
        try:g=json.loads(p.stdout)
        except ValueError:g=dict(status='process-error',stdout=p.stdout)
        row['generation']=g
        og=old.get('generation',{})
        if g.get('status')=='generated' and og.get('status')=='generated':
            row['identical']=dest.read_bytes()==(source/('%s-%s-stock.wasm'%(name,seed))).read_bytes()
        else:row['identical']=p.returncode==old['generation_process']['code'] and g.get('status')==og.get('status') and g.get('reason')==og.get('reason')
        if not row['identical']:errors.append(dict(name=name,seed=seed))
        rows.append(row)
    zero_pairs=[]
    for old in json.loads((source/'rows.json').read_text()):
        if old['mode']=='stock' and old['name']=='cycle-struct' and old.get('generation',{}).get('status')=='generated':
            stem='cycle-struct-%s-'%old['seed'];same=(source/(stem+'stock.wasm')).read_bytes()==(source/(stem+'zero.wasm')).read_bytes()
            zero_pairs.append(same)
            if not same:errors.append(dict(kind='negative-control',seed=old['seed']))
    dump(out/'rows.json',rows);dump(out/'summary.json',dict(compared=len(rows),generated=sum(r['generation'].get('status')=='generated' for r in rows),identical=sum(r['identical'] for r in rows),negative_control_pairs=len(zero_pairs),negative_control_identical=sum(zero_pairs),errors=errors))
    for src in [Path(__file__),pristine,HERE/'smith-pristine/Cargo.toml',HERE/'smith-pristine/Cargo.lock',HERE/'smith-driver/src/main.rs']:shutil.copy2(src,out/src.name)
    dump(out/'manifest.json',[dict(path=str(p.resolve()),sha256=digest(p)) for p in out.rglob('*') if p.is_file()]);print((out/'summary.json').read_text());assert not errors
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('out',type=Path);a=ap.parse_args();main(a.source,a.out)
