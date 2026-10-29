"""Read-only reconstruction of the saved caller factorial, including label triage."""
import argparse, collections, importlib.util, json, subprocess
from pathlib import Path
from experiment import ROOT, HERE, dump, sha
spec=importlib.util.spec_from_file_location('caller_experiment',HERE/'caller-experiment.py')
ce=importlib.util.module_from_spec(spec);spec.loader.exec_module(ce)

def main(out):
    out.mkdir(parents=True,exist_ok=False)
    src=ROOT/'results/boundary-alias/caller-v1';rows=json.loads((src/'rows.json').read_text())
    errors=[];hashes=0;replayed=0;labels=[];pairs=[];changes=[]
    for folder in ['caller-v1','caller-pilot-v1','caller-calibration-v2']:
        d=ROOT/'results/boundary-alias'/folder
        for item in json.loads((d/'manifest.json').read_text()):
            hashes+=1
            if sha(d/item['file'])!=item['sha256']:errors.append(dict(kind='hash',folder=folder,file=item['file']))
    for r in rows:
        txt=(src/r['stdout_file']).read_text(encoding='utf8')
        line=next((x[15:] for x in txt.splitlines() if x.startswith('[caller-study] ')),None)
        if line is None or json.loads(line)!=r['study']:errors.append(dict(kind='raw-study',file=r['stdout_file']))
    for m in json.loads((src/'metadata.json').read_text()):
        p=src/m['file'];api=json.loads(p.with_suffix('.wasm.api.json').read_text())
        q=subprocess.run([str(ce.INTERFACE),str(p)],capture_output=True,text=True,timeout=10);q.check_returncode();replayed+=1
        if json.loads(q.stdout)!=api:errors.append(dict(kind='metadata-replay',file=p.name))
        if sha(p)!=sha(ce.SOURCE/p.name):errors.append(dict(kind='target-bytes-changed',file=p.name))
    lookup={(r['seed'],r['level'],r['caller'],r['observer'],r['engine']):r for r in rows}
    for r in rows:
        if r['level']!='O0':continue
        s=lookup[r['seed'],'O3',r['caller'],r['observer'],r['engine']]
        a=r['study'];b=s['study'];meta=json.loads((src/('%d-O3.wasm.api.json'%r['seed'])).read_text())['functions']
        same_status=[c['status'] for c in a['calls']]==[c['status'] for c in b['calls']]
        same_trace=ce.semantic_trace(a)==ce.semantic_trace(b)
        pair=dict(seed=r['seed'],caller=r['caller'],observer=r['observer'],engine=r['engine'],status_equal=same_status,trace_equal=same_trace,labels_equal=[c['name'] for c in a['calls']]==[c['name'] for c in b['calls']]);pairs.append(pair)
        if not same_status or not same_trace:errors.append(dict(kind='optimization-semantic',**pair))
        for i,(x,y) in enumerate(zip(a['calls'],b['calls'])):
            if x['name']==y['name']:continue
            one,two=meta.get(x['name']),meta.get(y['name'])
            is_alias=bool(one and two and one['function_index']==two['function_index'])
            labels.append(dict(seed=r['seed'],caller=r['caller'],observer=r['observer'],engine=r['engine'],call=i,before=x['name'],after=y['name'],optimized_export_alias=is_alias))
            if not is_alias:errors.append(dict(kind='unexplained-label',**labels[-1]))
        if r['caller']=='null':
            t=lookup[r['seed'],'O0','typed',r['observer'],r['engine']]['study']
            # Same number/order of invocations is itself checked, not assumed.
            if len(a['calls'])!=len(t['calls']):errors.append(dict(kind='call-count-change',seed=r['seed']))
            for i,(x,y) in enumerate(zip(a['calls'],t['calls'])):
                if x['status']!=y['status']:changes.append(dict(seed=r['seed'],observer=r['observer'],engine=r['engine'],call=i,name=x['name'],known=x['known'],before=x['status'],after=y['status']))
    cross=[];baseline=[];old={(r['seed'],r['level'],r['engine']):r for r in json.loads((ce.SOURCE/'rows.json').read_text())}
    for r in rows:
        if r['engine']=='node':
            s=lookup[r['seed'],r['level'],r['caller'],r['observer'],'spidermonkey']
            equal=ce.semantic_trace(r['study'])==ce.semantic_trace(s['study']) and [c['status'] for c in r['study']['calls']]==[c['status'] for c in s['study']['calls']]
            cross.append(equal)
            if not equal:errors.append(dict(kind='cross-engine',seed=r['seed'],level=r['level'],caller=r['caller'],observer=r['observer']))
        if r['caller']=='null' and r['observer']=='flat':
            equal=[e['id'] for e in r['study']['trace']]==old[r['seed'],r['level'],r['engine']]['alias']['trace'];baseline.append(equal)
            if not equal:errors.append(dict(kind='old-baseline',seed=r['seed']))
    summary=ce.summarize(rows)
    if summary!=json.loads((src/'report.json').read_text())['summary']:errors.append(dict(kind='aggregate'))
    report=dict(processes=len(rows),verified_manifest_entries=hashes,metadata_replays=replayed,target_bytes_unchanged=128,optimization_pairs=len(pairs),optimization_semantic_differences=sum(not p['status_equal'] or not p['trace_equal'] for p in pairs),metadata_label_different_pairs=sum(not p['labels_equal'] for p in pairs),metadata_label_changed_calls=len(labels),all_label_changes_are_optimized_function_aliases=all(x['optimized_export_alias'] for x in labels),cross_engine_conditions=len(cross),cross_engine_differences=sum(not x for x in cross),old_baseline_conditions=len(baseline),old_baseline_differences=sum(not x for x in baseline),caller_status_changes_node_O0_flat=dict(collections.Counter(x['before']+' -> '+x['after'] for x in changes if x['observer']=='flat' and x['engine']=='node')),summary=summary,errors=errors)
    dump(out/'report.json',report);dump(out/'optimization-pairs.json',pairs);dump(out/'label-changes.json',labels);dump(out/'caller-status-changes.json',changes)
    dump(out/'manifest.json',[dict(file=p.name,sha256=sha(p)) for p in sorted(out.iterdir()) if p.is_file()])
    print(json.dumps({k:v for k,v in report.items() if k!='summary'},indent=2));assert not errors
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('out',type=Path);main(p.parse_args().out.resolve())
