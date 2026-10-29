"""WABT interpreter cross-check of selected raw/O3 targets; no new performance."""
import json,sys
from pathlib import Path
import prototype as p
src,out=map(Path,sys.argv[1:]);out.mkdir(parents=True,exist_ok=False);q=p.q
rows=[r for r in json.loads((src/'manifest.json').read_text()) if r['pages']==1 and r['seed']==(0 if r['mode']=='plain' else 7)]
records=[]
for r in rows:
    m=q.read(src/r['file']);ex={x[1].strip('"'):int(x[2][1]) for x in m[1:] if x[0]=='export' and x[2][0]=='func'}
    checksum_index=sum(x[0]=='func' for x in m[1:]);m.append(p.expr(f'''(func (result i32) (local i32 i32)
      (local.set 1 (i32.const 2166136261))
      (block (loop (br_if 1 (i32.eq (local.get 0) (i32.const 128)))
        (local.set 1 (i32.mul (i32.xor (local.get 1) (call {ex['read']} (local.get 0))) (i32.const 16777619)))
        (local.set 0 (i32.add (local.get 0) (i32.const 1))) (br 0))) (local.get 1))'''))
    operations=[('fill',[12345]),('copy',[1,0,33]),('copy',[0,1,65]),('copy',[65535,0,2]),('copy',[0,65535,2]),('copy',[65536,65536,0]),('copy',[65537,0,0]),('splice',[5,33,215]),('markcopy',[65535,0,2,87]),('copy',[0,0,0])]
    expected=[];a=bytearray(65536)
    for i,(name,args) in enumerate(operations):
        m.append(p.expr(f'(func (export "check{i}") (result i32) (call {ex[name]} '+''.join(f'(i32.const {x})' for x in args)+f') (call {checksum_index}))'))
        trap=False
        if name=='fill':
            x=args[0]
            for j in range(65536):x=(x*1664525+1013904223)&0xffffffff;a[j]=x>>24
        elif name=='splice':d,n,v=args;a[d:d+n-1]=a[d+1:d+n];a[d+n-1]=v
        else:
            d,s,n=args[:3]
            if name=='markcopy':a[0]=args[3]
            trap=d+n>65536 or s+n>65536
            if not trap:a[d:d+n]=bytes(a[s:s+n])
        h=2166136261
        for x in a[:128]:h=((h^x)*16777619)&0xffffffff
        expected.append('trap' if trap else h)
    f=out/r['file'];q.compile(q.w.emit(m),f);log=q.w.tool('wasm-interp',[f,'--run-all-exports']);f.with_suffix('.log').write_text(log,encoding='utf-8')
    actual=[]
    for i in range(len(operations)):
        line=next(x for x in log.splitlines() if x.startswith(f'check{i}()'))
        actual.append(int(line.split('i32:')[1]) if '=> i32:' in line else 'trap')
    assert actual==expected,(r['file'],actual,expected)
    records.append(dict(file=r['file'],actual=actual,expected=expected))
q.save(out/'verification.json',dict(targets=len(rows),calls=len(rows)*len(operations),expected_traps=sum(sum(x=='trap' for x in r['actual']) for r in records),mismatches=0,records=records))
print(json.dumps(dict(targets=len(rows),calls=len(rows)*len(operations))))
