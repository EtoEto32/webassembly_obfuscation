"""Actual restore inputs for public-only delayed-observation examples."""
import argparse,copy,hashlib,json,shutil,subprocess
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]

def main(source,out,repair_copy=False):
    out.mkdir(parents=True,exist_ok=False);rows=[]
    exes={'migrate':ROOT/'.tools/wasm-migrate-build/target/release/wasm-migrate-target.exe',
          'weave':ROOT/'.tools/weave-build/target/release/weave-probe.exe'}
    for r in json.loads((source/'manifest.json').read_text())['rows']:
        folder=out/r['name'];folder.mkdir();original=folder/'original.wasm';shutil.copy2(source/r['source'],original)
        module=k.p.read(original)
        if repair_copy and r['repair']:
            n=r['length'];module.append(['table',str(n),str(n),'funcref'])
            module.append(k.p.expr('(elem (table 2) (i32.const 0) func '+' '.join(['0']*n)+')'))
            f=k.p.section(module,'func')[6];i=next(i for i,x in enumerate(f) if isinstance(x,list) and x[0]=='table.fill')
            f[i]=k.p.expr(f'(table.copy 1 2 (i32.const 0) (i32.const 0) (i32.const {n}))')
        module.append(['memory','1','1']);module.append(['export','"memory"',['memory','0']])
        adapted=folder/'adapted.wasm';k.p.compile_wat(k.p.w.emit(module),adapted)
        changed=copy.deepcopy(module);f=k.p.section(changed,'func')[2]
        at=next(i for i,x in enumerate(f) if isinstance(x,list) and x==['elem.drop','0'])+1
        f.insert(at,k.p.expr('(loop (br_if 0 (i32.const 0)))'))
        cut=folder/'cut.wasm';k.p.compile_wat(k.p.w.emit(changed),cut)
        variants=[]
        for backend,exe in exes.items():
            dest=folder/(backend+'.wasm');cmd=[str(exe),str(cut),str(dest)]+(['2'] if backend=='migrate' else [])
            try:
                p=subprocess.run(cmd,capture_output=True,text=True,encoding='utf8',timeout=30)
                item={'backend':backend,'code':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'binary':dest.relative_to(out).as_posix()}
                if p.returncode: item['status']='transform-failure'
                else:
                    try:k.p.tool('wasm-validate',[dest]);item['status']='valid'
                    except RuntimeError as e:item.update(status='invalid-output',error=str(e))
            except subprocess.TimeoutExpired:item={'backend':backend,'status':'transform-timeout'}
            variants.append(item)
        rows.append({'name':r['name'],'length':r['length'],'repair':r['repair'],'sequence':r['sequence'],
          'original':original.relative_to(out).as_posix(),'adapted':adapted.relative_to(out).as_posix(),
          'cut':cut.relative_to(out).as_posix(),'variants':variants})
    for n in ('guard-external-generate.py','guard-external-run.mjs','prototype.py'):shutil.copy2(HERE/n,out/n)
    shutil.copy2(ROOT/'.tools/weave-build/js/weave.mjs',out/'weave.mjs')
    (out/'manifest.json').write_text(json.dumps({'rows':rows,'repairByCopy':repair_copy,'source':str(source),'sourceManifestSha256':hashlib.sha256((source/'sha256.json').read_bytes()).hexdigest(),
        'executableSha256':{str(v.relative_to(ROOT)):hashlib.sha256(v.read_bytes()).hexdigest() for v in exes.values()}},indent=2))
    (out/'sha256.json').write_text(json.dumps({p.relative_to(out).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()},indent=2))
    print(json.dumps({'modules':len(rows),'valid':sum(v['status']=='valid' for r in rows for v in r['variants'])}))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('source',type=Path);a.add_argument('out',type=Path);a.add_argument('--repair-copy',action='store_true');v=a.parse_args();main(v.source,v.out,v.repair_copy)
