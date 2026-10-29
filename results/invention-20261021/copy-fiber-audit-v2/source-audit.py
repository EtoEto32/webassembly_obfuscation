import hashlib,itertools,json,random,re,subprocess,sys
from pathlib import Path
import prototype as p
import recover as rr

def value_g(x,gs,width=32,linear=False,inverse=False):
    mask=(1<<width)-1;x=list(x)
    def rol(x,n):n%=width;return ((x<<n)|(x>>((-n)%width)))&mask
    for i,j,k,r,s in reversed(gs) if inverse else gs:
        z=(rol(x[j],r)^rol(x[k],s)) if linear else (rol((x[j]+x[k])&mask,r)^(x[j]&rol(x[k],s)))
        x[i]^=z
    return x
def encode(h,w,gs,width=32):return [a^b for a,b in zip(h,value_g([a^b for a,b in zip(h,w)],gs,width))]
def model():
    small=[(0,1,2,1,1),(1,2,0,1,1),(2,0,1,1,1)];values=list(itertools.product(range(4),repeat=3));n=0
    for h in values:
        for w in values:
            y=encode(h,w,small,2);decoded=[a^b for a,b in zip(h,value_g([a^b for a,b in zip(h,y)],small,2,inverse=True))]
            assert decoded==list(w) and encode(h,h,small,2)==list(h);n+=1
    rng=random.Random(211055);gs=p.gates(1);witness=None
    for _ in range(100):
        a=[rng.getrandbits(32) for _ in range(8)];b=[rng.getrandbits(32) for _ in range(8)];ab=[x^y for x,y in zip(a,b)]
        left=value_g(ab,gs);right=[x^y for x,y in zip(value_g(a,gs),value_g(b,gs))]
        assert value_g(value_g(a,gs),gs,inverse=True)==a
        if left!=right and witness is None:witness={'a':a,'b':b,'g_xor':left,'xor_g':right}
    assert witness
    return {'small_width':2,'small_words':3,'exhaustive_state_pairs':n,'random_inverse_checks':100,'nonlinear_witness':witness}
def body(f):return [x for x in f[1:] if x[0] not in ('type','param','result','local')]
def negative(main,out):
    rows=[];original=next(x for x in json.loads((main/'targets.json').read_text()) if x['label']=='fiber1-raw')
    for kind in ('nonzero_at_zero','inverse_order'):
        m=p.q.read(original['path']);fs=[x for x in m[1:] if x[0]=='func']
        for ix in range(1,17):
            f=fs[ix];b=body(f);decl=[x for x in f[1:] if x[0] in ('type','param','result','local')]
            if kind=='nonzero_at_zero':
                b[0][2]=p.xor(b[0][2],p.c(1))
                if ix>=9:
                    for x in b:
                        if x[0]=='i32.store' and p.addr(x[1])==32:x[2]=p.xor(x[2],p.c(1))
            else:b[8:16]=reversed(b[8:16])
            f[:]=['func',*decl,*b]
        raw=out/(kind+'-raw.wasm');p.q.compile(p.q.w.emit(m),raw)
        for opt in ('raw','O3'):
            f=raw if opt=='raw' else out/(kind+'-O3.wasm')
            if opt=='O3':p.q.tool('wasm-opt',[raw,'-O3','--enable-bulk-memory','--enable-multivalue','-o',f]);p.q.w.tool('wasm-validate',[f])
            js="const c=require(process.argv[1]);const e=c.instantiate(process.argv[2]);const x=Array.from({length:24},(_,i)=>i*1234567);const actual=e.compress(...x).map(x=>x>>>0),expected=c.reference(x.slice(0,8),x.slice(8));console.log(JSON.stringify({actual,expected,mismatch:JSON.stringify(actual)!==JSON.stringify(expected)}));"
            result=json.loads(subprocess.check_output(['node','-e',js,str(Path(__file__).with_name('check.cjs').resolve()),str(f)],text=True));assert result['mismatch'];rows.append({'kind':kind,'opt':opt,**result})
    return rows
