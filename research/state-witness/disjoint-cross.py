"""Replay the disjoint corpus's API outcome traces in an independent engine."""
import argparse,hashlib,importlib.metadata,json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'))
import wasmtime as wt

def main(source,out):
    out.mkdir(parents=True,exist_ok=False);r=json.loads((source/'results.json').read_text());engine=wt.Engine();rows=[];calls=0
    cache={f:wt.Module(engine,(source/f).read_bytes()) for f in {x['file'] for x in r['rows']}}
    def invoke(store,e,n,args):
        f=e[n]
        try:
            v=f(store,*args)
            if f.type(store).results and str(f.type(store).results[0])=='i64':v=str(v)
            return {'value':v}
        except wt.Trap:return {'trap':True}
    for item in r['rows']:
        seg=item['segment']
        with wt.Store(engine) as a,wt.Store(engine) as b:
            ae=wt.Instance(a,cache[item['file']],[]).exports(a);be=wt.Instance(b,cache[item['file']],[]).exports(b)
            be[f'__ctx_drop_{seg["kind"]}_{seg["index"]}'](b)
            for step in item['trace']:
                args=[]
                for x in step['args']:
                    bits=64 if x['type']=='i64' else 32;v=int(x['value'])%(1<<bits)
                    args.append(v if v<(1<<(bits-1)) else v-(1<<bits))
                assert invoke(a,ae,step['api'],args)==step['baseline'],(item['source'],step)
                assert invoke(b,be,step['api'],args)==step['changed'],(item['source'],step)
                calls+=2
            rows.append({'source':item['source'],'segment':seg,'status':item['status'],'apiTraceMatches':True})
    result={'wasmtime':importlib.metadata.version('wasmtime'),'summary':{**r['summary'],'apiCalls':calls},'rows':rows,
            'scope':'API return/trap traces only; full memory and canonical table snapshots were not repeated.'}
    (out/'results.json').write_text(json.dumps(result,indent=2));shutil.copy2(__file__,out/'disjoint-cross.py')
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()},indent=2));print(json.dumps(result['summary']))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('out',type=Path)
    v=p.parse_args();main(v.source,v.out)
