"""Reproducible correctness/known-method recovery gate; refuses overwrite."""
import hashlib,json,pathlib,random,shutil,subprocess,sys,time
import prototype as p
ROOT=p.ROOT
out=pathlib.Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=False)
def save(name,obj):(out/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding='utf-8')
snap=out/'sources';snap.mkdir()
for f in pathlib.Path(__file__).parent.iterdir():
    if f.suffix in ('.py','.cjs','.md'):shutil.copy2(f,snap/f.name)
rng=random.Random(21102131);fixtures=[]
for n in (8,32,128):
    source=ROOT/f'results/invention-20261021/notdec-baseline-v1/list-{n}-048.wasm'
    # Existing test oracle is separate from this transformer's profile reader.
    tests=json.loads(source.with_suffix('.tests.json').read_text())
    items=[(k,v) for k,v in tests if v!=0]
    fixtures.append((f'n{n}',source,items,tests))
new={
 'empty':[],
 'duplicate':[(5,7),(2,0),(5,9),(p.P,0xffffffff),(p.P,17)],
 'boundary':list(zip([0,1,2,3,0x7fffffff,0x80000000,p.P-2,p.P-1,p.P,p.P+1,p.P+2,p.P+3,p.P+4],
                    [0xffffffff,p.P,p.P+1,p.P+2,p.P+3,p.P+4,0,1,2,3,0x80000000,0x7fffffff,p.P-1])),
 'full32':[(k,rng.randrange(2**32)) for k in rng.sample(range(2**32),64)]}
for name,items in new.items():
    source=out/(name+'-input.wasm');p.q.compile(p.list_text(items),source)
    fixtures.append((name,source,items,[]))
rows=[];tasks=[];recovery=[]
bound=[0,1,2,3,0x7fffffff,0x80000000,p.P-2,p.P-1,*range(p.P,2**32)]
for name,src,items,oldtests in fixtures:
    oracle={}
    for k,v in items:oracle.setdefault(k&0xffffffff,v&0xffffffff)
    xs=list(oracle)+bound+[rng.randrange(2**32) for _ in range(1024)]
    tests=oldtests+[[x,oracle.get(x,0)] for x in xs]
    if name.startswith('n'):
        # Existing corpus has only positive saved keys, but old test rows can repeat them.
        assert len(oracle)==int(name[1:])
    save(name+'-oracle.json',dict(items=list(oracle.items()),tests=tests))
    modes={};transforms={}
    plain=out/(name+'-list-raw.wasm');shutil.copy2(src,plain);modes['list']=plain
    for mode in ('array','poly'):
        dst=out/f'{name}-{mode}-raw.wasm';transforms[mode]=p.transform(src,dst,mode);modes[mode]=dst
    for stage in ('raw','O3'):
        stagefiles={}
        for mode,raw in modes.items():
            file=raw if stage=='raw' else out/f'{name}-{mode}-O3.wasm'
            if stage=='O3':p.q.tool('wasm-opt',[raw,'-O3','--enable-bulk-memory','-o',file]);p.q.w.tool('wasm-validate',[file])
            stagefiles[mode]=file
        rec=out/f'{name}-recovered-{stage}.wasm';r=p.recover(stagefiles['poly'],rec)
        assert r['items']==[list(x) for x in sorted(oracle.items())] or r['items']==sorted(oracle.items())
        r.update(name=name,stage=stage,file=str(stagefiles['poly']),status='success');recovery.append(r)
        stagefiles['recovered']=rec
        for mode,file in stagefiles.items():
            tasks.append(dict(file=str(file),tests=tests))
            rows.append(dict(name=name,stage=stage,mode=mode,file=str(file),keys=len(oracle),
                bytes=file.stat().st_size,sha256=p.q.digest(file),linear_memory_bytes=65536,
                transform=transforms.get(mode)))
    print(json.dumps(dict(done=name,keys=len(oracle),calls_per_binary=len(tests))),flush=True)
save('manifest.json',rows);save('recovery.json',recovery);save('tasks.json',tasks)
res=subprocess.run(['node',str(pathlib.Path(__file__).with_name('check.cjs')),str(out/'tasks.json')],capture_output=True,text=True,timeout=60)
(out/'check-stdout.txt').write_text(res.stdout,encoding='utf-8');(out/'check-stderr.txt').write_text(res.stderr,encoding='utf-8')
res.check_returncode();save('checks.json',json.loads(res.stdout))
# Re-layout controls: the source's former next/key/value offsets are absent from output.
layouts=[]
for layout in ('804','480'):
    src=ROOT/f'results/invention-20261021/notdec-baseline-v1/list-32-{layout}.wasm'
    dst=out/f'layout-{layout}.wasm';p.transform(src,dst,'poly')
    same=dst.read_bytes()==(out/'n32-poly-raw.wasm').read_bytes();assert same
    layouts.append(dict(layout=layout,byte_identical=same))
save('layout.json',layouts)
print(json.dumps(dict(binaries=len(rows),calls=json.loads(res.stdout)['calls'],recovered=len(recovery))),flush=True)
