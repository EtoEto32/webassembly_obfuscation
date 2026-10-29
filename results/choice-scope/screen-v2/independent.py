"""Concrete Python oracle for the FIXTURE families, independent of SMT/AST.

Not a general binary interpreter. Exact set membership for these fixtures only.
"""
import argparse,collections,hashlib,itertools,json,random,shutil,subprocess,time
from pathlib import Path
from oracle import Program,ROOT,w,Unsupported
HERE=Path(__file__).resolve().parent
U=(1<<32)-1
def words(v):return [(v>>(32*i))&U for i in range(4)]
def big(ws):return sum(w<<(32*i) for i,w in enumerate(ws))
def integer_results(name,inputs):
    base,seed=name.split('-');seed=int(seed);y=inputs[1]
    aa=[0x12345678^(seed*0x01010101),0xaabbccdd,0x547698ba,0x11223344];bb=[0x87654321,0xddccbbaa,0xabcdef12,0x55667788]
    result=[]
    for profile in ((0,1) if base in ('swizzle','lane8') else (0,1,2)):
        if base=='swizzle':
            def sw(a,ix):
                ab=big(a).to_bytes(16,'little')
                return words(int.from_bytes(bytes(ab[j%16] if j<16 or (j<128 and profile) else 0 for j in ix),'little'))
            result.append(sw(aa,list(range(16,32)))+sw(bb,bytes(i^j for i,j in zip(bytes(range(16,32)),big([y]*4).to_bytes(16,'little')))))
        else:
            bits=8 if profile==2 else int(base[4:]);mask=(1<<bits)-1;a=big(aa);b=big(bb);out=[]
            for full in (big([y]*4),big([y^U]*4)):
                v=0
                for offset in range(0,128,bits):
                    x=(a>>offset)&mask;yy=(b>>offset)&mask;m=(full>>offset)&mask
                    r=(x if m>>(bits-1) else yy) if profile else ((x&m)|(yy&(~m&mask)))
                    v|=r<<offset
                out+=words(v)
            result.append(out)
    return result
def nan_valid(value,x):
    canonical=x&0x003fffff==0
    return value&0x7fffffff==0x7fc00000 if canonical else value&0x7fc00000==0x7fc00000
def allowed(name,inputs,values):
    if name.startswith(('lane','swizzle')):return values in integer_results(name,inputs)
    if name=='nan-independent':return len(values)==2 and all(nan_valid(v,inputs[0]) for v in values)
    if name=='nan-share':return len(values)==2 and values[0]==values[1] and nan_valid(values[0],inputs[0])
    if name=='nan-neg-copy':return len(values)==2 and values[0]^0x80000000==values[1] and nan_valid(values[0],inputs[0])
    if name=='mixed-share-swizzle':return len(values)==6 and values[0]==values[1] and nan_valid(values[0],inputs[0]) and values[2:] in ([0]*4,[values[0]]*4)
    raise ValueError(name)
def legal_samples(name,inputs):
    if name.startswith(('lane','swizzle')):return integer_results(name,inputs)
    a=0x7fc00000 if inputs[0]&0x003fffff==0 else 0x7fc12345;b=0x80000000|a
    if name=='nan-independent':return [[a,b],[b,a]]
    if name=='nan-share':return [[a,a],[b,b]]
    if name=='nan-neg-copy':return [[a,b],[b,a]]
    return [[a,a]+[0]*4,[a,a]+[a]*4,[b,b]+[0]*4,[b,b]+[b]*4]
