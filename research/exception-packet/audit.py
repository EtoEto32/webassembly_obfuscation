import argparse,json,statistics,subprocess,datetime
from pathlib import Path
import prototype as p
from run import save,snapshot
def load(d,f):return json.loads((d/f).read_text(encoding='utf-8'))
def main(root,out):
    root=Path(root);out=Path(out);out.mkdir(parents=True,exist_ok=False);snapshot(out)
    base=root/'exception-packet-v3';ver=root/'exception-packet-verify-v1';perf=root/'exception-packet-performance-v1';comp=root/'exception-packet-compatibility-v1';normal=root/'exception-packet-normal-v1'
    m=load(base,'manifest.json');a=load(base,'attacks.json');c=load(base,'correctness.json');vs=load(ver,'summary.json');ps=load(perf,'summary.json');cs=load(comp,'summary.json')
    assert len(m['files'])==72 and len(a)==72 and all(x['status']=='recovered' for x in a)
    assert c['calls']==147456 and c['mismatches']==c['unexpected_exceptions']==0
    assert len(c['rows'])==144 and all(x['errors']==0 and x['calls']==1024 for x in c['rows'])
    assert vs['interpreter_calls']==288 and vs['extra']['errors']==0 and vs['extra']['calls']==24864 and vs['refusals']==4
    assert vs['extra']['wrong_handler_mismatches']>0 and vs['extra']['null_packet_traps']==518
    assert load(comp,'correctness.json')==dict(calls=9216,errors=0)
    assert cs['targets']==cs['recoveries']==6 and cs['wabt_unsupported']==3
    for f in m['files']:
        assert p.digest(base/f['file'])==f['sha256'] and (base/f['file']).stat().st_size==f['bytes']
        assert p.digest(base/f['recovered'])==f['recovered_sha256']
    for f in m['sources']:assert p.digest(base/f['file'])==f['sha256']
    snapshots={}
    for d in (base,ver,perf,comp,normal):
        for x in load(d,'sources.json'):
            actual=p.digest(d/'sources'/x['snapshot']);assert actual==x['sha256']
            assert p.digest(p.ROOT/x['path'])==actual,(d,x['path'])
            snapshots[x['path']]=actual
    samples=load(perf,'samples.json');assert len(samples)==ps['fresh_processes']==108
    for f in ps['files']:
        assert p.digest(perf/f['file'])==f['harness_sha256']
        rs=[x for x in samples if x['file']==f['file']];assert len(rs)==3
        for x in rs:assert x['median_ns']==statistics.median(x['samples_ns']) and x['harness_checks']==4
        assert f['median_ns']==statistics.median(x['median_ns'] for x in rs)
    proofs=load(ver,'scalar-model-equivalence.json')['proofs'];nf=load(normal,'results.json')
    proven={x['file'] for x in proofs if x['status']=='unsat'}|{x['file'] for x in nf if x['equal']}
    assert proven=={x['file'] for x in m['files']}
    replay=[]
    for source in m['sources']:
        for mode in p.MODES:
            stem=f"{source['kernel']}{source['k']}-{mode}"
            raw=out/f'{stem}-raw.wasm';p.transform(base/source['file'],raw,mode)
            opt=out/f'{stem}-O3.wasm';p.optimize(raw,opt)
            for target in (raw,opt):
                assert p.digest(target)==p.digest(base/target.name),target
                replay.append(dict(file=target.name,sha256=p.digest(target)))
    # The unsupported-feature variants are readable by the adaptive route.
    survival=[]
    def count(tree,op):return int(tree[0]==op)+sum(count(x,op) for x in tree[1:] if isinstance(x,list))
    for f in m['files']:
        if f['mode'] in ('fresh','shared') and f['opt']=='O3':
            tree=p.binaryen_tree(base/f['file']);survival.append(dict(file=f['file'],throw_ref=count(tree,'throw_ref'),throw=count(tree,'throw')))
            assert survival[-1]['throw_ref']>0 and survival[-1]['throw']>0
    # v2 has identical target bytes; its post-recovery checker limit was not protection.
    previous=load(root/'exception-packet-v2','manifest.json');assert len(previous['files'])==72
    assert all(p.digest(root/'exception-packet-v2'/x['file'])==p.digest(base/x['file']) for x in previous['files'])
    docs=['README.md','algorithm.md','analysis.md','prior-art.md','paper-note.md','plan.md']
    for f in docs:assert (Path(__file__).parent/f).read_text(encoding='utf-8')
    save(out/'audit.json',dict(status='passed',time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),goal_complete=False,targets=72,packet_targets=36,recovered=72,native_calls=147456,additional_native_calls=24864,compatibility_native_calls=9216,interpreter_calls=288,performance_processes=108,harness_checks=432,scalar_smt_unsat=sum(x['status']=='unsat' for x in proofs),scalar_smt_unknown=sum(x['status']=='unknown' for x in proofs),normal_form_equal=sum(x['equal'] for x in nf),model_union_supported=len(proven),replay=replay,sources=snapshots,O3_survival=survival,document_hashes={f:p.digest(Path(__file__).parent/f) for f in docs}))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('results');a.add_argument('output');v=a.parse_args();main(v.results,v.output)
