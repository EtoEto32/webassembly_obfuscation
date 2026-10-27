"""Replay and independent sequential interpreter checks of the saved experiment."""
import argparse,hashlib,json,re,shutil,subprocess
from pathlib import Path
import prototype as p

def sha(f):return hashlib.sha256(Path(f).read_bytes()).hexdigest()

def run(main,output):
    main=Path(main).resolve();out=Path(output).resolve();out.mkdir(parents=True,exist_ok=False)
    pins=json.loads((main/'pins.json').read_text());assert all(sha(main/k)==v for k,v in pins.items())
    rows=json.loads((main/'manifest.json').read_text());replays=[];interp=[]
    for row in rows:
        file=out/row['file']
        if row['version']=='raw':
            if row['mode']=='plain':p.compile(p.fixture(row['profile']),file)
            else:p.transform(out/f"{row['profile']}.plain.raw.wasm",file,row['mode'])
        else:p.w.tool('wasm-opt',[out/row['file'].replace('.O3.','.raw.'),'--enable-threads','-O3','-o',file])
        assert sha(file)==sha(main/row['file']);replays.append(row['file'])
        m=p.read(file);m=[(['memory','1','1','shared'] if isinstance(x,list) and x[0]=='import' else x) for x in m]
        ex={x[1].strip('"'):x[2][1] for x in m[1:] if x[0]=='export'}
        def call(name,*args):return f'(call {ex[name]} '+' '.join(f'(i32.const {v&0xffffffff})' for v in args)+')'
        tests=[(call('store',0,0x7fffffff)+call('load',0),0x7fffffff),
            (call('store',4,0x12345678)+call('add',0,1),0x7fffffff),
            (call('cmpxchg',0,0x80000000,123),0x80000000),(call('cmpxchg',0,0,77),123),
            (call('and',0,15),123),(call('load',0),11),(call('load',4),0x12345678),
            (call('add',1,1),'trap'),(call('offset4294967292',4,1),'trap'),
            (call('edge',4,456),'trap'),(call('load',0),456),(call('load',4),0x12345678)]
        for i,(body,_) in enumerate(tests):m.append(p.w.parse(f'(module (func (export "probe{i}") (result i32) {body}))')[1])
        target=out/('interp-'+row['file']);p.compile(p.w.emit(m),target)
        log=p.w.tool('wasm-interp',[target,'--enable-threads','--run-all-exports']);target.with_suffix('.log').write_text(log,encoding='utf8')
        got=[]
        for i,(_,want) in enumerate(tests):
            line=next(l for l in log.splitlines() if l.startswith(f'probe{i}()'))
            value=int(re.search(r'i32:(\d+)',line)[1]) if 'i32:' in line else 'trap' if 'error:' in line else line
            assert value==want,(row,line,want);got.append(value)
        interp.append(dict(file=row['file'],actual=got))
    rejected=[]
    for name,body in {
       'ordinary-load':'(func (result i32) (i32.load (i32.const 0)))',
       'narrow':'(func (result i32) (i32.atomic.load8_u (i32.const 0)))',
       'grow':'(func (result i32) (memory.grow (i32.const 1)))',
       'data':'(data (i32.const 0) "x")',
       'memory-export':'(export "m" (memory 0))',
       'host-call':'(import "host" "f" (func))'}.items():
        src=out/f'reject-{name}.wasm';p.compile('(module (import "env" "memory" (memory 1 1 shared))'+body+')',src)
        try:p.transform(src,out/f'unexpected-{name}.wasm');raise AssertionError('unexpected acceptance '+name)
        except ValueError as e:rejected.append(dict(name=name,reason=str(e)))
    unknown=out/'unknown.wasm';p.compile(p.fixture('low').replace('(i32.and (local.get 0) (i32.const -8))','(local.get 0)'),unknown)
    unknown_stats=p.transform(unknown,out/'unknown.auto.wasm');assert unknown_stats['codec']=='both'
    r=subprocess.run(['node',str(Path(__file__).with_name('bench-check.cjs')),str(main)],capture_output=True,text=True,timeout=30)
    (out/'bench-check.stdout.txt').write_text(r.stdout,encoding='utf8');(out/'bench-check.stderr.txt').write_text(r.stderr,encoding='utf8')
    if r.returncode:raise RuntimeError(r.stderr)
    stats=dict(pins_verified=len(pins),replay=replays,wabt=interp,rejections=rejected,unknown_footprint=unknown_stats,bench=json.loads(r.stdout))
    (out/'audit.json').write_text(json.dumps(stats,indent=2),encoding='utf8')
    for f in Path(__file__).parent.iterdir():
        if f.suffix in ('.py','.cjs'):shutil.copy2(f,out/('source-'+f.name))
    (out/'pins.json').write_text(json.dumps({str(f.relative_to(out)):sha(f) for f in out.rglob('*') if f.is_file() and f.name!='pins.json'},indent=2),encoding='utf8')
    print(json.dumps(dict(pins_verified=len(pins),replayed=len(replays),wabt_calls=sum(len(v['actual']) for v in interp),rejections=len(rejected),passed=True)))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('main');ap.add_argument('output');a=ap.parse_args();run(a.main,a.output)
