"""Byte replay, unsupported inputs, and sequential WABT probe of saved targets."""
import json,re,sys
from pathlib import Path
import prototype as p
main=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();out.mkdir(parents=True,exist_ok=False)
rows=json.loads((main/'manifest.json').read_text());replay=[];wabt=[];rejects=[]
for r in rows:
    if r['opt']=='raw':p.transform(main/(r['profile']+'-source.wasm'),out/r['file'],r['mode'])
    else:p.q.tool('wasm-opt',[out/r['file'].replace('-O3','-raw'),'-O3','--enable-threads','-o',out/r['file']])
    replay.append(dict(file=r['file'],match=p.q.digest(out/r['file'])==r['sha256']))
    assert replay[-1]['match']
    if r['negative']:continue
    m=p.read(main/r['file']);m=[(['memory','1','1','shared'] if isinstance(x,list) and x[0]=='import' else x) for x in m]
    ex={e[1].strip('"'):e[2][1] for e in m[1:] if e[0]=='export'}
    def call(name,*args):return f'(call {ex[name]} '+' '.join(p.c(x) for x in args)+')'
    op='and' if r['profile']=='full' else 'sub';y=15 if op=='and' else 3;last=11 if op=='and' else 120
    probes=[(call('store',0,0x7fffffff)+' '+call('load',0),0x7fffffff),
       (call('add',0,1),0x7fffffff),(call('cmpxchg',0,0x80000000,123),0x80000000),
       (call('cmpxchg',0,0,77),123),(call(op,0,y),123),(call('add',1,1),'trap'),
       (call('load',0),last),(call('offset4294967292',4,1),'trap'),(call('load',0),last)]
    for j,(body,want) in enumerate(probes):m.append(p.q.w.parse(f'(module (func (export "probe{j}") (result i32) {body}))')[1])
    f=out/('interp-'+r['file']);p.compile(p.q.w.emit(m),f)
    log=p.q.w.tool('wasm-interp',[f,'--enable-threads','--run-all-exports']);f.with_suffix('.log').write_text(log,encoding='utf-8')
    actual=[]
    for j,(_,want) in enumerate(probes):
        line=next(x for x in log.splitlines() if x.startswith(f'probe{j}()'))
        got=int(re.search(r'i32:(\d+)',line)[1]) if 'i32:' in line else 'trap' if 'error:' in line else line
        assert got==want,(r,line,want);actual.append(got)
    wabt.append(dict(file=r['file'],actual=actual))
base='(module (import "env" "memory" (memory 1 1 shared)) %s)'
bad={'ordinary-load':'(func (export "f") (result i32) (i32.load (i32.const 0)))',
 'narrow':'(func (export "f") (result i32) (i32.atomic.load8_u (i32.const 0)))',
 'grow':'(func (export "f") (result i32) (memory.grow (i32.const 1)))',
 'data':'(data (i32.const 0) "abc")'}
for name,body in bad.items():
    src=out/('reject-'+name+'.wasm');p.compile(base%body,src)
    try:p.transform(src,out/('unexpected-'+name+'.wasm'),'native-neg');raise AssertionError('accepted '+name)
    except ValueError as e:rejects.append(dict(case=name,reason=str(e)))
try:p.transform(main/'full-source.wasm',out/'unexpected-affine.wasm','native-affine');raise AssertionError('accepted affine full')
except ValueError as e:rejects.append(dict(case='affine-incompatible-footprint',reason=str(e)))
(out/'audit.json').write_text(json.dumps(dict(replay=replay,wabt=wabt,rejections=rejects),indent=2),encoding='utf-8')
print(json.dumps(dict(replay=len(replay),wabt_conditions=len(wabt),wabt_calls=sum(len(x['actual']) for x in wabt),rejections=len(rejects))))
