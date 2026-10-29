"""Rebuild saved targets and audit evidence; no new performance claims."""
import json, math, re, sys
from pathlib import Path
import prototype as p
q=p.q
src,out=map(Path,sys.argv[1:]);out.mkdir(parents=True,exist_ok=False)
read=lambda n:json.loads((src/n).read_text(encoding='utf-8'))
rows=read('manifest.json');checks=read('checks.json');fixtures=read('fixtures.json')
assert len(rows)==len(checks['records'])==checks['targets']==32
assert len({r['file'] for r in rows})==32
assert checks['inputs']==len(read('inputs.json'))==1040
assert checks['calls']==33280
positive=[r for r in checks['records'] if r['mode']!='decoder']
negative=[r for r in checks['records'] if r['mode']=='decoder']
assert len(positive)==checks['positive_targets']==24
assert all(r['wrong_results']==r['watchdog_traps']==0 for r in positive)
assert len(negative)==8 and all(r['wrong_results']+r['watchdog_traps']==1040 for r in negative)
assert sum(r['wrong_results'] for r in negative)==4526
assert sum(r['watchdog_traps'] for r in negative)==3794
model=read('selector-model.json')
assert model['configurations']==len(model['rows'])==9734
assert model['fixed_successors']==0
assert model['value_checks']==sum(x['period'] for x in model['rows'])==103592
for r in model['rows']:
    M=r['M'];f=r['frequencies'];s=r['symbol'];B=[sum(f[:i]) for i in range(len(f))]
    assert sum(f)==M and min(f)>0 and len(f)>=2
    assert r['period']==M//math.gcd(f[s],M)
    for key in ('first','second'):
        rem=(f[s]*r[key+'_value']+r['residue']-B[s])%M
        t=next(i for i,b in enumerate(B) if b<=rem<b+f[i])
        assert t==r[key+'_next_symbol']
    assert r['first_next_symbol']!=r['second_next_symbol']
for r in read('sources.json'):assert q.digest(p.ROOT/r['file'])==r['sha256']
rebuilt=[]
for name,ops in fixtures.items():
    original=out/(name+'-source.wasm');q.compile(p.source(ops),original)
    assert q.digest(original)==q.digest(src/original.name)
    for mode in ('plain','decoder','lift'):
        raw=out/(name+'-'+mode+'-raw.wasm')
        if mode=='plain':q.compile(p.source(ops),raw)
        else:p.transform(original,raw,mode)
        for opt in ('raw','O3'):
            f=raw if opt=='raw' else out/(name+'-'+mode+'-O3.wasm')
            if opt=='O3':q.tool('wasm-opt',[raw,'-O3','-o',f])
            if mode=='lift':p.recover(f,f.with_name(f.stem+'-recovered.wasm'))
for r in rows:
    f=src/r['file'];g=out/r['file']
    assert q.digest(f)==r['sha256']==q.digest(g)
    assert f.stat().st_size==r['bytes']
    q.w.tool('wasm-validate',[f]);q.w.tool('wasm-validate',[g])
    rebuilt.append(dict(file=r['file'],sha256=r['sha256']))
assert len(read('recovery.json'))==8
interp=read('interpreter.json');assert interp['calls']==96 and len(interp['rows'])==24
for r in interp['rows']:
    f=src/('interp-'+r['file']);q.w.tool('wasm-validate',[f])
    log=f.with_suffix('.log').read_text(encoding='utf-8')
    got={int(i):int(x) for i,x in re.findall(r'probe(\d+)\(\) => i32:(\d+)',log)}
    assert [got[i] for i in range(4)]==r['outputs']
sources=sorted(Path(__file__).parent.glob('*.md'))+sorted(Path(__file__).parent.glob('*.py'))+sorted(Path(__file__).parent.glob('*.cjs'))
sources += [p.ROOT/'research/isotope-swizzle/prototype.py',p.ROOT/'research/connectivity-elimination/prototype.py']
links=[]
for f in sources:
    if f.suffix!='.md':continue
    for href in re.findall(r'\]\(([^)]+)\)',f.read_text(encoding='utf-8')):
        if '://' in href or href.startswith('#'):continue
        target=(f.parent/href.split('#')[0]).resolve()
        if target!= (out/'audit.json').resolve():assert target.exists(),(f,href)
        links.append(dict(file=str(f.relative_to(p.ROOT)),target=href))
tools=[p.ROOT/'.tools/wabt-1.0.42/bin'/n for n in ('wat2wasm.exe','wasm2wat.exe','wasm-validate.exe','wasm-interp.exe')]+[p.ROOT/'.tools/binaryen-version_133/bin/wasm-opt.exe']
evidence=[dict(file=str(f.resolve().relative_to(p.ROOT)),sha256=q.digest(f)) for f in sorted(src.iterdir()) if f.suffix in ('.json','.wasm','.log')]
q.save(out/'audit.json',dict(scope='32 byte-identical rebuilds and saved evidence consistency; no new independent test inputs or timing experiment',positive_calls=24960,negative_calls=8320,negative_wrong_results=4526,diagnostic_watchdog_traps=3794,model_configurations=9734,model_value_checks=103592,wabt_calls=96,replay=rebuilt,sources=[dict(file=str(f.relative_to(p.ROOT)),sha256=q.digest(f)) for f in sources],tools=[dict(file=str(f.relative_to(p.ROOT)),sha256=q.digest(f)) for f in tools],evidence=evidence,local_links=links))
print(json.dumps(dict(rebuilt=len(rebuilt),source_files=len(sources),evidence_files=len(evidence),local_links=len(links))))
