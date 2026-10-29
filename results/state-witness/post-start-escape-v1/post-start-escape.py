"""Internal function references escaping through start imports/global/table."""
import argparse,hashlib,importlib.util,json,shutil,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('post_start',HERE/'post-start.py');p=importlib.util.module_from_spec(s);s.loader.exec_module(p);wt=p.wt

def main(out):
    out.mkdir(parents=True,exist_ok=False);rows=[];engine=wt.Engine()
    for kind in ('start-import','global','table'):
        head='(import "env" "capture" (func $capture (param funcref)))' if kind=='start-import' else ''
        body='(elem declare func $reader) (func $start (call $capture (ref.func $reader))) (start $start)' if kind=='start-import' else '(global (export "handle") funcref (ref.func $reader))' if kind=='global' else '(table (export "handle") 1 funcref (ref.func $reader))'
        wat=f'(module {head} (memory (export "memory") 1) (data $d "A") (func $reader (memory.init $d (i32.const 0) (i32.const 0) (i32.const 1))) (func (export "retire") (data.drop $d)) (func (export "entry")) {body})'
        raw=out/(kind+'.wasm');raw.write_bytes(wt.wat2wasm(wat));(out/(kind+'.wat')).write_text(wat);found=p.scan(raw);graph=found['postInstantiation']
        assert not graph['allLifetimeDifferencesIrrelevant'];roots={e['index'] for e in found['exports'] if e['kind']=='Func'};todo=list(roots)
        while todo:
            for target in graph['callsByFunction'].get(str(todo.pop()),[]):
                if target not in roots:roots.add(target);todo.append(target)
        export_only_safe=not any(int(index) in roots for index in graph['allSegmentReaders']);assert export_only_safe
        results=[]
        for drop in (False,True):
            with wt.Store(engine) as store:
                captured=[];imports=[wt.Func(store,wt.FuncType([wt.ValType.funcref()],[]),lambda f:captured.append(f))] if kind=='start-import' else []
                ex=wt.Instance(store,wt.Module(engine,raw.read_bytes()),imports).exports(store)
                if drop:ex['retire'](store)
                before=bytes(ex['memory'].read(store)).hex()
                f=captured[0] if kind=='start-import' else ex['handle'].value(store) if kind=='global' else ex['handle'].get(store,0)
                try:f(store);outcome='return'
                except wt.Trap:outcome='trap'
                results.append({'outcome':outcome,'beforeSha256':hashlib.sha256(bytes.fromhex(before)).hexdigest(),'firstByte':ex['memory'].read(store,0,1)[0]})
        assert results[0]['beforeSha256']==results[1]['beforeSha256'];assert results[0]['outcome']=='return' and results[1]['outcome']=='trap'
        rows.append({'kind':kind,'source':raw.name,'scan':found,'exportOnlyMutantSaysSafe':export_only_safe,'results':results})
    (out/'manifest.json').write_text(json.dumps({'rows':rows,'pairsPerEngine':len(rows),'executableSha256':p.digest(p.EXE)},indent=2))
    node=subprocess.run(['node',str(HERE/'post-start-escape.mjs'),str(out.resolve())],capture_output=True,text=True,encoding='utf8',timeout=30)
    (out/'node-log.json').write_text(json.dumps({'code':node.returncode,'stdout':node.stdout,'stderr':node.stderr},indent=2));assert node.returncode==0,node.stderr
    for name in ('post-start-escape.py','post-start-escape.mjs','post-start.py','post-start-plan.md','post-start-proof.md'):shutil.copy2(HERE/name,out/name)
    for name in ('src/main.rs','Cargo.toml','Cargo.lock'):shutil.copy2(HERE/'census-native'/name,out/Path(name).name)
    (out/'sha256.json').write_text(json.dumps({f.name:p.digest(f) for f in out.iterdir()},indent=2));print(node.stdout)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('out',type=Path);main(a.parse_args().out)
