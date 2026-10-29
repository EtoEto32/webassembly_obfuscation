import json
from pathlib import Path
import re
import subprocess
import sys
import prototype as p


def main(base,out):
    base=Path(base).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    load=lambda f:json.loads(f.read_text());cases=load(base/'cases.json');targets=load(base/'manifest.json')
    diagnostic=[];cross=[];replay=[];negative=[]
    for c in cases:
        name=c['name'];g=next(g for g in p.grammars() if name.startswith(g['name']));src=out/(name+'-source.wasm');p.q.compile(p.render(c['grammar']),src)
        if src.read_bytes()!=(base/(name+'-plain-raw.wasm')).read_bytes():raise AssertionError('source replay')
        for t in [t for t in targets if t['name']==name and not t['mode'].endswith('recovered')]:
            f=base/t['file'];dst=out/t['file'];mode=t['mode'];raw=dst.with_name(dst.stem.replace('-O3','-raw')+'.wasm')
            if not raw.exists():
                if mode=='plain':p.q.compile(p.render(c['grammar']),raw)
                else:
                    kind,alpha=mode.split('-');p.transform(src,raw,g['a'],g['b'],g['c'],int(alpha),kind=='linear')
            if t['optimization']=='O3':p.q.w.tool('wasm-opt',[raw,'--enable-bulk-memory','-O3','-o',dst])
            if dst.read_bytes()!=f.read_bytes():raise AssertionError('replay '+f.name)
            replay.append(f.name)
            m=p.q.read(f);run=next(e[2][1] for e in m[1:] if e[:2]==['export','"run"'])
            # Same probes across all modes, scored below against source interpreter.
            for i,args in enumerate([(0,0,0),(0,0,1),(4,0,2),(0x44444444,0,8),(0x44444444,0x44444444,32)]):
                m.append(['func',['export','"probe%d"'%i],['result','i32'],['call',run,*[['i32.const',str(v)] for v in args]]])
            probe=out/(f.stem+'-probe.wasm');p.q.compile(p.q.w.emit(m),probe)
            stdout=p.q.w.tool('wasm-interp',[probe,'--run-all-exports'])
            actual=[int(x)&p.MASK for x in re.findall(r'probe\d+\(\) => i32:(\d+)',stdout)]
            if len(actual)!=5:raise AssertionError(stdout)
            cross.append(dict(name=name,file=f.name,values=actual))
            m=p.q.read(f);m.append(['export','"memory"',['memory','0']]);diag=out/(f.stem+'-diagnostic.wasm');p.q.compile(p.q.w.emit(m),diag)
            diagnostic.append({**t,'file':diag.name})
        values=[r['values'] for r in cross if r['name']==name]
        if any(x!=values[0] for x in values):raise AssertionError('WABT disagreement')
    for label,text in [('wrong arithmetic',p.render(cases[0]['grammar']).replace('(i32.mul (local.get 7) (i32.const 12))','(i32.add (local.get 7) (i32.const 12))')),
                       ('exported memory',p.render(cases[0]['grammar'])[:-1]+'(export "memory" (memory 0)))')]:
        f=out/(label.replace(' ','-')+'.wasm');p.q.compile(text,f)
        try:p.read(f)
        except ValueError as ex:negative.append(dict(name=label,status='rejected',reason=str(ex)))
        else:raise AssertionError('accepted invalid profile')
    # Removing the compensating quadratic rule is a semantic error, not merely
    # an altered internal representation. Save the wrong executable for audit.
    g=p.grammars()[0];bad=p.shear(g['polys'],g['a'],g['b'],g['c'],257)
    bad[g['a']]=p.add(bad[g['a']],{(g['b'],g['c']):(-257)&p.MASK})
    p.q.compile(p.render(p.binarize(bad,g['alphabet'])),out/'missing-correction.wasm')
    js="const fs=require('fs');const e=process.argv.slice(1).map(f=>new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(f))).exports.run);let diff=null;for(let n=1;n<=10&&!diff;n++)for(let v=0;v<2**n&&!diff;v++){let lo=0;for(let i=0;i<n;i++)lo|=((v>>>i)&1)<<(2*i);let r=e.map(f=>f(lo,0,n)>>>0);if(r[0]!==r[1])diff={n,lo,values:r};}if(!diff)throw Error('negative not detected');console.log(JSON.stringify(diff));"
    counterexample=json.loads(subprocess.check_output(['node','-e',js,str(out/'dyck-source.wasm'),str(out/'missing-correction.wasm')],text=True))
    p.q.save(out/'cases.json',cases);p.q.save(out/'manifest.json',diagnostic)
    r=subprocess.run(['node',str(p.HERE/'check.cjs'),str(out)],capture_output=True,text=True,timeout=120)
    (out/'checks.stdout.txt').write_text(r.stdout);(out/'checks.stderr.txt').write_text(r.stderr)
    if r.returncode:raise RuntimeError(r.stderr)
    p.q.save(out/'memory-checks.json',json.loads(r.stdout));p.q.save(out/'audit.json',dict(replayed=len(replay),wabt_calls=5*len(cross),cross=cross,replay=replay,negative=negative,counterexample=counterexample))
    print(json.dumps(dict(replayed=len(replay),wabt_calls=5*len(cross),memory=json.loads(r.stdout)['calls'],counterexample=counterexample)))


if __name__=='__main__':main(*sys.argv[1:])
