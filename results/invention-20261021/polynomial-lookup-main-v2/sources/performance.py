import json,pathlib,platform,random,statistics,struct,subprocess,sys
import prototype as p
root=pathlib.Path(sys.argv[1]).resolve();out=pathlib.Path(sys.argv[2]).resolve();out.mkdir(parents=True,exist_ok=False)
def save(name,obj):(out/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding='utf-8')
rows=[r for r in json.loads((root/'manifest.json').read_text())
      if r['stage']=='O3' and r['mode'] in ('list','array','poly','poly-pruned') and r['name'] in ('n8','n32','n128','full32')]
rng=random.Random(21102132);workloads={}
for name in sorted(set(r['name'] for r in rows)):
    items=dict(json.loads((root/(name+'-oracle.json')).read_text())['items']);hit=sorted(items)
    miss=[]
    while len(miss)<len(hit):
        x=rng.randrange(2**32)
        if x not in items:miss.append(x)
    workloads[name]={'hit':(hit,[items[x] for x in hit]),'miss':(miss,[0]*len(miss))}
tasks=[]
for r in rows:
    for kind,(inputs,answers) in workloads[r['name']].items():
        m=p.q.read(r['file']);idx=next(x[2][1] for x in m[1:] if x[0]=='export' and x[1]=='"lookup"')
        body=f'''(module (func (export "bench") (param $n i32) (result i32)
         (local $i i32) (local $s i32) (local $p i32)
         (block $done (loop $next (br_if $done (i32.ge_u (local.get $i) (local.get $n)))
          (local.set $s (i32.add (i32.rotl (local.get $s) (i32.const 1))
            (call {idx} (i32.load (i32.add (i32.const 49152) (local.get $p))))))
          (local.set $p (i32.add (local.get $p) (i32.const 4)))
          (if (i32.eq (local.get $p) (i32.const {4*len(inputs)})) (then (local.set $p (i32.const 0))))
          (local.set $i (i32.add (local.get $i) (i32.const 1))) (br $next))) (local.get $s)))'''
        m.append(p.q.w.parse(body)[1]);m.append(['data',['i32.const','49152'],p.quoted(b''.join(struct.pack('<I',x) for x in inputs))])
        file=out/f'{r["name"]}-{r["mode"]}-{kind}.wasm';p.q.compile(p.q.w.emit(m),file)
        task=dict(name=r['name'],mode=r['mode'],kind=kind,file=str(file),inputs=inputs,answers=answers,
                  original_bytes=r['bytes'],linear_memory_bytes=65536)
        path=out/(file.stem+'.json');save(path.name,task);tasks.append((task,path))
jobs=[(task,path,i) for task,path in tasks for i in range(3)];rng.shuffle(jobs);results=[]
for task,path,i in jobs:
    cmd=['node','--no-liftoff','--no-wasm-lazy-compilation',str(pathlib.Path(__file__).with_name('bench.cjs')),str(path)]
    run=subprocess.run(cmd,capture_output=True,text=True,timeout=60,check=True)
    row=dict(task,**json.loads(run.stdout),process=i);results.append(row)
    save(f'{path.stem}-process-{i}.json',row)
summary=[]
for task,path in tasks:
    xs=[r for r in results if (r['name'],r['mode'],r['kind'])==(task['name'],task['mode'],task['kind'])]
    ts=[x['median_ns'] for x in xs]
    summary.append(dict(name=task['name'],mode=task['mode'],kind=task['kind'],median_ns=statistics.median(ts),
                        min_ns=min(ts),max_ns=max(ts),bytes=task['original_bytes'],rss_kib=[x['maxRSS_KiB'] for x in xs]))
save('summary.json',summary);save('environment.json',dict(platform=platform.platform(),processor=platform.processor(),
 python=sys.version,node=subprocess.check_output(['node','--version'],text=True).strip(),
 wasm_opt=p.q.tool('wasm-opt',['--version']).strip(),wabt=p.q.w.tool('wat2wasm',['--version']).strip(),
 cpu_affinity='not fixed',frequency='not controlled',processes=len(results),seed=21102132))
print(json.dumps(summary))
