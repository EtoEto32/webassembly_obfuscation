import ast
import json
from pathlib import Path
import sys
import recover as r


def main(main_dir,adapt_dir,dest):
    dirs=[Path(main_dir).resolve(),Path(adapt_dir).resolve()];out=Path(dest).resolve();out.mkdir(parents=True,exist_ok=False)
    pins=0;rows=[];replay=[]
    for folder in dirs:
        for item in json.loads((folder/'provenance.json').read_text(encoding='utf-8')):
            if r.p.q.digest(folder/item['file'])!=item['sha256']:raise AssertionError('changed artifact')
            pins+=1
        cases={c['name']:c for c in json.loads((folder/'cases.json').read_text(encoding='utf-8'))}
        manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
        for entry in manifest:
            if entry.get('negative') or (folder==dirs[0] and entry['variant']=='recovered'):continue
            src=folder/entry['file'];m=r.p.q.read(src);c=cases[entry['name']];n=len(c['edges'])
            run=next(int(x[2][1]) for x in m[1:] if x[0]=='export' and x[1]=='"run"')
            probes=[(0,0,0,0),(n,0,0,2),(n-1,1,n-1,2),(0,0,n,1),(0,n-1,1,0xffffffff),(1,0,0,255)]
            extras=[];expected=[];edges=c['edges'][:]
            for i,(u,v,start,steps) in enumerate(probes):
                if u>=n or v>=n or start>=n:expected.append('trap')
                else:
                    edges[u]=v;cur=start;acc=0
                    for _ in range(steps&255):acc=(((acc<<5)|(acc>>27))^c['payload'][cur])&0xffffffff;cur=edges[cur]
                    expected.append(acc)
                args=' '.join('(i32.const %d)'%(x if x<2**31 else x-2**32) for x in (u,v,start,steps))
                extras.append('(func (export "probe%d") (result i32) (call %d %s))'%(i,run,args))
            target=out/(folder.name+'-'+src.name);r.p.q.compile(r.p.q.w.emit(m)[:-1]+' '.join(extras)+')',target)
            log=r.p.q.w.tool('wasm-interp',[target,'--run-all-exports']);target.with_suffix('.log').write_text(log,encoding='utf-8')
            actual=[]
            for line in log.splitlines():
                if not line.startswith('probe'):continue
                if 'error: unreachable executed' in line:actual.append('trap')
                elif 'i32:' in line:actual.append(int(line.split('i32:')[1]))
                else:raise AssertionError(line)
            if actual!=expected:raise AssertionError((src.name,actual,expected))
            rows.append(dict(file=str(src),calls=len(actual),traps=actual.count('trap'),values=actual))
    # Rebuild each source variant using the recorded predecessor, checking the
    # exact bytes independently of the original output directory.
    cased={c['name']:c for c in json.loads((dirs[0]/'cases.json').read_text(encoding='utf-8'))}
    for row in json.loads((dirs[0]/'manifest.json').read_text(encoding='utf-8')):
        if row.get('negative') or row['variant']=='recovered':continue
        original=dirs[0]/(row['name']+'-original-raw.wasm');m=r.p.q.read(original)
        target=out/('replay-'+row['file']);raw=target if row['opt']=='raw' else target.with_name(target.stem+'-before-opt.wasm')
        r.p.q.compile(r.p.q.w.emit(r.b.mutate(m,row['variant'],len(cased[row['name']]['edges']))),raw)
        if row['opt']=='O3':r.p.q.w.tool('wasm-opt',[raw,'--enable-bulk-memory','-O3','-o',target])
        same=target.read_bytes()==(dirs[0]/row['file']).read_bytes()
        if not same:raise AssertionError('replay mismatch')
        replay.append(dict(file=row['file'],byte_identical=same))
    python_files=list(r.HERE.glob('*.py'))
    for f in python_files:ast.parse(f.read_text(encoding='utf-8'))
    result=dict(verified_hashes=pins,interpreter=rows,interpreter_calls=sum(x['calls'] for x in rows),interpreter_traps=sum(x['traps'] for x in rows),mismatches=0,replay=replay,python_syntax=[f.name for f in python_files])
    r.p.q.save(out/'audit.json',result)
    snapshot=out/'sources';snapshot.mkdir()
    for f in python_files:(snapshot/f.name).write_bytes(f.read_bytes())
    r.p.q.save(out/'provenance.json',[dict(file=str(f.relative_to(out)),sha256=r.p.q.digest(f)) for f in sorted(out.rglob('*')) if f.is_file()])
    print(json.dumps({k:result[k] for k in ('verified_hashes','interpreter_calls','interpreter_traps','mismatches')}))


if __name__=='__main__':main(*sys.argv[1:])
