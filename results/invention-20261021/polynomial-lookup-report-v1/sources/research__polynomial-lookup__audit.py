import json,pathlib,re,struct,subprocess,sys,time
import prototype as p
root=pathlib.Path(sys.argv[1]).resolve();out=pathlib.Path(sys.argv[2]).resolve();out.mkdir(parents=True,exist_ok=False)
def save(name,obj):(out/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding='utf-8')
rows=json.loads((root/'manifest.json').read_text());replay=[];interpreter=[];attacks=[]
assert all(p.P%d for d in range(2,65536))  # Deterministic trial division, sqrt(P)<65536.
for r in rows:
    file=out/pathlib.Path(r['file']).name
    if r['mode'] in ('array','poly','poly-pruned'):
        raw=out/(r['name']+'-'+r['mode']+'-raw.wasm')
        if r['stage']=='raw':p.transform(root/(r['name']+'-list-raw.wasm'),raw,r['mode'])
        else:p.q.tool('wasm-opt',[raw,'-O3','--enable-bulk-memory','-o',file])
        same=file.read_bytes()==pathlib.Path(r['file']).read_bytes();assert same
        replay.append(dict(file=file.name,byte_identical=same))
    elif r['mode']=='recovered':
        p.recover(root/(r['name']+'-poly-'+r['stage']+'.wasm'),file)
        same=file.read_bytes()==pathlib.Path(r['file']).read_bytes();assert same
        replay.append(dict(file=file.name,byte_identical=same))
    # 3 independent interpreter probes for every main condition, oracle from source fixture.
    oracle=json.loads((root/(r['name']+'-oracle.json')).read_text());mapping=dict(oracle['items'])
    xs=[0,p.P+4,next(iter(mapping),1)];m=p.q.read(r['file'])
    idx=next(e[2][1] for e in m[1:] if e[0]=='export')
    for i,x in enumerate(xs):m.append(p.q.w.parse(f'(module (func (export "probe{i}") (result i32) (call {idx} (i32.const {x}))))')[1])
    probe=out/(pathlib.Path(r['file']).stem+'-probe.wasm');p.q.compile(p.q.w.emit(m),probe)
    stdout=p.q.w.tool('wasm-interp',[probe,'--run-all-exports'])
    got=[int(v) for v in re.findall(r'probe\d+\(\) => i32:(\d+)',stdout)]
    assert got==[mapping.get(x,0) for x in xs],(r,stdout)
    interpreter.append(dict(file=r['file'],inputs=xs,outputs=got,stdout=stdout))
    # Pruning is the same representation, but validate recovery of its actual O3/raw binary too.
    if r['mode']=='poly-pruned':
        recovered=p.recover(r['file']);assert recovered['items']==sorted(mapping.items())
        attacks.append(dict(name=r['name'],stage=r['stage'],mode=r['mode'],**recovered))
save('replay.json',replay);save('interpreter.json',interpreter);save('pruned-recovery.json',attacks)

# Valid source modules that must not be converted because their observable semantics differ.
base=p.q.read(root/'n8-list-raw.wasm');reject=[]
import copy
mods={}
m=copy.deepcopy(base);m.append(['export','"memory"',['memory','0']]);mods['memory-export']=m
m=copy.deepcopy(base);f=next(e for e in m[1:] if e[0]=='func');f.insert(6,['i32.store',['i32.const','0'],['i32.const','1']]);mods['write']=m
for name,target in [('cycle',64),('out-of-bounds',65532)]:
    m=copy.deepcopy(base);d=next(e for e in m[1:] if e[0]=='data');data=bytearray(p.unquote(d[2]));struct.pack_into('<I',data,0,target);d[2]=p.quoted(data);mods[name]=m
for name,m in mods.items():
    src=out/f'reject-{name}.wasm';p.q.compile(p.q.w.emit(m),src)
    try:p.transform(src,out/f'UNEXPECTED-{name}.wasm','poly')
    except p.q.Unsupported as e:reject.append(dict(name=name,status='rejected',reason=str(e)))
    else:raise AssertionError(name)
save('rejections.json',reject)

# Three wrong transforms with concrete execution witnesses.
source=root/'boundary-poly-raw.wasm';wat=p.q.w.tool('wasm2wat',[source,'--fold-exprs','--no-debug-names']);m=p.q.w.parse(wat)
negative=[];mapping=dict(json.loads((root/'boundary-oracle.json').read_text())['items'])
mods={}
m1=copy.deepcopy(m)
for e in p.q.walk(m1):
    if e[0]=='i64.ge_u':e[:]=['i32.const','0']
mods['missing-key-domain-split']=m1
m2=copy.deepcopy(m);d=next(e for e in m2[1:] if e[0]=='data');data=bytearray(p.unquote(d[2]));n=struct.unpack_from('<I',data,0)[0]
for i in range(n):struct.pack_into('<I',data,28+4*(2*n+1+i),0)
d[2]=p.quoted(data);mods['missing-value-quotient']=m2
m3=copy.deepcopy(m)
for e in p.q.walk(m3):
    if e[0]=='i64.mul' and e[1][:1]==['local.get'] and e[2][:1]==['local.get']:
        old=copy.deepcopy(e);e[:]=['i64.extend_i32_u',['i32.wrap_i64',old]];break
mods['wrapped-product']=m3
node="const fs=require('fs');const a=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[1]))).exports;const xs=JSON.parse(process.argv[2]);console.log(JSON.stringify(xs.map(x=>a.lookup(x)>>>0)));"
for name,mod in mods.items():
    dst=out/f'negative-{name}.wasm';p.q.compile(p.q.w.emit(mod),dst);xs=list(mapping)
    got=json.loads(subprocess.check_output(['node','-e',node,str(dst),json.dumps(xs)],text=True,timeout=30))
    witnesses=[dict(input=x,expected=mapping[x],actual=y) for x,y in zip(xs,got) if y!=mapping[x]]
    assert witnesses,name;negative.append(dict(name=name,witnesses=witnesses))
save('negative.json',negative)

# Analysis timings use fresh Python processes and three public split seeds. No source oracle in child.
timings=[]
for name in ('n8','n32','n128','full32'):
    expected=sorted(json.loads((root/(name+'-oracle.json')).read_text())['items'])
    for mode in ('array','poly','poly-pruned'):
        file=root/(name+'-'+mode+'-O3.wasm')
        for rep in range(3):
            cmd=['python',str(pathlib.Path(__file__).with_name('attack.py')),str(file),'array' if mode=='array' else 'poly',str(271021+rep)]
            run=subprocess.run(cmd,capture_output=True,text=True,timeout=60,check=True);got=json.loads(run.stdout)
            assert got['items']==expected
            timings.append(dict(name=name,mode=mode,process=rep,seed=271021+rep,**got))
save('analysis-timings.json',timings)
print(json.dumps(dict(replay=len(replay),interpreter_calls=sum(len(x['inputs']) for x in interpreter),
 pruned_recovered=len(attacks),valid_rejections=len(reject),negative_witnessed=len(negative),analysis_processes=len(timings))))
