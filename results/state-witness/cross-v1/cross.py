"""Independent-engine checks of scalar/segment observers (not full table identity)."""
import argparse,hashlib,importlib.metadata,json,shutil,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'))
import wasmtime as wt


def main(source,out):
    out.mkdir(parents=True,exist_ok=False);shutil.copy2(__file__,out/'cross.py')
    engine=wt.Engine();manifest=json.loads((source/'manifest.json').read_text());rows=[]
    count=traps=0;start=time.perf_counter()
    def invoke(s,e,name,args=()):
        nonlocal count,traps
        count+=1
        try:return {'value':e[name](s,*args)}
        except wt.Trap:traps+=1;return {'trap':True}
    def snap(s,e,m):
        r={}
        for name in ['pages','length','memory_end','table_end']:
            r[name]=invoke(s,e,'__sw_'+name)
        for g in m['globals']:r['g'+str(g['index'])]=invoke(s,e,'__sw_global_'+str(g['index']))
        for seg in m['segments']:
            if seg['probe']:r[seg['probe']]=invoke(s,e,seg['probe'])
        return r
    for row in manifest['rows']:
        meta=row['numericManifest']
        with wt.Store(engine) as store:
            base=wt.Instance(store,wt.Module(engine,(source/row['numeric']).read_bytes()),[]).exports(store)
            initial=snap(store,base,meta)
            for mode,file in row['J'].items():
                with wt.Store(engine) as s:
                    e=wt.Instance(s,wt.Module(engine,(source/file).read_bytes()),[]).exports(s);failures=[]
                    for epoch in range(6):
                        for name,args in [('grow',[1]),('tgrow',[3]),('gput',[333]),('ddrop',[]),('edrop',[]),('fault',[])]:invoke(s,e,name,args)
                        e['__lr_reset'](s);got=snap(s,e,meta)
                        differences=[name for name in initial if got[name]!=initial[name]]
                        if differences:failures.append({'epoch':epoch,'differences':differences})
                    assert (not failures)==(mode=='full'),(row['name'],mode,failures)
                    rows.append({'name':row['name'],'mode':mode,'failures':failures})
    result={'calls':count,'traps':traps,'rows':rows,'seconds':time.perf_counter()-start,
       'wasmtime':importlib.metadata.version('wasmtime'),
       'scope':'Scalar globals, lengths, boundary traps, segment probes. Excludes memory bytes/table function identity.',
       'inputManifestSha256':hashlib.sha256((source/'sha256.json').read_bytes()).hexdigest()}
    (out/'results.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()},indent=2))
    print(json.dumps({k:v for k,v in result.items() if k!='rows'}))


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('source',type=Path);a.add_argument('out',type=Path);v=a.parse_args();main(v.source,v.out)
