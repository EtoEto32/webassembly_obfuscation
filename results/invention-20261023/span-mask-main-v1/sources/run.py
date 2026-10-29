# -*- coding: utf-8 -*-
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import prototype as p
import attack


def write(path,value):Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')


def join(op,trees):
    if len(trees)==1:return trees[0]
    at=len(trees)//2
    return (op,join(op,trees[:at]),join(op,trees[at:]))


def fixtures():
    v=lambda i:('var',i)
    neg=lambda i:('xor',v(i),('const',p.MASK))
    nested=join('or',[join('and',[join('or',[v(i),v(i+1)]),v(i+2)]) for i in range(0,12,3)])
    cnf=join('and',[('or',v(i),v(i+1)) for i in range(0,16,2)])
    repeated=join('and',[join('or',[v(i),neg((i+1)%12),v(i+12)]) for i in range(12)])
    return {'nested12':{'n':12,'tree':nested},'cnf16':{'n':16,'tree':cnf},'policy24':{'n':24,'tree':repeated}}


def main(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
    for name in ('prototype.py','attack.py','run.py','check.cjs','plan.md'):
        shutil.copyfile(p.HERE/name,out/'sources'/name)
    for name in ('prototype.py','recover.py'):
        shutil.copyfile(p.HERE.parent/'connectivity-elimination'/name,out/'sources'/('shared-'+name))
    manifest={'fixtures':fixtures(),'targets':[],'transforms':[],'recoveries':[],'negative':[],'rejections':[]}
    for name,f in manifest['fixtures'].items():
        sub=out/name;sub.mkdir();plain=sub/'plain.wasm'
        p.save(p.w.plain_wat(f['n'],'"run"',f['tree']),plain)
        b=attack.BDD();root=attack.source_root(f['tree'],b)
        f['bdd_digest']=b.digest(root);f['bdd_nodes']=len(b.nodes);f['output_nodes']=len(attack.reachable(b,root))
        sources={'plain':plain}
        for mode in ('span','constant','dependent'):
            dest=sub/(mode+'.wasm');result=p.transform(plain,dest,mode)
            manifest['transforms'].append({'fixture':name,'mode':mode,**result});sources[mode]=dest
            print(json.dumps({'built':name,'mode':mode,**result}),flush=True)
        for mode,src in sources.items():
            opt=sub/(mode+'-O3.wasm');p.optimize(src,opt)
            for form,path in (('raw',src),('O3',opt)):
                manifest['targets'].append({'fixture':name,'mode':mode,'form':form,'file':str(path.relative_to(out)),'bytes':path.stat().st_size})
        rec,_=p.construct(f['n'],f['tree'],'span')
        # Change a nontrivial column, but deliberately fail to update target.
        bad={**rec,'rows':[sorted(p.column_add(dict(r),0,rec['d']-1,0).items()) for r in rec['rows']]}
        badfile=sub/'bad-target.wasm';p.save(p.render(bad),badfile)
        manifest['negative'].append({'fixture':name,'file':str(badfile.relative_to(out))})
    write(out/'manifest.json',manifest)
    check=subprocess.run(['node',str(p.HERE/'check.cjs'),str(out)],capture_output=True,text=True,timeout=120)
    (out/'initial-check.stdout.txt').write_text(check.stdout,encoding='utf8')
    (out/'initial-check.stderr.txt').write_text(check.stderr,encoding='utf8')
    if check.returncode:raise RuntimeError(check.stderr)
    print(check.stdout,flush=True)
    originals=list(manifest['targets'])
    for target in originals:
        if target['mode']=='plain':continue
        src=out/target['file']
        for method in ('direct','coefficient'):
            dest=src.with_stem(src.stem+'-'+method+'-recovered')
            result=attack.recover(src,dest,method)
            entry={**target,'method':method,**result}
            if result['status']=='recovered':
                if result['bdd_digest']!=manifest['fixtures'][target['fixture']]['bdd_digest']:
                    raise AssertionError('Source/recovered BDD mismatch')
                entry['source_bdd_equal']=True
                manifest['targets'].append({**target,'mode':target['mode']+'-'+method+'-recovered','file':str(dest.relative_to(out)),'bytes':dest.stat().st_size})
            manifest['recoveries'].append(entry)
            write(out/'manifest.json',manifest)
            print(json.dumps(entry),flush=True)
    unsupported=out/'unsupported.wasm'
    p.save('(module (func (export "run") (param i32) (result i32) (i32.div_s (local.get 0) (i32.const 0))))',unsupported)
    try:p.transform(unsupported,out/'must-not-exist.wasm','dependent')
    except ValueError as e:manifest['rejections'].append({'case':'trapping-source','reason':str(e)})
    else:raise AssertionError('Accepted div')
    # Kernel spoofing must not be treated as protected.
    rec,_=p.construct(4,('and',('var',0),('var',1)),'dependent')
    forged=out/'forged.wasm';p.save(p.render(rec).replace('(i32.xor (local.get $v) (i32.const -1))))','(i32.xor (local.get $v) (i32.const 0))))'),forged)
    try:attack.read(forged)
    except ValueError as e:manifest['rejections'].append({'case':'forged-evaluator','reason':str(e)})
    else:raise AssertionError('Accepted forged kernel')
    write(out/'manifest.json',manifest)
    check=subprocess.run(['node',str(p.HERE/'check.cjs'),str(out)],capture_output=True,text=True,timeout=120)
    (out/'final-check.stdout.txt').write_text(check.stdout,encoding='utf8')
    (out/'final-check.stderr.txt').write_text(check.stderr,encoding='utf8')
    if check.returncode:raise RuntimeError(check.stderr)
    write(out/'sha256.json',{str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(out.rglob('*')) if f.is_file()})
    print(check.stdout,flush=True)


if __name__=='__main__':main(sys.argv[1])
