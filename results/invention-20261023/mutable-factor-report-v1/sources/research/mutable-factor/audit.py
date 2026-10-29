import json
from pathlib import Path
import sys
import prototype as p


def main(main_dir,out):
    main_dir=Path(main_dir).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    cases={x['name']:x for x in json.loads((main_dir/'cases.json').read_text())}
    rows=json.loads((main_dir/'manifest.json').read_text());records=[];replay=[];rejects=[]
    for row in rows:
        if row.get('negative') or row.get('diagnostic'):continue
        file=main_dir/row['file'];m=p.q.read(file);c=cases[row['name']];n=len(c['edges'])
        exports={e[1]:int(e[2][1]) for e in m[1:] if e[0]=='export'};run,reset=exports['"run"'],exports['"reset"']
        probes=[(0,0,0,0),(n-1,1,n-1,2),(0,n-1,1,0xffffffff),(1,0,0,255)]
        additions=[];expected=[];edges=c['edges'][:]
        for i,(u,v,start,steps) in enumerate(probes):
            edges[u]=v;cur=start;acc=0
            for _ in range(steps&255):acc=(((acc<<5)|(acc>>27))^c['payload'][cur])&0xffffffff;cur=edges[cur]
            expected.append(acc)
            additions.append('(func (export "probe%d") (result i32) (call %d %s))'%(i,run,' '.join('(i32.const %d)'%x for x in (u,v,start,steps if steps<2**31 else steps-2**32))))
        target=out/file.name;p.q.compile(p.q.w.emit(m)[:-1]+' '.join(additions)+')',target)
        stdout=p.q.w.tool('wasm-interp',[target,'--run-all-exports']);(out/(file.stem+'.log')).write_text(stdout,encoding='utf-8')
        actual=[int(line.split('i32:')[1]) for line in stdout.splitlines() if line.startswith('probe')]
        if actual!=expected:raise AssertionError((row,actual,expected))
        records.append(dict(file=file.name,calls=len(actual),values=actual))
    for c in cases.values():
        f=out/(c['name']+'-source-replay.wasm');p.q.compile(p.render(c['edges'],c['payload']),f)
        same=f.read_bytes()==(main_dir/(c['name']+'-plain-raw.wasm')).read_bytes()
        if not same:raise AssertionError('replay')
        replay.append(dict(file=f.name,byte_identical=same))
    c=next(iter(cases.values()));src=main_dir/(c['name']+'-moving-raw.wasm');e,values,_,perm=p.recognize(src,['moving'])
    for label,text in [('exported-memory',p.render(e,values,'moving',perm,True)),('bad-order',p.render(e,values,'bad-order',perm))]:
        f=out/(label+'.wasm');p.q.compile(text,f)
        try:p.recover(f,out/(label+'-recovered.wasm'))
        except ValueError as ex:rejects.append(dict(label=label,reason=str(ex)))
        else:raise AssertionError('bad input accepted')
    p.q.save(out/'audit.json',dict(interpreter=records,interpreter_calls=sum(x['calls'] for x in records),byte_replay=replay,rejects=rejects))
    print(len(records),sum(x['calls'] for x in records),len(rejects))


if __name__=='__main__':main(*sys.argv[1:])