def rejects(main,out):
    rows=[]
    for kind in ('memory_export','short_copy','mutable_anchor'):
        m=p.q.read(main/'source.wasm');f=next(e for e in m[1:] if e[0]=='func');b=body(f)
        if kind=='memory_export':m.append(['export','"memory"',['memory','0']])
        elif kind=='short_copy':b[8][3]=p.c(28)
        else:f.insert(len(f)-8,p.store(0,p.c(1)))
        src=out/(kind+'.wasm');p.q.compile(p.q.w.emit(m),src)
        try:p.transform(src,out/(kind+'-invalid.wasm'))
        except ValueError as e:rows.append({'kind':kind,'validation':'valid Wasm','rejected':str(e)})
        else:raise AssertionError('accepted '+kind)
    return rows
def engine_probe(src,dst):
    m=p.q.read(src);fs=[e for e in m[1:] if e[0]=='func'];ix=next(int(e[2][1]) for e in m[1:] if e[0]=='export')
    f=['func',['result','i32'],['local',*(['i32']*8)],['call',str(ix),*[p.c(i*1234567) for i in range(24)]],*([['local.set',str(i)] for i in reversed(range(8))]),p.xor(*[p.get(i) for i in range(8)])]
    m.extend([f,['export','"probe"',['func',str(len(fs))]]]);p.q.compile(p.q.w.emit(m),dst)
    log=p.q.w.tool('wasm-interp',[dst,'--run-all-exports']);match=re.search(r'probe\(\) => i32:(\d+)',log)
    if not match:raise AssertionError(log)
    js="const c=require(process.argv[1]);const x=Array.from({length:24},(_,i)=>i*1234567);console.log(c.reference(x.slice(0,8),x.slice(8)).reduce((a,b)=>a^b,0)>>>0);"
    expected=int(subprocess.check_output(['node','-e',js,str(Path(__file__).with_name('check.cjs').resolve())],text=True));assert int(match[1])==expected
    return {'file':str(src),'result':int(match[1]),'expected':expected,'log':log}
def main(main,rec,out):
    main=Path(main).resolve();rec=Path(rec).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    result={'model':model(),'negative_controls':negative(main,out),'rejections':rejects(main,out)}
    rows=json.loads((main/'targets.json').read_text());result['byte_reproduction']=[]
    for t in rows:
        dst=out/(t['label']+'-replay.wasm')
        if t['opt']=='raw':
            if t['kind']=='plain':p.q.compile(p.source(),dst)
            else:p.transform(main/'source.wasm',dst,t['info']['mode'],t['info']['layers'],t['info']['seed'],t['info']['linear'])
        else:
            raw=out/(t['kind']+'-raw-replay.wasm');p.q.tool('wasm-opt',[raw,'-O3','--enable-bulk-memory','--enable-multivalue','-o',dst]);p.q.w.tool('wasm-validate',[dst])
        assert p.q.digest(dst)==t['sha256'];result['byte_reproduction'].append({'label':t['label'],'match':True})
    rrows=json.loads((rec/'recovery.json').read_text());assert len(set(r['output_sha256'] for r in rrows))==1
    result['all_recovered_byte_identical']=True;result['all_fingerprints_identical']=len({tuple(r['output_fingerprints']) for r in rrows})==1;assert result['all_fingerprints_identical']
    result['engines']=[]
    probes=[(x['label'],x['path']) for x in rows if x['opt']=='O3']+[('recovered',str(rec/'fiber1-O3-recovered-O3.wasm'))]
    for label,f in probes:result['engines'].append(engine_probe(f,out/(label+'-interpreter.wasm')))
    files=list(Path(__file__).parent.glob('*.py'))+list(Path(__file__).parent.glob('*.cjs'))
    for folder in (main,rec):files.extend(x for x in folder.iterdir() if x.suffix in ('.json','.wasm'))
    result['pins']=[{'file':str(f.resolve().relative_to(p.ROOT)),'sha256':p.q.digest(f)} for f in files]
    (out/'audit.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:len(result[k]) for k in ('negative_controls','rejections','byte_reproduction','engines','pins')}))
if __name__=='__main__':main(*sys.argv[1:])
