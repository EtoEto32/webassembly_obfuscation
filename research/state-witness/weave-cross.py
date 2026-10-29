"""Independent Wasmtime execution of Weave's memory/control-global ABI."""
import argparse,hashlib,importlib.metadata,json,shutil,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'))
import wasmtime as wt

def main(source,out):
    out.mkdir(parents=True,exist_ok=False);engine=wt.Engine();rows=[]
    manifest=json.loads((source/'manifest.json').read_text())
    js="""import fs from 'node:fs';import path from 'node:path';import {pathToFileURL} from 'node:url';
const dir=process.argv[1];const {extractMeta}=await import(pathToFileURL(path.join(dir,'weave.mjs')));
const m=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json')));
console.log(JSON.stringify(Object.fromEntries(m.rows.filter(x=>x.status==='valid').map(x=>[x.output,extractMeta(fs.readFileSync(path.join(dir,x.output)))]))));"""
    r=subprocess.run(['node','--input-type=module','-e',js,str(source.resolve())],capture_output=True,text=True,timeout=30)
    assert r.returncode==0,r.stderr;metas=json.loads(r.stdout)
    def invoke(s,e,name):
        try:e[name](s);return {'status':'held' if e['__weave_flag'].value(s)==1 else 'done',**({} if e['__weave_flag'].value(s)==1 else {'results':[]})}
        except wt.Trap:return {'trap':True}
    def make(module,meta,stop,saved=None):
        s=wt.Store(engine);state={'polls':0}
        def poll():
            n=state['polls'];state['polls']+=1;return int(stop>=0 and n>=stop)
        e=wt.Instance(s,module,[wt.Func(s,wt.FuncType([],[wt.ValType.i32()]),poll)]).exports(s)
        if saved:
            memories,globals_=saved
            for n,b in memories.items():
                mem=e[n];need=len(b)//65536-mem.size(s)
                if need>0:mem.grow(s,need)
                mem.write(s,b,0)
            for n,v in globals_.items():e[n].set_value(s,v)
        else:e['__weave_init'](s)
        return s,e,state
    def value(s,e):return int.from_bytes(e['memory'].read(s,0,4),'little',signed=True)
    def probe(s,e):
        try:e['__sw_data_0'](s);return {'value':None}
        except wt.Trap:return {'trap':True}
    node=json.loads((source/'results.json').read_text())
    for item in node['rows']:
        assert item['status']=='executed'
        r=next(r for r in manifest['rows'] if r['name']==item['name'] and r['kind']==item['kind'])
        meta=metas[r['output']];module=wt.Module(engine,(source/r['output']).read_bytes())
        s,e,stats=make(module,meta,-1);continuous=invoke(s,e,'_start');cv=value(s,e);polls=stats['polls'];s.close()
        scenarios=[]
        for stop in range(polls+1):
            a,ae,_=make(module,meta,stop);first=invoke(a,ae,'_start')
            if first.get('status')!='held':scenarios.append({'stopAt':stop,'status':'checkpoint-not-reached','outcome':first});a.close();continue
            saved=({n:bytes(ae[n].read(a)) for n in meta['memories']},{n:ae[n].value(a) for n in meta['controlGlobals']})
            observed=None
            if item['kind']=='observed':
                z,ze,_=make(module,meta,-1,saved);observed={'source':probe(a,ae),'restored':probe(z,ze)};z.close()
            b,be,_=make(module,meta,-1,saved);resumed=invoke(b,be,'__weave_resume');bv=value(b,be)
            scenarios.append({'stopAt':stop,'status':'restored','resumed':resumed,'resumedValue':bv,'probe':observed,
                              'matches':resumed==item['expected'] and bv==item['expectedValue']});a.close();b.close()
        rows.append({'name':item['name'],'kind':item['kind'],'status':'executed','expected':item['expected'],
                     'expectedValue':item['expectedValue'],'continuous':continuous,'continuousValue':cv,'polls':polls,'scenarios':scenarios})
    assert rows==node['rows']
    result={'wasmtime':importlib.metadata.version('wasmtime'),'rows':rows,'matchesNode':True,
            'inputManifestHash':hashlib.sha256((source/'sha256.json').read_bytes()).hexdigest()}
    (out/'metadata.json').write_text(json.dumps(metas,indent=2));(out/'results.json').write_text(json.dumps(result,indent=2))
    shutil.copy2(__file__,out/'weave-cross.py')
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()},indent=2))
    print(json.dumps({'rows':len(rows),'matchesNode':True}))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('source',type=Path);a.add_argument('out',type=Path);v=a.parse_args();main(v.source,v.out)
