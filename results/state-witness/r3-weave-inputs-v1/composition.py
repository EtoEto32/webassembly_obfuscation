"""Test full-reference observer composition, without modifying frozen K."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]

def with_getters(module):
    m,meta=k.augment(module,False)
    for i in range(meta['functions']):
        m.append(k.p.expr(f'(func (export "__sw_identity_{i}") (result funcref) (ref.func {i}))'))
    meta['identityProvider']='getter'
    return m,meta

def with_directory(module,directory=True):
    m,meta=k.augment(module,True);meta['profile']='full';meta['referenceAccess']='host-table'
    if meta['memory']:m.append(k.p.expr('(export "__sw_memory" (memory 0))'))
    for t in range(meta['tableCount']):
        suffix='_'+str(t) if t else ''
        m.append(k.p.expr(f'(export "__sw_table{suffix}" (table {t}))'))
    for i in range(meta['functions']):m.append(k.p.expr(f'(export "__sw_func_{i}" (func {i}))'))
    if directory:
        n=meta['functions'];t=meta['tableCount']
        m.append(k.p.expr(f'(table {n} {n} funcref)'))
        m.append(k.p.expr(f'(elem (table {t}) (i32.const 0) func '+ ' '.join(map(str,range(n)))+')'))
        m.append(k.p.expr(f'(export "__sw_directory" (table {t}))'))
    meta['identityProvider']='directory' if directory else 'export'
    return m,meta

def main(out):
    out.mkdir(parents=True,exist_ok=False);rows=[]
    source=out/'source.wasm'
    k.p.compile_wat('''(module (type $t (func (result i32)))
      (memory (export "memory") 1 2) (table 4 8 funcref)
      (func $a (result i32) (i32.const 17)) (func $b (result i32) (i32.const 29))
      (elem (i32.const 0) $a $b $a) (elem $passive func $b $a)
      (func (export "value") (param i32) (result i32) (call_indirect (type $t) (local.get 0)))
      (func (export "_start") (local i32)
        (table.set (i32.const 0) (ref.func $b))
        (loop (local.set 0 (i32.add (local.get 0) (i32.const 1)))
          (br_if 0 (i32.lt_u (local.get 0) (i32.const 3))))
        (table.init $passive (i32.const 1) (i32.const 0) (i32.const 2))
        (elem.drop $passive) (i32.store (i32.const 0) (i32.const 71))))''',source)
    module=k.p.read(source);exe=ROOT/'.tools/weave-build/target/release/weave-probe.exe'
    for mode in ('export','getter','host-export','directory'):
        if mode in ('host-export','directory'):m,meta=with_directory(module,mode=='directory')
        else:m,meta=k.augment(module,False) if mode=='export' else with_getters(module)
        src=out/(mode+'.wasm');k.p.compile_wat(k.p.w.emit(m),src)
        dst=out/(mode+'-woven.wasm')
        r=subprocess.run([str(exe),str(src),str(dst)],capture_output=True,text=True,encoding='utf8',timeout=30)
        row={'mode':mode,'source':src.name,'output':dst.name,'manifest':meta,'code':r.returncode,'stderr':r.stderr}
        if r.returncode==0:k.p.tool('wasm-validate',[dst]);row['status']='valid'
        else:row['status']='transform-failure'
        rows.append(row)
    for name in ('composition.py','composition.mjs','observer.cjs','prototype.py'):shutil.copy2(HERE/name,out/name)
    shutil.copy2(ROOT/'.tools/weave-build/js/weave.mjs',out/'weave.mjs')
    (out/'manifest.json').write_text(json.dumps({'rows':rows,'exeSha256':hashlib.sha256(exe.read_bytes()).hexdigest()},indent=2))
    r=subprocess.run(['node',str(out/'composition.mjs'),str(out.resolve())],capture_output=True,text=True,encoding='utf8',timeout=60)
    (out/'node-log.json').write_text(json.dumps({'code':r.returncode,'stdout':r.stdout,'stderr':r.stderr},indent=2))
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file()},indent=2))
    assert r.returncode==0,r.stderr;print(json.dumps(json.loads(r.stdout),ensure_ascii=True))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('out',type=Path);main(p.parse_args().out)
