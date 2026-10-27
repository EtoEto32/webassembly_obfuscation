import json
from pathlib import Path
import re
import sys
import prototype as p


def main(base,out):
    base=Path(base).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);load=lambda f:json.loads(f.read_text())
    cases=load(base/'cases.json');targets=load(base/'manifest.json');rows=[]
    for case in cases:
        name=case['name'];data=bytes(case['initial']);plan=case['plan'];source=out/(name+'-source.wasm');p.q.compile(p.render(data,plan),source)
        if source.read_bytes()!=(base/(name+'-plain-raw.wasm')).read_bytes():raise AssertionError('replay')
        for target in [x for x in targets if x['name']==name and not x.get('negative')]:
            src=base/target['file'];m=p.q.read(src);run=next(e[2][1] for e in m[1:] if e[:2]==['export','"run"'])
            expects=[]
            for probe,query in enumerate((0,7,31,65535)):
                args=[0]*(3*len(plan)+1);mem=bytearray(65536);mem[:4096]=data
                for step,(d,s,l) in enumerate(plan):
                    dst=(step*7)%32;source_index=(step*11)%32;length=48
                    args[d]=dst;args[s]=source_index;args[l]=length
                    mem[dst:dst+length]=mem[source_index:source_index+length]
                args[-1]=query;expects.append(mem[query])
                m.append(['func',['export','"probe%d"'%probe],['result','i32'],['call',run,*[['i32.const',str(v)] for v in args]]])
            dst=out/(Path(target['file']).stem+'-probe.wasm');p.q.compile(p.q.w.emit(m),dst)
            stdout=p.q.w.tool('wasm-interp',[dst,'--run-all-exports']);actual=[int(x) for x in re.findall(r'probe\d+\(\) => i32:(\d+)',stdout)]
            if actual!=expects:raise AssertionError((target['file'],actual,expects,stdout))
            rows.append(dict(file=target['file'],values=actual))
    controls=[];case=cases[0]
    for name,text in [('exported-memory',p.render(bytes(case['initial']),case['plan'],'pullback')[:-1]+'(export "memory" (memory 0)))'),('missing-bounds',p.render(bytes(case['initial']),case['plan'],'pullback',False))]:
        src=out/(name+'.wasm');p.q.compile(text,src)
        try:p.extract(src)
        except ValueError as ex:controls.append(dict(name=name,status='rejected',reason=str(ex)))
        else:raise AssertionError('invalid accepted')
    p.q.save(out/'audit.json',dict(wabt_calls=4*len(rows),rows=rows,controls=controls));print(json.dumps(dict(wabt_calls=4*len(rows),rejected=len(controls))))


if __name__=='__main__':main(*sys.argv[1:])
