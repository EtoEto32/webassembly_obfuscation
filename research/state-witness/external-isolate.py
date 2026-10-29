"""Causal controls for the pinned external result; NOT a general migration repair.

Only the two-region, no-local, idempotent fixture shape is accepted. The selector
intervention intentionally changes upstream output and is never counted as an
unmodified upstream result. Segment replay is the known drop-state mechanism.
"""
import argparse,copy,hashlib,importlib.metadata,json,shutil,subprocess,sys
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'))
import wasmtime as wt


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def clear_selector(m):
    m=copy.deepcopy(m);func=k.p.section(m,'func')[0]
    assert sum(x[0]=='local' for x in func[1:] if isinstance(x,list))==1
    assert ['local','i32'] in func
    expected={1,3};found=[]
    for region in func[1:]:
        if not isinstance(region,list) or region[0]!='block':continue
        for i,guard in enumerate(region[1:],1):
            if not isinstance(guard,list) or guard[0]!='block' or guard[-1]!=['br','1']:continue
            assert len(guard)==4
            target=guard[1][2]
            assert target[:2]==['i32.eq',['local.get','0']]
            n=int(target[2][1]);assert n in expected
            assert guard[2]==['br_if','0',['i32.eq',['local.get','0'],['i32.const','0']]]
            region.insert(i+1,['local.set','0',['i32.const','0']]);found.append(n);break
    assert set(found)==expected and len(found)==2,found
    return m,found


def main(source,out,build):
    out.mkdir(parents=True,exist_ok=False);engine=wt.Engine();rows=[];manifest=[]
    exe=build/'target/release/wasm-migrate-probe.exe'
    def invoke(store,fn):
        try:return {'value':fn(store)}
        except wt.Trap:return {'trap':True}
    def instantiate(module,stop,saved=None):
        store=wt.Store(engine);state={'polls':0,'requested':False}
        def should():
            yes=state['polls']==stop;state['polls']+=1;state['requested']|=yes;return int(yes)
        def restore(caller):
            if saved:
                for n,b in saved.items():caller.get(n).write(caller,b,0)
        imports=[wt.Func(store,wt.FuncType([],[wt.ValType.i32()]),should),
                 wt.Func(store,wt.FuncType([],[]),restore,access_caller=True)]
        return store,wt.Instance(store,module,imports).exports(store),state
    for name in ('retained','dropped','empty-dropped','active'):
        src=source/(name+'-observed.wasm');tree=k.p.read(src)
        tree.append(k.p.expr('(func (export "__sw_replay_drop") (data.drop 0))'))
        own=out/(name+'-helper.wasm');k.p.compile_wat(k.p.w.emit(tree),own)
        external=out/(name+'-external.wasm')
        r=subprocess.run([str(exe),str(own),str(external)],capture_output=True,text=True,timeout=30)
        (out/(name+'-transform.json')).write_text(json.dumps({'code':r.returncode,'out':r.stdout,'err':r.stderr},indent=2))
        assert r.returncode==0
        original=k.p.read(external);changed,guards=clear_selector(original)
        fixed=out/(name+'-selector-control.wasm');k.p.compile_wat(k.p.w.emit(changed),fixed)
        manifest.append({'name':name,'sourceHash':digest(src),'source':str(src),'guards':guards})
        with wt.Store(engine) as s:
            e=wt.Instance(s,wt.Module(engine,own.read_bytes()),[]).exports(s)
            expected=invoke(s,e['_start']);value=e['value'](s)
        for selector,filename in [(False,external),(True,fixed)]:
            module=wt.Module(engine,filename.read_bytes())
            s,e,_=instantiate(module,-1);continuous=invoke(s,e['_start'])
            assert continuous==expected and e['value'](s)==value;s.close()
            for segment in (False,True):
                for stop in (0,1):
                    a,ae,ast=instantiate(module,stop);first=invoke(a,ae['_start']);assert ast['requested']
                    before=invoke(a,ae['__sw_data_0']);saved={n:bytes(ae[n].read(a)) for n in ('memory','checkpoint_memory')}
                    b,be,bst=instantiate(module,-1,saved)
                    replay=segment and before.get('trap',False)
                    if replay:be['__sw_replay_drop'](b)
                    after=invoke(b,be['__sw_data_0']);second=invoke(b,be['_start']);bv=be['value'](b)
                    rows.append({'name':name,'selectorControl':selector,'segmentReplay':segment,'stopAt':stop,
                                 'expected':expected,'expectedValue':value,'first':first,'sourceValue':ae['value'](a),
                                 'beforeProbe':before,'freshProbeBeforeResume':after,'dropApplied':replay,
                                 'resumed':second,'resumedValue':bv,'matches':second==expected and bv==value})
                    a.close();b.close()
    summary=[]
    for selector in (False,True):
        for segment in (False,True):
            subset=[r for r in rows if r['selectorControl']==selector and r['segmentReplay']==segment]
            summary.append({'selectorControl':selector,'segmentReplay':segment,'cases':len(subset),
                            'mismatches':sum(not r['matches'] for r in subset)})
    assert [r['mismatches'] for r in summary]==[5,4,1,0],summary
    result={'wasmtime':importlib.metadata.version('wasmtime'),'rows':rows,'summary':summary,'manifest':manifest,
            'scope':'Diagnostic interventions on two-region idempotent fixtures, not a general upstream repair.',
            'executableHash':digest(exe),'inputManifestHash':digest(source/'sha256.json')}
    shutil.copy2(__file__,out/'external-isolate.py');(out/'results.json').write_text(json.dumps(result,indent=2))
    (out/'sha256.json').write_text(json.dumps({p.name:digest(p) for p in out.iterdir() if p.is_file()},indent=2))
    print(json.dumps(summary))


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('source',type=Path);a.add_argument('out',type=Path)
    a.add_argument('--build',type=Path,default=ROOT/'.tools/wasm-migrate-build')
    v=a.parse_args();main(v.source,v.out,v.build)
