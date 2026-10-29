"""Adaptive shape recovery and matched runtime controls for the bounded probe."""
import argparse
import collections
import json
import os
from pathlib import Path
import platform
import random
import statistics
import subprocess
import time

import pilot
import wasm_probe as w


def recover_shape(r, texts):
    cs=r.SchemaParser.parse_constraint_set(texts)
    eq,g=r.Solver.compute_quotient_graph(cs,r.DummyLattice().atomic_types)
    root=eq.find_equiv_rep(r.SchemaParser.parse_variable('F.in_0'))
    if root is None:
        raise ValueError('missing root')
    bounds=collections.defaultdict(set)
    for c in cs:
        if c.right in r.DummyLattice().atomic_types:
            node=eq.find_equiv_rep(c.left)
            if node is not None:
                bounds[node].add(str(c.right))
    fields=[]
    for _,load,label in g.out_edges(root,data='label'):
        if label!=r.LoadLabel.instance():
            continue
        for _,target,label in g.out_edges(load,data='label'):
            if isinstance(label,r.DerefLabel):
                fields.append({'offset':label.offset,'bytes':label.size,
                               'recursive_pointer':target==root,
                               'upper_bounds':sorted(bounds[target])})
    fields.sort(key=lambda f:f['offset'])
    return {'fields':fields,'quotient_nodes':len(g.nodes),'quotient_edges':len(g.edges)}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('regular',type=Path);p.add_argument('forced',type=Path);p.add_argument('out',type=Path)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    r=pilot.load_retypd()
    analysis=[];jobs=[];byte_matches=[]
    replay=a.out/'replay';replay.mkdir()
    for kind,directory in [('regular',a.regular),('forced',a.forced)]:
        manifest=json.loads((directory/'manifest.json').read_text(encoding='utf-8'))
        for row in manifest['rows']:
            start=time.perf_counter();texts=w.extract(directory/row['file'])
            read_ms=(time.perf_counter()-start)*1000
            samples=[]
            for _ in range(11):
                start=time.perf_counter();shape=recover_shape(r,texts)
                samples.append((time.perf_counter()-start)*1000)
            expected=[{'offset':off,'bytes':4,'recursive_pointer':off!=8,
                       'upper_bounds':[] if off!=8 else ['int']} for off in (0,4,8)]
            assert shape['fields']==expected,(row['file'],shape)
            # Change an actual field constraint to check that the extractor responds.
            changed=[x.replace('\u03c34@8','\u03c34@12') for x in texts]
            negative=recover_shape(r,changed)
            assert [x['offset'] for x in negative['fields']]==[0,4,12]
            analysis.append({'kind':kind,'file':row['file'],'reader_ms':read_ms,
                             'shape_ms_median':statistics.median(samples),'shape_ms_samples':samples,
                             'shape':shape,'changed_field_detected':True})
            if row['n'] in (1,4,8) and 'O3' in row['file']:
                jobs += [(kind,directory,row,i) for i in range(3)]
            if 'raw' in row['file']:
                raw=replay/(kind+'-'+row['file']);opt=raw.with_name(raw.name.replace('-raw','-O3'))
                w.q.compile(w.module(row['n'],row['mode']=='peeled',kind=='forced'),raw)
                w.q.tool('wasm-opt',[raw,'-O3','--enable-bulk-memory','-o',opt])
                for f in (raw,opt):
                    original=directory/f.name[len(kind)+1:]
                    assert f.read_bytes()==original.read_bytes(),str(original)
                    byte_matches.append({'original':str(original),'sha256':w.q.digest(f)})
    w.q.save(a.out/'shape-recovery.json',analysis)
    w.q.save(a.out/'replay.json',byte_matches)
    random.Random(211021).shuffle(jobs)
    runtime=[]
    for kind,directory,row,rep in jobs:
        cmd=['node','--no-liftoff','--no-wasm-lazy-compilation',str(w.HERE/'check.cjs'),str(directory),'bench',row['file']]
        run=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',timeout=30)
        if run.returncode:
            raise RuntimeError(run.stderr)
        sample=json.loads(run.stdout);sample.update(kind=kind,rep=rep)
        runtime.append(sample)
        w.q.save(a.out/'runtime.json',runtime)
        print(json.dumps({k:sample[k] for k in ('kind','file','rep','ns_per_call_median')}),flush=True)
    w.q.save(a.out/'environment.json',{'os':platform.platform(),'processor':platform.processor(),
                                      'python':platform.python_version(),'cwd':str(w.ROOT),
                                      'node_flags':['--no-liftoff','--no-wasm-lazy-compilation'],
                                      'cpu_affinity':'unfixed','frequency':'unfixed',
                                      'retpy_commit':subprocess.check_output(['git','-C',str(pilot.SOURCE),'rev-parse','HEAD'],text=True).strip()})


if __name__=='__main__':
    main()
