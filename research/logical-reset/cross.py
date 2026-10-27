import argparse,hashlib,importlib.metadata,json,random,shutil,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'))
import wasmtime as wt

def invoke(store,e,name,args):
    try:return {'value':e[name](store,*args)}
    except wt.Trap:return {'trap':True}

def snap(store,e):
    size=e['size'](store);tsize=e['tsize'](store);table=[]
    for i in range(tsize):
        fn=e['__test_table'].get(store,i)
        if isinstance(fn,wt.Func):
            try:table.append(fn(store,123))
            except wt.Trap:table.append('trap')
        else:table.append(None)
    return size,tsize,e['gget'](store),bytes(e['__test_mem'].read(store,0,size*65536)),table

def main(source,out):
    out.mkdir(parents=True,exist_ok=False);shutil.copy2(__file__,out/'cross.py')
    m=json.loads((source/'manifest.json').read_text());engine=wt.Engine();rng=random.Random(20261024)
    calls=traps=checked=0;rows=[];start=time.perf_counter()
    try:
        for r in m['rows']:
            if r['mode']!='full':continue
            raw=next(x for x in m['rows'] if x['fixture']==r['fixture'] and x['mode']=='source' and x['pipeline']=='raw')
            a=wt.Module(engine,(source/raw['observed']).read_bytes());b=wt.Module(engine,(source/r['observed']).read_bytes())
            targetStore=wt.Store(engine);target=wt.Instance(targetStore,b,[]).exports(targetStore);count=0
            for epoch in range(12):
                s=wt.Store(engine);e=wt.Instance(s,a,[]).exports(s);target['__lr_reset'](targetStore)
                size=e['size'](s);tsize=e['tsize'](s)
                ops=[('get8',[size*65536]),('tget',[tsize]),('grow',[1]),('tgrow',[3]),('init',[0,0,3]),('tinit',[0,0,3]),
                     ('ddrop',[]),('edrop',[]),('init',[0,0,1]),('tinit',[0,0,1]),('init',[0,0,0]),('tinit',[0,0,0]),
                     ('initactive',[0,1,0]),('tdeclare',[0,0,1]),('side',[-1,909]),('fault',[]),('work',[16])]
                edges=[0,1,2,7,15,16,17,65535,65536,size*65536,size*65536+1,-1,2147483647,-2147483648]
                arity={'get':1,'put':2,'get8':1,'put8':2,'put64':2,'get64':1,'putf32':2,'getf32':1,'putf64':2,'copy':3,'fill':3,'tcopy':3,'tfill':2,'call':2,'offset':1,'grow':1,'tgrow':1}
                for _ in range(80):
                    name=rng.choice(list(arity));ops.append((name,[rng.choice(edges) for _ in range(arity[name])]))
                for name,args in ops:
                    expected=invoke(s,e,name,args);actual=invoke(targetStore,target,name,args)
                    left=snap(s,e);right=snap(targetStore,target)
                    assert expected==actual and left==right,(r['fixture'],r['pipeline'],epoch,name,args,expected,actual)
                    calls+=1;count+=1;checked+=len(left[3]);traps+=int('trap' in expected)
            rows.append({'fixture':r['fixture'],'pipeline':r['pipeline'],'calls':count})
        result={'calls':calls,'sourceTraps':traps,'comparedMemoryBytes':checked,'rows':rows,'seconds':time.perf_counter()-start,
                'wasmtime':importlib.metadata.version('wasmtime'),'sourceSHA256':hashlib.sha256((source/'sha256.json').read_bytes()).hexdigest()}
        (out/'results.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='rows'}))
    except Exception as e:
        (out/'error.json').write_text(json.dumps({'error':str(e)},indent=2),encoding='utf-8');raise
    finally:(out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file()},indent=2),encoding='utf-8')

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('source',type=Path);a.add_argument('out',type=Path);v=a.parse_args();main(v.source,v.out)
