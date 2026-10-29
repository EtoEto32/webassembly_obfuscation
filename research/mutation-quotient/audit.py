import json
from pathlib import Path
import re
import subprocess
import sys
import prototype as p


def main(base,out):
    base=Path(base).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    cases=json.loads((base/'cases.json').read_text());targets=json.loads((base/'manifest.json').read_text());replay=[];cross=[];diagnostics=[]
    for c in cases:
        name=c['name'];src=out/(name+'-plain-raw.wasm');p.q.compile(p.render(c['initial'],c['k']),src)
        for mode in ('plain','representative','canonical'):
            raw=out/(name+'-'+mode+'-raw.wasm')
            if mode!='plain':p.transform(src,raw,mode)
            for opt in ('raw','O3'):
                f=out/(name+'-'+mode+'-'+opt+'.wasm')
                if opt=='O3':p.q.w.tool('wasm-opt',[raw,'-O3','-o',f])
                old=base/f.name
                if p.q.digest(old)!=p.q.digest(f):raise AssertionError('replay '+str(f))
                replay.append(f.name)
                if mode!='plain':
                    rec=f.with_name(f.stem+'-recovered.wasm');p.recover(f,rec)
                    if p.q.digest(base/rec.name)!=p.q.digest(rec):raise AssertionError('recovery replay')
                    replay.append(rec.name)
                # Six sequential calls, including an anchor update and alias.
                m=p.q.read(f);run=next(e[2][1] for e in m[1:] if e[:2]==['export','"run"'])
                seq=[(0,0,1,0),(3,0,1,0xffffffff),(2,1,0,0x80000000),(1,0,0,1),(3,1,1,17),(0,1,0,0)]
                model=c['initial'][:];expects=[]
                for z,(op,i,j,d) in enumerate(seq):
                    if op==1:model[i]=(model[i]+d)&p.MASK
                    if op==2:model[i]=(model[j]+d)&p.MASK
                    if op==3:model[i]=(model[i]*c['k']+d)&p.MASK
                    expects.append((model[i]-model[j])&p.MASK)
                    m.append(['func',['export','"probe%d"'%z],['result','i32'],['call',run,*[['i32.const',str(v)] for v in (op,i,j,d)]]])
                probe=out/(f.stem+'-probe.wasm');p.q.compile(p.q.w.emit(m),probe)
                stdout=p.q.w.tool('wasm-interp',[probe,'--run-all-exports']);actual=[int(x)&p.MASK for x in re.findall(r'probe\d+\(\) => i32:(\d+)',stdout)]
                if actual!=expects:raise AssertionError((f,actual,expects,stdout))
                cross.append(dict(file=f.name,values=actual))
                m=p.q.read(f);m.append(['export','"memory"',['memory','0']]);diag=out/(f.stem+'-diagnostic.wasm');p.q.compile(p.q.w.emit(m),diag)
                diagnostics.append(dict(name=name,mode=mode,optimization=opt,file=diag.name))
    p.q.save(out/'cases.json',cases);p.q.save(out/'manifest.json',diagnostics)
    r=subprocess.run(['node',str(p.HERE/'check.cjs'),str(out)],capture_output=True,text=True,timeout=120)
    (out/'checks.stdout.txt').write_text(r.stdout);(out/'checks.stderr.txt').write_text(r.stderr)
    if r.returncode:raise RuntimeError(r.stderr)
    p.q.save(out/'memory-checks.json',json.loads(r.stdout))
    controls=[]
    for name,wat in [
        ('over-erasure',p.render([0,1,2,3],257,1,32)),
        ('wrong-operation',p.render([1,2,3,4],257,2).replace('(i32.mul (i32.const 257)','(i32.add (i32.const 257)')),
        ('exported-memory',p.render([1,2,3,4],257,2)[:-1]+' (export "memory" (memory 0)))')]:
        f=out/(name+'.wasm');p.q.compile(wat,f)
        try:p.recover(f,out/(name+'-must-not-exist.wasm'))
        except ValueError as ex:controls.append(dict(name=name,status='rejected',reason=str(ex)))
        else:raise AssertionError('accepted invalid profile')
    # A deliberately wrong transform that erases all 32 bits although k=257.
    p.q.compile(p.render([0x01000001,7,11,13],257),out/'negative-source.wasm')
    p.q.compile(p.render(p.representative([0x01000001,7,11,13],32),257,1,32),out/'negative-over-erasure.wasm')
    js="const fs=require('fs');let r=process.argv.slice(1).map(f=>new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(f))).exports.run(3,0,1,0)>>>0);if(r[0]===r[1])throw Error('missed negative');console.log(JSON.stringify(r));"
    r=subprocess.run(['node','-e',js,str(out/'negative-source.wasm'),str(out/'negative-over-erasure.wasm')],capture_output=True,text=True,check=True)
    p.q.save(out/'audit.json',dict(replayed=len(replay),files=replay,wabt_calls=6*len(cross),cross=cross,controls=controls,negative_outputs=json.loads(r.stdout),memory_checks=json.loads((out/'memory-checks.json').read_text())['calls']))
    print(json.dumps(dict(replayed=len(replay),wabt_calls=6*len(cross),controls=controls,negative_outputs=json.loads(r.stdout))),flush=True)


if __name__=='__main__':main(sys.argv[1],sys.argv[2])
