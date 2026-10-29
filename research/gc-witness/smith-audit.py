"""Rebuild saved smith outputs and recompute principal summaries."""
import argparse,collections,json,statistics,subprocess,shutil
from pathlib import Path
from experiment import ROOT,HERE,CHECKER,dump,digest

def main(source,inputs,out):
    out.mkdir(parents=True,exist_ok=False);errors=[];rebuilt=0;reinstrumented=0
    rows=json.loads((source/'rows.json').read_text());summary=json.loads((source/'summary.json').read_text())
    for name,modes in summary.items():
        for mode,stored in modes.items():
            rs=[r for r in rows if r['name']==name and r['mode']==mode];gs=[r for r in rs if r.get('generation',{}).get('status')=='generated']
            actual=dict(status=dict(collections.Counter(r['status'] for r in rs)),generated=len(gs),static_constructor_runs=sum(r.get('instrumentation',{}).get('sites',[0])[0]>0 for r in rs),successful_constructor_runs=sum(r.get('constructed',0)>0 for r in rs),successful_access_runs=sum(r.get('accessed',0)>0 for r in rs),median_generation_ms=statistics.median(r['generation']['generation_ms'] for r in gs),total_bytes=sum(r['generation']['bytes'] for r in gs))
            if actual!=stored:errors.append(dict(kind='summary',name=name,mode=mode))
    scratch=out/'rebuild';scratch.mkdir()
    for old in rows:
        name,seed,mode=old['name'],old['seed'],old['mode'];stem='%s-%s-%s'%(name,seed,mode);dest=scratch/(stem+'.wasm');shape=source/(name+'-shape.wasm');driver=source/'source'/('gc-witness-smith-'+mode+'.exe')
        cp=subprocess.run([str(driver),str(shape),str(source/(name+'-%s.seed'%seed)),str(dest)],capture_output=True,text=True,timeout=15)
        try:g=json.loads(cp.stdout)
        except ValueError:g={}
        og=old.get('generation',{})
        if g.get('status')!=og.get('status') or g.get('reason')!=og.get('reason'):errors.append(dict(kind='generation-status',name=stem));continue
        if g.get('status')!='generated':continue
        rebuilt+=1
        if dest.read_bytes()!=(source/(stem+'.wasm')).read_bytes():errors.append(dict(kind='generation-bytes',name=stem))
        counted=scratch/(stem+'-counted.wasm');cp=subprocess.run([str(CHECKER),'instrument',str(shape),'0',str(dest),str(counted),'--bound-arrays'],capture_output=True,text=True,timeout=10);ins=json.loads(cp.stdout)
        if ins.get('status')!='instrumented':errors.append(dict(kind='instrumentation-status',name=stem));continue
        reinstrumented+=1
        if counted.read_bytes()!=(source/(stem+'-counted.wasm')).read_bytes():errors.append(dict(kind='instrumentation-bytes',name=stem))
    ir=json.loads((inputs/'rows.json').read_text());orig={(r['name'],r['seed'],r['mode']):r for r in rows};nulls=0;newseeds={}
    for r in ir:
        if r['variant']=='null':
            nulls+=1;o=orig[r['name'],r['seed'],r['mode']]
            if any(r.get(k)!=o.get(k) for k in ['status','constructed','accessed']):errors.append(dict(kind='null-replay',name=r['name'],seed=r['seed']))
    for name,modes in json.loads((inputs/'summary.json').read_text()).items():
        newseeds[name]={}
        for mode,s in modes.items():
            rs=[r for r in ir if r['name']==name and r['mode']==mode]
            empty={r['seed'] for r in rs if r['variant']=='empty' and r.get('accessed',0)>0};deep={r['seed'] for r in rs if r['variant'].startswith('depth') and r.get('accessed',0)>0};newseeds[name][mode]=sorted(deep-empty)
            if sorted(deep-empty)!=s['new_access_seeds_vs_empty'] or sorted(deep)!=s['deep_access_seeds']:errors.append(dict(kind='input-summary',name=name,mode=mode))
    upstream=ROOT/'.tools/gc-witness-smith-upstream';provenance=json.loads((upstream/'provenance.json').read_text());checked=0
    for r in provenance['files']:
        checked+=1
        if digest(upstream/r['file'])!=r['sha256']:errors.append(dict(kind='upstream-modified',file=r['file']))
    result=dict(rebuilt=rebuilt,reinstrumented=reinstrumented,recomputed_generation_groups=sum(len(v) for v in summary.values()),null_replays=nulls,input_calls=len(ir),new_access_seeds_vs_empty=newseeds,upstream_files=checked,errors=errors);dump(out/'report.json',result)
    for p in [Path(__file__),HERE/'checker/src/main.rs',HERE/'checker/src/instrument.rs',CHECKER]:shutil.copy2(p,out/p.name)
    dump(out/'manifest.json',[dict(path=str(p.resolve()),sha256=digest(p)) for p in out.rglob('*') if p.is_file()]);print(json.dumps(result,indent=2));assert not errors
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('inputs',type=Path);ap.add_argument('out',type=Path);a=ap.parse_args();main(a.source,a.inputs,a.out)