def main(source,out):
    out.mkdir(parents=True,exist_ok=False)
    for f in ('oracle.py','independent.py','fixtures.py'):shutil.copy2(HERE/f,out/f)
    req=json.loads((source/'request.json').read_text());files=[x for x in req['files'] if not '-O3' in x];programs={f:Program(source/f) for f in files};rng=random.Random(261026);rows=[];actual=[]
    for engine in ('node','wasmtime','wasmtime-det'):
        for r in json.loads((source/(engine+'.json')).read_text())['rows']:
            if r['status']=='ok':actual.append(dict(engine=engine,file=r['file'],inputs=r['inputs'],legal=allowed(r['file'].replace('-O3','')[:-5],r['inputs'],r['outputs'])))
    shell="""var q=JSON.parse(read(scriptArgs[0]));var rows=[];for(var f of q.files){var e;try{e=new WebAssembly.Instance(new WebAssembly.Module(read(q.directory+'/'+f,'binary'))).exports;}catch(x){rows.push({file:f,status:'compile-error',error:String(x)});continue;}for(var a of q.inputs){try{var r=e.run(...a);rows.push({file:f,inputs:a,outputs:(Array.isArray(r)?r:[r]).map(x=>x>>>0),status:'ok'});}catch(x){rows.push({file:f,inputs:a,status:'trap',error:String(x)});}}}print(JSON.stringify({engine:'SpiderMonkey150.0.1',build:getBuildConfiguration(),rows:rows}));"""
    (out/'shell.js').write_text(shell)
    cp=subprocess.run([str(ROOT/'.tools/spidermonkey-150.0.1/js.exe'),str(out/'shell.js'),str(source/'request.json')],capture_output=True,text=True,timeout=60)
    (out/'spidermonkey-process.json').write_text(json.dumps(dict(code=cp.returncode,stderr=cp.stderr)))
    sm=json.loads(cp.stdout) if cp.returncode==0 else {'rows':[]};(out/'spidermonkey.json').write_text(json.dumps(sm,indent=2))
    for r in sm['rows']:
        if r['status']=='ok':
            src=r['file'].replace('-O3','');actual.append(dict(engine='spidermonkey',file=r['file'],inputs=r['inputs'],legal=allowed(src[:-5],r['inputs'],r['outputs']),smt=programs[src].check(r['inputs'],r['outputs'])))
    for file in files:
        name=file[:-5]
        for ins in req['inputs']:
            for original in legal_samples(name,ins):
                bad=original.copy();k=rng.randrange(len(bad));bad[k]^=1<<rng.randrange(32)
                for kind,obs in [('legal',original),('mutated',bad)]:
                    expected=allowed(name,ins,obs)
                    for mode in ('joint','pointwise','independent-site','enumerated'):
                        v=programs[file].check(ins,obs,mode)
                        rows.append(dict(file=file,inputs=ins,outputs=obs,kind=kind,expected_legal=expected,mode=mode,**v))
    unsupported=[]
    tests={'memory':'(module (memory 1) (func (export "run") (result i32) (i32.const 0)))',
           'after-return':'(module (func (export "run") (result i32) (return (i32.const 0)) (unreachable)))',
           'i16-laneselect':'(module (func (export "run") (result i32) (i32x4.extract_lane 0 (i16x8.relaxed_laneselect (v128.const i32x4 0 0 0 0) (v128.const i32x4 0 0 0 0) (v128.const i32x4 0 0 0 0)))))'}
    for name,wat in tests.items():
        src=out/(name+'.wat');src.write_text(wat);dst=src.with_suffix('.wasm');w.tool('wat2wasm',[src,'--enable-all','-o',dst])
        try:Program(dst);status='unexpected-supported'
        except Unsupported as e:status='unsupported: '+str(e)
        unsupported.append(dict(name=name,status=status))
    report=dict(actual_executions=len(actual),concrete_actual_failures=sum(not r['legal'] for r in actual),spidermonkey_statuses=dict(collections.Counter(r['status'] for r in sm['rows'])),smt_actual_failures=sum(r.get('smt',{}).get('status','sat')!='sat' for r in actual),traces=len(rows)//4,
                exact_mode_disagreements=sum(r['status']!=('sat' if r['expected_legal'] else 'unsat') for r in rows if r['mode'] in ('joint','enumerated')),unsupported=unsupported)
    for name,obj in [('actual.json',actual),('traces.json',rows),('summary.json',report)]: (out/name).write_text(json.dumps(obj,indent=2))
    (out/'manifest.json').write_text(json.dumps({str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest() for f in out.rglob('*') if f.is_file() and f.name!='manifest.json'},indent=2));print(json.dumps(report))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('out',type=Path);a=ap.parse_args();main(a.source.resolve(),a.out.resolve())
