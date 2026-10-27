"""Static applicability profile; does not instantiate downloaded applications."""
import argparse,collections,json,subprocess,shutil
from pathlib import Path
from realize import ROOT,HERE,read,Unsupported
from experiment import dump,digest
def main(corpus,out):
    out.mkdir(parents=True,exist_ok=False);rows=[];exe=ROOT/'.tools/gc-realization-target/release/gc-realization-inspector.exe'
    for entry in json.loads((corpus/'manifest.json').read_text()):
        file=corpus/entry['file'];assert digest(file)==entry['sha256'];p=subprocess.run([str(exe),str(file)],capture_output=True,text=True,timeout=30);p.check_returncode();m=json.loads(p.stdout);dump(out/(file.stem+'.json'),m)
        row=dict(file=entry['file'],sha256=entry['sha256'],bytes=entry['bytes'],inspection_status=m['status'])
        if m['status']=='inspected':
            ts=m['types'];gc=[t for t in ts if t['kind'] in ('struct','array')];fs=[f for t in gc for f in t['fields']];refs=[f for f in fs if f['value'].get('reference')]
            row.update(types=len(ts),gc_types=len(gc),kinds=dict(collections.Counter(t['kind'] for t in ts)),nonfinal_gc=sum(not t['final'] for t in gc),subtype_gc=sum(bool(t['supertypes']) for t in gc),fields=len(fs),reference_fields=len(refs),nonnull_reference_fields=sum(not f['value']['nullable'] for f in refs),mutable_nonnull_reference_fields=sum(f['mutable'] and not f['value']['nullable'] for f in refs),immutable_reference_fields=sum(not f['mutable'] for f in refs),max_rec_group=max(g['length'] for g in m['groups']),operations=m['operations'])
        if m['status']=='inspected':
            row['independent_scope_gates']=dict(nonfinal_or_subtyping=any(not t['final'] or t['supertypes'] for t in m['types']),shared=any(t['shared'] for t in m['types']),over_4096_types=len(m['types'])>4096)
        try:read(file);row['prototype_input_status']='supported'
        except Unsupported as e:row['prototype_input_status']='unsupported';row['prototype_input_reason']=str(e)
        except Exception as e:row['prototype_input_status']='reader-error';row['prototype_input_reason']=str(e)
        rows.append(row)
    dump(out/'rows.json',rows);summary=dict(files=len(rows),inspected=sum(r['inspection_status']=='inspected' for r in rows),prototype_status=dict(collections.Counter(r['prototype_input_status'] for r in rows)),distinct_applications=6,optimized_unoptimized_pairs=6,executed_downloaded_apps=False);dump(out/'summary.json',summary)
    for p in [Path(__file__),HERE/'inspector/src/main.rs',HERE/'inspector/Cargo.toml',HERE/'inspector/Cargo.lock',exe]:shutil.copy2(p,out/p.name)
    dump(out/'manifest.json',[dict(path=str(p.resolve()),sha256=digest(p)) for p in out.rglob('*') if p.is_file()]);print(json.dumps(dict(summary=summary,rows=rows),indent=2))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('corpus',type=Path);ap.add_argument('out',type=Path);a=ap.parse_args();main(a.corpus,a.out)
