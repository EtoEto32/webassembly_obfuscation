"""Build comparison artifacts and attach recovered helpers to the full hash."""
import copy,json,subprocess,sys,time
from pathlib import Path
import recover as p
q=p.q;ROOT=Path(__file__).resolve().parents[2]
isolated,rawrec,optrec,out=map(Path,sys.argv[1:]);out.mkdir(parents=True,exist_ok=False);rows=[]
plain='''(module (func (export "run") (param i32 i32 i32) (result i32)
 (i32.add (i32.xor (i32.xor (i32.rotr (local.get 0) (i32.const 2)) (i32.rotr (local.get 0) (i32.const 13))) (i32.rotr (local.get 0) (i32.const 22)))
 (i32.or (i32.and (local.get 0) (local.get 1)) (i32.and (local.get 2) (i32.or (local.get 0) (local.get 1)))))))'''
for opt,rec in [('raw',rawrec),('O3',optrec)]:
    for mode in ('original','certified','recovered-state','recovered-io','plain'):
        f=out/f'{mode}-{opt}.wasm';start=time.perf_counter()
        if mode=='plain':q.compile(plain,f)
        else:
            src=isolated/f'isolated-{opt}.wasm' if mode=='original' else rec/(mode+'.wasm')
            q.compile(q.w.emit(q.read(src)),f)
        if opt=='O3' and mode!='original':q.tool('wasm-opt',[f,'--enable-bulk-memory','-O3','-o',f])
        rows.append(dict(mode=mode,opt=opt,file=f.name,sha256=q.digest(f),bytes=f.stat().st_size,prepare_ms=(time.perf_counter()-start)*1000,state=mode in ('original','certified','recovered-state')))
q.save(out/'manifest.json',rows)
full=q.read(ROOT/'experiments/sha256-fixedpoint/artifacts/fixedpoint.wasm')
index=int(next(x[2][1] for x in full[1:] if x[:2]==['export','"t2"']));funcs=[x for x in full[1:] if x[0]=='func'];field=full.index(funcs[index]);fullrows=[]
for mode in ('original','certified','recovered-state'):
    raw=out/f'hash-{mode}-raw.wasm'
    module=copy.deepcopy(full)
    if mode!='original':
        f=next(x for x in q.read(rawrec/(mode+'.wasm'))[1:] if x[0]=='func');f=[x for x in f if not isinstance(x,list) or x[0]!='type'];module[field]=f
    q.compile(q.w.emit(module),raw)
    for opt in ('raw','O3'):
        target=raw if opt=='raw' else out/f'hash-{mode}-O3.wasm'
        if opt=='O3':q.tool('wasm-opt',[raw,'--enable-bulk-memory','-O3','-o',target])
        fullrows.append(dict(mode=mode,opt=opt,file=target.name,sha256=q.digest(target),bytes=target.stat().st_size))
q.save(out/'full-manifest.json',fullrows)
info=json.loads((rawrec/'recovery.json').read_text());q.save(out/'extracted.json',info)
subprocess.run(['node',str(Path(__file__).with_name('check.cjs')),str(out)],check=True,timeout=180)
print(json.dumps(dict(local_targets=len(rows),hash_targets=len(fullrows))))
