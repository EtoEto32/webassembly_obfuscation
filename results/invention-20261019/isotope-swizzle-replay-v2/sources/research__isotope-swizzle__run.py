import argparse,json,platform,random,shutil,subprocess
from pathlib import Path
import prototype as q
HERE=Path(__file__).resolve().parent
MODELS={'add':('add',0,1),'xor':('xor',0,1),'mixed':('sub',('add',0,1),('xor',2,('sub',1,0)))}
def count(t):return 0 if isinstance(t,int) else 1+count(t[1])+count(t[2])
def snapshot(out):
    dst=out/'sources';dst.mkdir();ss=[]
    for f in [*HERE.glob('*.py'),*HERE.glob('*.cjs'),HERE/'plan.md',q.ROOT/'research/connectivity-elimination/prototype.py']:
        name=str(f.relative_to(q.ROOT)).replace('\\','__').replace('/','__');shutil.copyfile(f,dst/name);ss.append(dict(path=str(f.relative_to(q.ROOT)),snapshot=name,sha256=q.digest(f)))
    q.save(out/'sources.json',ss)
def negatives(out):
    rows=[]
    tables={'not_latin':[[0]*16 for _ in range(16)],'C4xC4':[[((a%4+b%4)%4)+4*((a//4+b//4)%4) for a in range(16)] for b in range(16)]}
    t=[[a^b for a in range(16)] for b in range(16)]
    for y in (0,1):t[y][0],t[y][1]=t[y][1],t[y][0]
    tables['nonassociative_trade']=t
    for name,t in tables.items():
        try:q.normalize(t)
        except q.Unsupported as e:rows.append(dict(name=name,status='rejected',reason=str(e)))
        else:raise AssertionError(name)
    # All indices 0..255 are legal for swizzle, but the group's rewrite only
    # applies to 0..15. Reject a matching table with unconstrained input.
    t=[[a^b for a in range(16)] for b in range(16)]
    a=['i32x4.splat',['local.get','0']];b=q.masked(['i32x4.splat',['local.get','1']])
    text=q.w.emit(['module',['func',['export','"run"'],['param','i32','i32','i32'],['result','i32'],['i32x4.extract_lane','0',q.table_expr(t,a,b)]]])
    f=out/'out-of-range.wasm';q.compile(text,f)
    try:q.lower(f)
    except q.Unsupported as e:rows.append(dict(name='unproven_range',status='rejected',reason=str(e)))
    else:raise AssertionError('range guard')
    # Validate mathematical recovery independently for many randomized labelings.
    r=random.Random(991);checks=0;groups={}
    for op in ('add','sub','xor'):
        for _ in range(64):
            a=list(range(16));b=a[:];c=a[:];r.shuffle(a);r.shuffle(b);r.shuffle(c)
            t=[[c[q.op_eval(op,a[x],b[y])] for x in range(16)] for y in range(16)];s=q.normalize(t)
            for x in range(16):
                for y in range(16):
                    assert s['output'][q.op_eval(s['op'],s['left'][x],s['right'][y])]==t[y][x];checks+=1
            groups[op]=s['op']
    q.save(out/'negative.json',rows);q.save(out/'algebra.json',dict(random_tables=192,exhaustive_pairs=checks,groups=groups))
def main(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False);snapshot(out);q.save(out/'models.json',MODELS)
    node=json.loads(subprocess.check_output(['node','-e','console.log(JSON.stringify({node:process.version,v8:process.versions.v8,cpu:require("os").cpus()[0].model,logical_cpus:require("os").cpus().length}))'],text=True))
    q.save(out/'environment.json',dict(python=platform.python_version(),os=platform.platform(),binaryen=q.tool('wasm-opt',['--version']).strip(),wabt=q.w.tool('wat2wasm',['--version']).strip(),**node));records=[]
    for kernel,tree in MODELS.items():
        src=out/(kernel+'-source.wasm');q.compile(q.source_text(tree),src)
        for mode,seed in [('plain',0),('decode',7),('decode',29),('table',7),('table',29)]:
            raw=out/f'{kernel}-{mode}-s{seed}-raw.wasm';info=q.transform(src,raw,mode,seed)
            for opt in ('raw','O3'):
                f=raw if opt=='raw' else out/f'{kernel}-{mode}-s{seed}-O3.wasm'
                if opt=='O3':q.tool('wasm-opt',[raw,'--enable-simd','-O3','-o',f])
                rec=out/(f.stem+'-recovered.wasm');a=q.lower(f,rec)
                assert a['tables']==(count(tree) if mode=='table' else 0),(f,a)
                # Confirm no full table mux remains after recovery.
                assert not any(e[0]=='v128.bitselect' for e in q.walk(q.read(rec)))
                records.append(dict(info,kernel=kernel,opt=opt,source=src.name,file=f.name,recovered=rec.name,sha256=q.digest(f),recovered_sha256=q.digest(rec),bytes=f.stat().st_size,recovered_bytes=rec.stat().st_size,analysis=a))
    q.save(out/'manifest.json',records);negatives(out)
    subprocess.run(['node',str(HERE/'check.cjs'),str(out)],check=True,timeout=120)
    summary=dict(targets=len(records),table_targets=sum(r['mode']=='table' for r in records),recovered_tables=sum(r['analysis']['tables'] for r in records),checks=json.loads((out/'checks.json').read_text()),negative=json.loads((out/'negative.json').read_text()),algebra=json.loads((out/'algebra.json').read_text()))
    q.save(out/'summary.json',summary);print(json.dumps({k:v for k,v in summary.items() if k!='checks'}|{k:v for k,v in summary['checks'].items() if k!='records'}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output');main(p.parse_args().output)
