import argparse,hashlib,json,platform,random,shutil,subprocess,time
from pathlib import Path
import prototype as p

def save(f,v):Path(f).write_text(json.dumps(v,indent=2),encoding='utf8')
def pin(out):
    for f in Path(__file__).parent.iterdir():
        if f.suffix in ('.py','.cjs'):shutil.copy2(f,out/('source-'+f.name))
    shutil.copy2(p.w.__file__,out/'source-common.py')
    save(out/'pins.json',{str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest() for f in out.rglob('*') if f.is_file() and f.name!='pins.json'})

def run(output):
    out=Path(output).resolve();out.mkdir(parents=True,exist_ok=False);rows=[];definitions={};analyses=[]
    rng=random.Random(20261022)
    for label,nvars,nclauses,width in [('access',16,8,3),('compat',32,20,4),('features',64,48,5)]:
        planted=[rng.randrange(2) for _ in range(nvars)];clauses=[]
        for _ in range(nclauses):
            vs=rng.sample(range(nvars),width);c=[(v//32,v%32,rng.randrange(2)) for v in vs]
            if not any(planted[v]^x[2] for v,x in zip(vs,c)):c[0]=(c[0][0],c[0][1],1-planted[vs[0]])
            clauses.append(c)
        witness=[sum(planted[i]<<i for i in range(min(nvars,32))),sum(planted[i]<<(i-32) for i in range(32,nvars))]
        definitions[label]=dict(clauses=clauses,witness=witness,variables=nvars)
        src=out/f'{label}.plain.raw.wasm';p.compile(p.source(clauses),src)
        target=out/f'{label}.validator.raw.wasm';stats=p.transform(src,target)
        for mode in ('plain','validator'):
            raw=out/f'{label}.{mode}.raw.wasm';opt=out/f'{label}.{mode}.O3.wasm';p.w.tool('wasm-opt',[raw,'-O3','-o',opt]);p.w.tool('wasm-validate',[opt])
            for version,file in (('raw',raw),('O3',opt)):
                row=dict(name=label,mode=mode,version=version,file=file.name,bytes=file.stat().st_size,**({k:v for k,v in stats.items() if k!='bytes'} if mode=='validator' else {}));rows.append(row)
                if mode=='validator':
                    recovered=out/f'{label}.recovered.{version}.wasm';analysis=p.recover(file,recovered);analyses.append(dict(name=label,version=version,**analysis))
                    rows.append(dict(name=label,mode='recovered',version=version,file=recovered.name,bytes=recovered.stat().st_size))
    save(out/'manifest.json',rows);save(out/'definitions.json',definitions);save(out/'analysis.json',analyses)
    save(out/'environment.json',dict(python=platform.python_version(),platform=platform.platform(),wabt=p.w.tool('wat2wasm',['--version']).strip(),binaryen=p.w.tool('wasm-opt',['--version']).strip()))
    # A reduced family fully enumerates truth assignments to two clauses.
    query_rows=[];qdir=out/'queries';qdir.mkdir()
    for lengths in ([0],[1],[3],[2,2],[3,3],[]):
        template,groups=p.template(lengths);n=sum(lengths)
        for bits in range(1<<n):
            data=bytearray(template);offset=0;want=True
            for g in groups:
                satisfied=False
                for pos in g:
                    bit=(bits>>offset)&1;offset+=1;data[pos]=1-bit;satisfied|=bool(bit)
                want&=satisfied
            f=qdir/f'query-{len(query_rows)}.wasm';f.write_bytes(data);query_rows.append(dict(file=str(f.relative_to(out)),expected=want,lengths=lengths,bits=bits))
    # An explicit i64 operand remains a type error even after unreachable.
    # Function locals + unreachable/i64.const/add/drop/end.
    body=bytes([0,0,0x42,0,0x6a,0x1a,0x0b]);invalid=bytearray(b'\0asm\x01\0\0\0'+bytes([1,4,1,0x60,0,0,3,2,1,0,10])+p.uleb(2+len(body))+bytes([1,len(body)])+body)
    f=qdir/'typed-mismatch.wasm';f.write_bytes(invalid);query_rows.append(dict(file=str(f.relative_to(out)),expected=False,negative='explicit i64 after unreachable'))
    save(out/'queries.json',query_rows)
    for script in ('check.cjs','performance.cjs'):
        r=subprocess.run(['node',str(Path(__file__).with_name(script)),str(out)],capture_output=True,text=True,timeout=240)
        (out/(script+'.stdout.txt')).write_text(r.stdout,encoding='utf8');(out/(script+'.stderr.txt')).write_text(r.stderr,encoding='utf8')
        if r.returncode:raise RuntimeError(script+': '+r.stderr)
        print(r.stdout.strip(),flush=True)
    pin(out)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output');a=ap.parse_args()
    try:run(a.output)
    except Exception as e:
        dest=Path(a.output)
        if dest.exists() and not (dest/'failure.txt').exists():(dest/'failure.txt').write_text(repr(e),encoding='utf8')
        raise
