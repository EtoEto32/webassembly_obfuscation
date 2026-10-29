"""Infer logical stage order from predecessor edges, without using mask values."""
import argparse,copy,json,statistics,time
from pathlib import Path
import prototype as p
def extract(src):
    start=time.perf_counter();m=p.read(src);t1=time.perf_counter();loops=[x for x in p.walk(m) if x[0]=='loop']
    if len(loops)!=1:raise p.Unsupported('one loop')
    env={};stack=[];packets=[]
    def seq(es):
        for e in es:
            v=resolve(e)
            if v is not None:stack.append(v)
    def resolve(e):
        if not isinstance(e,list):return e
        if e[0]=='local.get':return copy.deepcopy(env.get(e[1],e))
        if e[0] in ('local.set','local.tee'):
            v=resolve(e[2]) if len(e)==3 else stack.pop();env[e[1]]=v;return v if e[0]=='local.tee' else None
        if e[0] in ('then','block'):seq(e[1:]);return None
        if e[0] in ('if','br','br_if'):
            for x in e[1:]:
                if isinstance(x,list):resolve(x)
            return None
        z=[e[0],*[resolve(x) for x in e[1:]]]
        if e[0]=='v128.bitselect':packets.append((z[1],z[2])) # mask deliberately not retained
        return z
    seq(loops[0][1:]);values={};predecessors={};kinds=set();rotations=set()
    for update,old in packets:
        if old[0]!='local.get':raise p.Unsupported('state head')
        cc=[p.words(x) for x in p.walk(update) if x[0]=='v128.const' and all(v>65536 and v&1 for v in p.words(x))]
        if not cc or any(v!=cc[0] for v in cc):raise p.Unsupported('coefficient vector')
        shuffles=list({p.w.emit(x):x for x in p.walk(update) if x[0]=='i8x16.shuffle'}.values())
        if len(shuffles)!=1:raise p.Unsupported('shuffle')
        sh=shuffles[0];ix=list(map(int,sh[1:17]));args=sh[17:]
        kinds.add({'v128.or':0,'i32x4.add':1,'v128.xor':2}[update[0]])
        rotations.update(int(x[2][1],0) for x in p.walk(update) if x[0]=='i32x4.shl')
        for lane in range(4):
            node=(old[1],lane);offset=ix[lane*4]
            if node in values or offset%4 or ix[lane*4:lane*4+4]!=list(range(offset,offset+4)):raise p.Unsupported('word routing')
            origin=args[offset//16];values[node]=cc[0][lane]
            if origin[0]=='local.get':predecessors[node]=(origin[1],offset%16//4)
            elif origin[0]=='i32x4.splat':predecessors[node]=None
            else:raise p.Unsupported('predecessor source')
    successor={};roots=[]
    for node,previous in predecessors.items():
        if previous is None:roots.append(node)
        elif previous not in values or previous in successor:raise p.Unsupported('not a chain')
        else:successor[previous]=node
    if len(roots)!=1:raise p.Unsupported('one stream root')
    order=[];node=roots[0]
    while node is not None:
        if node in order:raise p.Unsupported('cycle')
        order.append(node);node=successor.get(node)
    if len(order)!=len(values) or len(order) not in (4,8,16) or len(kinds)!=1 or len(rotations)!=1:raise p.Unsupported('incomplete graph')
    return dict(n=len(order),coeff=[values[x] for x in order],kind=kinds.pop(),r=rotations.pop(),order=order,mask_values_used=False,read_ms=(t1-start)*1000,extract_ms=(time.perf_counter()-t1)*1000)
def main(data,out):
    data,out=map(Path,(data,out));out.mkdir(parents=True,exist_ok=False);rows=[]
    for r in json.loads((data/'manifest.json').read_text()):
        if 'attack' not in r:continue
        runs=[extract(data/r['file']) for _ in range(7)];a=runs[0]
        # Source, generation seed and reference coefficients consulted only after inference.
        assert all(all(x[k]==r[k] for k in ('n','kind','r','coeff')) for x in runs)
        f=out/(Path(r['file']).stem+'-graph-recovered.wasm');p.compile(p.w.emit(p.source(a['coeff'],a['kind'],a['r'])),f)
        assert p.digest(f)==p.digest(data/r['source'])
        rows.append(dict(file=r['file'],recovered=f.name,recovered_sha256=p.digest(f),runs=runs))
    p.save(out/'records.json',rows);p.save(out/'summary.json',dict(targets=len(rows),runs=len(rows)*7,byte_identical_to_source=len(rows),mask_values_used=False,extract_ms=[min(statistics.median(a['extract_ms'] for a in r['runs']) for r in rows),max(statistics.median(a['extract_ms'] for a in r['runs']) for r in rows)],source_sha256=p.digest(Path(__file__))));print((out/'summary.json').read_text())
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('data');a.add_argument('output');v=a.parse_args();main(v.data,v.output)
