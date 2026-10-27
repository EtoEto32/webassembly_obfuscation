import copy,json,platform,re,subprocess,sys
from pathlib import Path
import prototype as p
import model
q=p.q;src,out=map(Path,sys.argv[1:]);out.mkdir(parents=True,exist_ok=False)
rows=json.loads((src/'manifest.json').read_text());fixtures=json.loads((src/'fixtures.json').read_text());replay=[]
for row in rows:
    dst=out/row['file']
    if row['mode'] in ('candidate','residual'):continue
    if row['opt']=='raw':p.transform(src/(row['kernel']+'-source.wasm'),dst,row['mode'],row['seed'])
    else:q.tool('wasm-opt',[out/row['file'].replace('-O3.wasm','-raw.wasm'),'-O3','-o',dst])
    assert dst.read_bytes()==(src/row['file']).read_bytes();replay.append(dict(file=row['file'],sha256=q.digest(dst)))
for row in rows:
    if row['mode']!='deferred':continue
    target=out/row['file'];candidate=target.with_name(target.stem+'-recovered.wasm');residual=target.with_name(target.stem+'-residual.wasm')
    p.recover(target,candidate);p.residual_recovery(target,candidate,residual)
    for dst in (candidate,residual):assert dst.read_bytes()==(src/dst.name).read_bytes();replay.append(dict(file=dst.name,sha256=q.digest(dst)))
q.save(out/'replay.json',replay)
triples=[[0,0x80000000,0],[0x80000000,0x3f800000,0x80000000],[1,0x3f000000,0x80000000],[0x7f7fffff,0x7f7fffff,0xff800000],[0x7f800001,0x3f800000,0],[0x3eaaaaab,0xbf100001,0x3f345678]]
interp=[]
for row in rows:
    if row['mode'] in ('candidate','uncorrected'):continue
    m=q.read(src/row['file']);index=next(x[2][1] for x in m[1:] if x[:2]==['export','"run"']);count=len([x for x in m[1:] if x[0]=='func'])
    for i,t in enumerate(triples):
        m.append(['func',['result','i32'],['call',index,*[['i32.const',str(x)] for x in t]]]);m.append(['export','"probe'+str(i)+'"',['func',str(count+i)]])
    dst=out/('interp-'+row['file']);q.compile(q.w.emit(m),dst);stdout=q.w.tool('wasm-interp',[dst,'--run-all-exports'])
    (out/(dst.stem+'.log')).write_text(stdout,encoding='utf-8');got={int(i):int(x) for i,x in re.findall(r'probe(\d+)\(\) => i32:(\d+)',stdout)}
    f=fixtures[row['kernel']];want=[model.evaluate(f['nodes'],f['root'],t) for t in triples]
    assert len(got)==len(want) and all(got[i]==x for i,x in enumerate(want));interp.append(dict(file=row['file'],expected=want,actual=[got[i] for i in range(len(want))]))
q.save(out/'interpreter.json',dict(inputs=triples,rows=interp,calls=len(interp)*len(triples)))
source=q.read(src/'fma-source.wasm');rejects=[]
for name in ('memory','import','division','noncanonical'):
    m=copy.deepcopy(source)
    if name=='memory':m.append(['memory','1'])
    elif name=='import':m.insert(1,['import','"env"','"g"',['global','i32']])
    elif name=='division':next(x for x in q.walk(m) if x[0]=='f32.mul')[0]='f32.div'
    else:next(x for x in q.walk(m) if x==['i32.const','2143289344'])[1]='0'
    dst=out/('reject-'+name+'.wasm');q.compile(q.w.emit(m),dst)
    try:p.parse_source(q.read(dst))
    except p.Unsupported as e:rejects.append(dict(name=name,reason=str(e),validated=True))
    else:raise AssertionError('unsupported accepted '+name)
q.save(out/'rejections.json',rejects)
q.save(out/'environment.json',dict(platform=platform.platform(),python=sys.version,processor=platform.processor(),node=subprocess.check_output(['node','--version'],text=True).strip(),wabt=q.w.tool('wasm-validate',['--version']).strip(),binaryen=q.tool('wasm-opt',['--version']).strip()))
q.save(out/'sources.json',[dict(file=str(f.relative_to(p.ROOT)),sha256=q.digest(f)) for f in Path(__file__).parent.iterdir() if f.suffix in ('.py','.cjs')])
print(json.dumps(dict(replayed=len(replay),interpreter_targets=len(interp),interpreter_calls=len(interp)*len(triples),rejected=len(rejects))))
