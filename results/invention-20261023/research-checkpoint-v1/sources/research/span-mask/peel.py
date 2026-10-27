# -*- coding: utf-8 -*-
"""Adaptive inversion by strictly reducing public ANF coefficient weight.

No generator operation sequence, random seed, original formula or fixture is used.
Each candidate elementary operation is sound whether or not it was used to generate.
"""
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time
import prototype as p
import attack


@lru_cache(maxsize=100000)
def weight(v):return bin(v).count('1')


def scaled(row,bit):
    out={}
    for m,bits in row.items():
        key=m|bit;out[key]=out.get(key,0)^bits
    return {m:b for m,b in out.items() if b}


def gain(a,b):
    return sum(weight(a.get(m,0))-weight(a.get(m,0)^bits) for m,bits in b.items())


def transpose(rows,width):
    cols=[{} for _ in range(width)]
    for i,row in enumerate(rows):
        for mono,bits in row.items():
            while bits:
                bit=bits & -bits;j=bit.bit_length()-1
                cols[j][mono]=cols[j].get(mono,0)|(1<<i)
                bits ^= bit
    return cols


def simplify(record,seconds=30):
    start=time.perf_counter();deadline=start+seconds
    rows=[dict(x) for x in record['rows']];target=dict(record['target'])
    scalars=[0]+[1<<i for i in range(record['n'])]
    cost=lambda:sum(weight(v) for r in rows+[target] for v in r.values())
    initial=cost();steps=[];tested=0;status='local_minimum'
    for iteration in range(512):
        best=None
        for side,vecs in (('row',rows),('column',transpose(rows+[target],record['d']))):
            for a,src in enumerate(vecs):
                for scalar in scalars:
                    s=scaled(src,scalar)
                    for b,dst in enumerate(vecs):
                        if a==b:continue
                        tested+=1;g=gain(dst,s)
                        if g>0 and (best is None or g>best[0]):best=(g,side,a,b,scalar,s)
                    if time.perf_counter()>deadline:
                        status='preprocess_budget';break
                if status=='preprocess_budget':break
            if status=='preprocess_budget':break
        if best is None:break
        g,side,a,b,scalar,s=best
        before=cost()
        if side=='row':rows[b]=p.add_scaled(rows[b],rows[a],scalar)
        else:
            rows=[p.column_add(r,a,b,scalar) for r in rows]
            target=p.column_add(target,a,b,scalar)
        after=cost()
        assert before-after==g and g>0
        steps.append({'side':side,'src':a,'dst':b,'scalar':scalar,'before':before,'after':after})
        if status=='preprocess_budget':break
    else:status='step_budget'
    result={**record,'rows':[sorted(r.items()) for r in rows],'target':sorted(target.items())}
    return result,{'initial_weight':initial,'final_weight':cost(),'steps':steps,'tested':tested,
                   'preprocess_status':status,'preprocess_ms':(time.perf_counter()-start)*1000}


def main(mainpath,out):
    mainpath=Path(mainpath);out=Path(out);out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
    for name in ('prototype.py','attack.py','peel.py'):shutil.copyfile(p.HERE/name,out/'sources'/name)
    manifest=json.loads((mainpath/'manifest.json').read_text(encoding='utf8'));results=[]
    for t in manifest['targets']:
        if t['form']!='O3' or t['mode'] not in ('constant','dependent'):continue
        src=mainpath/t['file'];r,reader=attack.read(src);r,log=simplify(r)
        name=t['fixture']+'-'+t['mode']
        (out/(name+'-operations.json')).write_text(json.dumps(log,indent=2),encoding='utf8')
        (out/(name+'-record.json')).write_text(json.dumps(r),encoding='utf8')
        print(json.dumps({'preprocessed':name,**{k:v for k,v in log.items() if k!='steps'},'steps':len(log['steps'])}),flush=True)
        b=attack.BDD();start=time.perf_counter()
        try:
            root=attack.symbolic(r,b);core=(time.perf_counter()-start)*1000
            assert b.digest(root)==manifest['fixtures'][t['fixture']]['bdd_digest']
            p.save(attack.render_bdd(r['n'],b,root),out/(name+'-recovered.wasm'))
            info={'status':'recovered','bdd_digest':b.digest(root),'output_nodes':len(attack.reachable(b,root)),'source_bdd_equal':True}
        except (OverflowError,TimeoutError) as e:
            core=(time.perf_counter()-start)*1000
            info={'status':'node_budget' if isinstance(e,OverflowError) else 'timeout','message':str(e)}
        result={**t,**info,'reader_ms':reader,'core_ms':core,'bdd_nodes':len(b.nodes),
                **{k:v for k,v in log.items() if k!='steps'},'steps':len(log['steps'])}
        results.append(result);(out/'results.json').write_text(json.dumps(results,indent=2),encoding='utf8')
        print(json.dumps(result),flush=True)
    (out/'sha256.json').write_text(json.dumps({str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(out.rglob('*')) if f.is_file()},indent=2),encoding='utf8')


if __name__=='__main__':main(*sys.argv[1:])
