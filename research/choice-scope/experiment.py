import argparse,collections,hashlib,importlib.metadata,itertools,json,platform,random,shutil,subprocess,sys,time
from pathlib import Path
from oracle import Program,Unsupported,w,z,bv,ROOT
from fixtures import fixtures
HERE=Path(__file__).resolve().parent
def dump(path,obj):path.write_text(json.dumps(obj,indent=2),encoding='utf8')
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main(out):
    out.mkdir(parents=True,exist_ok=False)
    for f in HERE.glob('*.py'):shutil.copy2(f,out/f.name)
    shutil.copy2(HERE/'node.cjs',out/'node.cjs');shutil.copy2(ROOT/'research/connectivity-elimination/prototype.py',out/'wat-reader.py')
    inputs=[[0,0],[1,0x80],[0x7fffffff,0x00800080],[0xffffffff,0xff00ff00],[0x80000000,0xffffffff],[0x7fc00001,0x0f0f0f0f],[0x7fc00000,0x80808080],[0x3f800000,0x7f7f7f7f]]
    rng=random.Random(20261026);inputs += [[rng.getrandbits(32),rng.getrandbits(32)] for _ in range(8)]
    files=[];build=[];metadata=[]
    for f in fixtures():
        name=f['name'];wat=out/(name+'.wat');wat.write_text(f['wat']);raw=out/(name+'.wasm');t=time.perf_counter()
        w.tool('wat2wasm',[wat,'--enable-all','-o',raw]);w.tool('wasm-validate',[raw,'--enable-all'])
        build.append(dict(file=raw.name,milliseconds=(time.perf_counter()-t)*1000,bytes=raw.stat().st_size));files.append(raw.name);metadata.append({k:v for k,v in f.items() if k!='wat'})
        opt=out/(name+'-O3.wasm');t=time.perf_counter()
        w.tool('wasm-opt',[raw,'-O3','--enable-simd','--enable-relaxed-simd','--enable-multivalue','-o',opt]);w.tool('wasm-validate',[opt,'--enable-all'])
        build.append(dict(file=opt.name,milliseconds=(time.perf_counter()-t)*1000,bytes=opt.stat().st_size));files.append(opt.name)
    dump(out/'build.json',build);dump(out/'fixtures.json',metadata)
    request=dict(directory=str(out.resolve()),files=files,inputs=inputs);dump(out/'request.json',request)
    cp=subprocess.run(['node',str(HERE/'node.cjs'),str(out/'request.json')],capture_output=True,text=True,timeout=60);dump(out/'node-process.json',dict(code=cp.returncode,stderr=cp.stderr));cp.check_returncode();node=json.loads(cp.stdout);dump(out/'node.json',node)
    sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'));import wasmtime as wt
    engine_runs=[('node',node)];checks=[];programs={};errors=[]
    for det in (False,True):
        cfg=wt.Config();cfg.wasm_relaxed_simd=True;cfg.wasm_relaxed_simd_deterministic=det;engine=wt.Engine(cfg);rows=[]
        for file in files:
            store=wt.Store(engine)
            try:run=wt.Instance(store,wt.Module(engine,(out/file).read_bytes()),[]).exports(store)['run']
            except Exception as e:rows.append(dict(file=file,status='compile-error',error=str(e)));continue
            for ins in inputs:
                t=time.perf_counter()
                try:
                    values=run(store,*ins);values=values if isinstance(values,list) else [values]
                    rows.append(dict(file=file,inputs=ins,outputs=[x&0xffffffff for x in values],status='ok',milliseconds=(time.perf_counter()-t)*1000))
                except Exception as e:rows.append(dict(file=file,inputs=ins,status='trap',error=str(e)))
        label='wasmtime-det' if det else 'wasmtime';data=dict(engine=importlib.metadata.version('wasmtime'),deterministic=det,rows=rows);dump(out/(label+'.json'),data);engine_runs.append((label,data))
    for file in files:
        try:programs[file]=Program(out/file)
        except Unsupported as e:errors.append(dict(file=file,status='unsupported',reason=str(e)))
    for label,data in engine_runs:
        for r in data['rows']:
            if r['status']!='ok':continue
            # Optimized outputs must be legal for the ORIGINAL input program.
            src=r['file'].replace('-O3.wasm','.wasm');p=programs[src]
            verdict=p.check(r['inputs'],r['outputs'])
            checks.append(dict(engine=label,file=r['file'],inputs=r['inputs'],**verdict))
    dump(out/'checks.json',checks);dump(out/'unsupported.json',errors)
    # Controlled traces have independently known expected labels.
    controls=[
        ('nan-share',[1,0],[0x7fc00001,0x7fc00002],False,'copy-corruption'),
        ('nan-share',[1,0],[0xffc12345,0xffc12345],True,'legal-payload'),
        ('nan-independent',[1,0],[0x7fc00001,0x7fc00002],True,'fresh-choices'),
        ('nan-independent',[0,0],[0x7fc00000,0xffc00000],True,'independent-sign'),
        ('nan-independent',[0,0],[0x7fc00001,0x7fc00000],False,'noncanonical-from-canonical'),
        ('nan-neg-copy',[1,0],[0x7fc00001,0xffc00001],True,'exact-negation'),
        ('nan-neg-copy',[1,0],[0x7fc00001,0xffc00002],False,'negation-corruption'),
    ]
    # Concrete scalar swizzle outputs for two full vectors, with input mask 0.
    a=[0x12345678,0xaabbccdd,0x547698ba,0x11223344];b=[0x87654321,0xddccbbaa,0xabcdef12,0x55667788]
    controls.extend([('swizzle-0',[1,0],a+b,True,'common-profile-1'),('swizzle-0',[1,0],[0]*8,True,'common-profile-0'),('swizzle-0',[1,0],a+[0]*4,False,'site-profile-mix'),('swizzle-0',[1,0],[a[0],0,a[2],0]+b,False,'lane-profile-mix')])
    control_rows=[]
    for name,ins,obs,legal,kind in controls:
        for mode in ('joint','pointwise','independent-site','enumerated'):
            v=programs[name+'.wasm'].check(ins,obs,mode)
            control_rows.append(dict(name=name,inputs=ins,outputs=obs,expected_legal=legal,kind=kind,mode=mode,**v))
    dump(out/'controls.json',control_rows)
    # Compare full vs enumerated profiles on measured tuples and controlled ones.
    baseline=[]
    for r in node['rows']:
        if r['status']=='ok' and not '-O3' in r['file']:
            for mode in ('joint','pointwise','independent-site','enumerated'):
                baseline.append(dict(file=r['file'],inputs=r['inputs'],mode=mode,**programs[r['file']].check(r['inputs'],r['outputs'],mode)))
    dump(out/'baselines.json',baseline)
    summary=dict(files=len(files),engine_invocations={k:dict(collections.Counter(r['status'] for r in d['rows'])) for k,d in engine_runs},oracle_checks=dict(collections.Counter(r['status'] for r in checks)),unsupported=errors,controls=len(controls),joint_control_errors=sum(r['status']!=('sat' if r['expected_legal'] else 'unsat') for r in control_rows if r['mode']=='joint'),python=platform.python_version(),z3=z.get_version_string())
    dump(out/'summary.json',summary);print(json.dumps(summary))
    dump(out/'manifest.json',{str(f.relative_to(out)):digest(f) for f in out.rglob('*') if f.is_file() and f.name!='manifest.json'})
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);a=ap.parse_args();main(a.out.resolve())
